"""
news_routes.py — Local Area News for a given zip code
Flow: zip_code -> geocode to neighborhood/city (Google Maps) -> fetch targeted
      real-estate-relevant news (NewsAPI.org) -> clean + filter + summarize
      (Groq) -> cache in Supabase (area_news_cache)
"""

from flask import Blueprint, request, jsonify
import os
import json
import re
import logging
import requests
from datetime import datetime, timedelta, timezone
from groq import Groq

logger = logging.getLogger(__name__)
news_bp = Blueprint('news', __name__, url_prefix='/api/news')

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  # reuse your existing key
NEWS_API_KEY = os.getenv('NEWS_API_KEY')

CACHE_TTL_HOURS = 6  # how long before cached news is considered stale

# Terms that signal a story is NOT relevant to a home buyer's decision.
# NewsAPI's query syntax supports "-term" to exclude a word from results.
EXCLUDE_TERMS = ['drugs', 'murder', 'shooting', 'celebrity', 'bollywood', 'cricket score']

# Terms that signal a story IS relevant to a home buyer's decision.
RELEVANCE_TERMS = [
    'real estate', 'property', 'infrastructure', 'development', 'metro',
    'construction', 'investment', 'housing', 'project launch', 'road',
    'flyover', 'water supply', 'electricity', 'safety', 'security',
    'school', 'hospital', 'connectivity'
]


# ─── Helpers ────────────────────────────────────────────────

def zip_to_location(zip_code):
    """
    Convert zip code to a specific area name (neighborhood/sublocality first,
    falling back to city) using Google Geocoding API.
    """
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {'address': zip_code, 'key': GOOGLE_MAPS_KEY}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    if data.get('status') != 'OK' or not data.get('results'):
        return None

    result = data['results'][0]
    components = result.get('address_components', [])

    def find_component(*type_names):
        for c in components:
            types = c.get('types', [])
            if any(t in types for t in type_names):
                return c['long_name']
        return None

    # Most specific -> least specific. This is what actually gets you
    # "area near this zip" instead of just "the whole city".
    neighborhood = find_component('neighborhood')
    sublocality = find_component('sublocality_level_1', 'sublocality')
    city = find_component('locality') or find_component('administrative_area_level_2')
    state = find_component('administrative_area_level_1')

    # The most specific name we have — used for the actual news search.
    area_name = neighborhood or sublocality or city

    return {
        'area_name': area_name,        # e.g. "Rohini" or "Sector 15"
        'city': city,                   # e.g. "Delhi"
        'state': state,
        'formatted_address': result.get('formatted_address'),
        'lat': result['geometry']['location']['lat'],
        'lng': result['geometry']['location']['lng']
    }


def clean_text(text):
    """
    NewsAPI's free tier truncates description/content mid-sentence and
    appends '… [+1234 chars]'. Strip that, then trim back to the last
    complete sentence so nothing reads as cut off.
    """ 
    if not text:
        return ''

    # Remove NewsAPI's truncation marker, e.g. "... [+1532 chars]"
    text = re.sub(r'\s*\[\+\d+\s*chars\]\s*$', '', text).strip()
    text = re.sub(r'\u2026\s*$', '', text).strip()  # trailing ellipsis char

    if not text:
        return ''

    # If it doesn't end on sentence punctuation, trim back to the last
    # sentence boundary so we never hand the LLM (or the user) a
    # sentence fragment.
    if text[-1] not in '.!?':
        last_period = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
        if last_period > 40:  # keep it only if we're not left with almost nothing
            text = text[:last_period + 1]

    return text.strip()


def build_query(area_name, city):
    """
    Build a NewsAPI query scoped to the area AND real-estate-relevant topics,
    with obviously irrelevant topics excluded at the API level.
    """
    location_part = f'"{area_name}"'
    if city and city.lower() != (area_name or '').lower():
        location_part = f'({location_part} OR "{city}")'

    topic_part = '(' + ' OR '.join(f'"{t}"' for t in RELEVANCE_TERMS) + ')'
    exclude_part = ' '.join(f'-{t}' for t in EXCLUDE_TERMS)

    return f'{location_part} AND {topic_part} {exclude_part}'


def fetch_news(area_name, city):
    """Fetch recent, topically-relevant news articles using NewsAPI.org"""
    url = "https://newsapi.org/v2/everything"
    query = build_query(area_name, city)

    params = {
        'q': query,
        'sortBy': 'relevancy',   # relevance to the query, not just newest
        'language': 'en',
        'pageSize': 20,          # pull a wider candidate pool for the LLM to pick from
        'apiKey': NEWS_API_KEY
    }
    logger.info(f"[NEWS FETCH] Query: {query}")
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()
    logger.info(
        f"[NEWS FETCH] status={data.get('status')}, "
        f"totalResults={data.get('totalResults')}, "
        f"returned={len(data.get('articles', []))}"
    )

    if data.get('status') != 'ok':
        logger.warning(f"[NEWS FETCH] NewsAPI returned non-ok status: {data}")
        return []

    # If the topic-filtered query returns too little (common for small
    # towns/areas), fall back to a looser location-only query so the
    # user still gets something instead of an empty state.
    articles_raw = data.get('articles', [])
    if len(articles_raw) < 3:
        logger.info("[NEWS FETCH] Sparse results, retrying with broader location-only query")
        fallback_params = dict(params)
        fallback_params['q'] = f'"{area_name}"' if area_name else f'"{city}"'
        resp = requests.get(url, params=fallback_params, timeout=10)
        data = resp.json()
        if data.get('status') == 'ok':
            articles_raw = data.get('articles', [])

    articles = []
    for a in articles_raw[:20]:
        articles.append({
            'title': clean_text(a.get('title')),
            'description': clean_text(a.get('description')),
            'source': a.get('source', {}).get('name'),
            'url': a.get('url'),
            'published_at': a.get('publishedAt')
        })
    return articles


def summarize_news(articles, area_name, city):
    """
    Use Groq to FILTER for real-estate-buyer relevance and condense the
    relevant articles into 3-4 short points. Explicitly told to discard
    crime/celebrity/generic-city news that doesn't affect a buying decision.
    """
    if not articles:
        return []

    articles_text = "\n\n".join([
        f"- {a['title']}: {a['description']}" for a in articles if a['title']
    ])

    location_label = area_name or city

    prompt = f"""You are screening local news for someone deciding whether to BUY a house or flat in {location_label}, {city}.

ARTICLES:
{articles_text}

TASK:
1. From the articles above, keep ONLY the ones that would matter to a home buyer:
   - New infrastructure or transit (roads, metro, flyovers)
   - New residential/commercial development or major projects
   - Utilities and civic services (water, power, sanitation)
   - Genuine safety/security developments (e.g. new police station, better lighting) —
     NOT routine crime-blotter stories
   - Schools, hospitals, connectivity, or major economic investment in the area
2. Discard anything generic to the wider city that isn't tied to this specific area,
   and discard crime, politics, celebrity, or entertainment stories unless they
   directly involve real estate or development.
3. If NOTHING qualifies, return an empty "points" list — do not force irrelevant
   stories in just to hit a count.
4. Otherwise, write 3-4 bullet points (12-20 words each), in your own words,
   each ending on a complete sentence. Do not cut off mid-sentence.

Respond in this exact JSON format and nothing else:
{{
  "points": ["point 1", "point 2", "point 3"]
}}
"""

    try:
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=500
        )

        raw = completion.choices[0].message.content.strip()
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.DOTALL).strip()
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if match:
            points = json.loads(match.group()).get('points', [])
            # belt-and-suspenders: strip any lingering truncation artifacts
            return [clean_text(p) for p in points if p and clean_text(p)]
        return []
    except Exception as e:
        logger.error(f"[NEWS SUMMARIZE ERROR] {e}")
        return []


# ============================================================
# GET /api/news/area?zip_code=110001
# ============================================================

@news_bp.route('/area', methods=['GET'])
def get_area_news():
    try:
        from app import supabase

        zip_code = request.args.get('zip_code', '').strip()
        if not zip_code:
            return jsonify({'error': 'zip_code is required'}), 400

        # ── Check cache first ────────────────────────────────
        cache_result = supabase.table('area_news_cache') \
            .select('*') \
            .eq('zip_code', zip_code) \
            .execute()

        if cache_result.data:
            cached = cache_result.data[0]
            fetched_at = datetime.fromisoformat(cached['fetched_at'].replace('Z', '+00:00'))
            age = datetime.now(timezone.utc) - fetched_at

            if age < timedelta(hours=CACHE_TTL_HOURS):
                logger.info(f"[AREA NEWS] Cache hit for {zip_code}")
                return jsonify({
                    'success': True,
                    'zip_code': zip_code,
                    'location': {
                        'area_name': cached.get('area_name'),
                        'city': cached['city'],
                        'formatted_address': cached['formatted_address'],
                        'lat': cached['lat'],
                        'lng': cached['lng']
                    },
                    'summary_points': cached['summary_points'],
                    'articles': cached['articles'],
                    'cached': True
                }), 200

        # ── Cache miss or stale — fetch fresh ────────────────
        location = zip_to_location(zip_code)
        if not location or not location.get('city'):
            return jsonify({'error': 'Could not resolve zip code to a location'}), 404

        articles = fetch_news(location['area_name'], location['city'])
        points = summarize_news(articles, location['area_name'], location['city'])

        # ── Upsert into cache ─────────────────────────────────
        supabase.table('area_news_cache').upsert({
            'zip_code': zip_code,
            'area_name': location['area_name'],
            'city': location['city'],
            'formatted_address': location['formatted_address'],
            'lat': location['lat'],
            'lng': location['lng'],
            'summary_points': points,
            'articles': articles,
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }, on_conflict='zip_code').execute()

        return jsonify({
            'success': True,
            'zip_code': zip_code,
            'location': location,
            'summary_points': points,
            'articles': articles,
            'cached': False
        }), 200

    except Exception as e:
        logger.error(f"[AREA NEWS ERROR] {e}")
        return jsonify({'error': 'Failed to fetch area news', 'details': str(e)}), 500


# ============================================================
# HEALTH CHECK
# GET /api/news/health
# ============================================================

@news_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'module': 'area_news',
        'endpoints': [
            'GET /api/news/area?zip_code=110001 — fetch and summarize local news for a zip code'
        ]
    }), 200