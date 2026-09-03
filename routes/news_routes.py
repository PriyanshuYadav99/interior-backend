# """
# news_routes.py — Local Area News for a given zip code
# Flow: zip_code -> geocode to neighborhood/city (Google Maps) -> fetch targeted
#       real-estate-relevant news (NewsAPI.org) -> clean + filter + summarize
#       (Groq) -> cache in Supabase (area_news_cache)
# """

# from flask import Blueprint, request, jsonify
# import os
# import json
# import re
# import logging
# import requests
# from datetime import datetime, timedelta, timezone
# from groq import Groq

# logger = logging.getLogger(__name__)
# news_bp = Blueprint('news', __name__, url_prefix='/api/news')

# groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
# GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  # reuse your existing key
# NEWS_API_KEY = os.getenv('NEWS_API_KEY')

# CACHE_TTL_HOURS = 6  # how long before cached news is considered stale

# # Terms that signal a story is NOT relevant to a home buyer's decision.
# # NewsAPI's query syntax supports "-term" to exclude a word from results.
# EXCLUDE_TERMS = ['drugs', 'murder', 'shooting', 'celebrity', 'bollywood', 'cricket score']

# # Terms that signal a story IS relevant to a home buyer's decision.
# RELEVANCE_TERMS = [
#     'real estate', 'property', 'infrastructure', 'development', 'metro',
#     'construction', 'investment', 'housing', 'project launch', 'road',
#     'flyover', 'water supply', 'electricity', 'safety', 'security',
#     'school', 'hospital', 'connectivity'
# ]


# # ─── Helpers ────────────────────────────────────────────────

# def zip_to_location(zip_code):
#     """
#     Convert zip code to a specific area name (neighborhood/sublocality first,
#     falling back to city) using Google Geocoding API.
#     """
#     url = "https://maps.googleapis.com/maps/api/geocode/json"
#     params = {'address': zip_code, 'key': GOOGLE_MAPS_KEY}
#     resp = requests.get(url, params=params, timeout=10)
#     data = resp.json()

#     if data.get('status') != 'OK' or not data.get('results'):
#         return None

#     result = data['results'][0]
#     components = result.get('address_components', [])

#     def find_component(*type_names):
#         for c in components:
#             types = c.get('types', [])
#             if any(t in types for t in type_names):
#                 return c['long_name']
#         return None

#     # Most specific -> least specific. This is what actually gets you
#     # "area near this zip" instead of just "the whole city".
#     neighborhood = find_component('neighborhood')
#     sublocality = find_component('sublocality_level_1', 'sublocality')
#     city = find_component('locality') or find_component('administrative_area_level_2')
#     state = find_component('administrative_area_level_1')

#     # The most specific name we have — used for the actual news search.
#     area_name = neighborhood or sublocality or city

#     return {
#         'area_name': area_name,        # e.g. "Rohini" or "Sector 15"
#         'city': city,                   # e.g. "Delhi"
#         'state': state,
#         'formatted_address': result.get('formatted_address'),
#         'lat': result['geometry']['location']['lat'],
#         'lng': result['geometry']['location']['lng']
#     }


# def clean_text(text):
#     """
#     NewsAPI's free tier truncates description/content mid-sentence and
#     appends '… [+1234 chars]'. Strip that, then trim back to the last
#     complete sentence so nothing reads as cut off.
#     """ 
#     if not text:
#         return ''

#     # Remove NewsAPI's truncation marker, e.g. "... [+1532 chars]"
#     text = re.sub(r'\s*\[\+\d+\s*chars\]\s*$', '', text).strip()
#     text = re.sub(r'\u2026\s*$', '', text).strip()  # trailing ellipsis char

#     if not text:
#         return ''

#     # If it doesn't end on sentence punctuation, trim back to the last
#     # sentence boundary so we never hand the LLM (or the user) a
#     # sentence fragment.
#     if text[-1] not in '.!?':
#         last_period = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
#         if last_period > 40:  # keep it only if we're not left with almost nothing
#             text = text[:last_period + 1]

#     return text.strip()


# def build_query(area_name, city):
#     """
#     Build a NewsAPI query scoped to the area AND real-estate-relevant topics,
#     with obviously irrelevant topics excluded at the API level.
#     """
#     location_part = f'"{area_name}"'
#     if city and city.lower() != (area_name or '').lower():
#         location_part = f'({location_part} OR "{city}")'

#     topic_part = '(' + ' OR '.join(f'"{t}"' for t in RELEVANCE_TERMS) + ')'
#     exclude_part = ' '.join(f'-{t}' for t in EXCLUDE_TERMS)

#     return f'{location_part} AND {topic_part} {exclude_part}'


# def fetch_news(area_name, city):
#     """Fetch recent, topically-relevant news articles using NewsAPI.org"""
#     url = "https://newsapi.org/v2/everything"
#     query = build_query(area_name, city)

#     params = {
#         'q': query,
#         'sortBy': 'relevancy',   # relevance to the query, not just newest
#         'language': 'en',
#         'pageSize': 20,          # pull a wider candidate pool for the LLM to pick from
#         'apiKey': NEWS_API_KEY
#     }
#     logger.info(f"[NEWS FETCH] Query: {query}")
#     resp = requests.get(url, params=params, timeout=10)
#     data = resp.json()
#     logger.info(
#         f"[NEWS FETCH] status={data.get('status')}, "
#         f"totalResults={data.get('totalResults')}, "
#         f"returned={len(data.get('articles', []))}"
#     )

#     if data.get('status') != 'ok':
#         logger.warning(f"[NEWS FETCH] NewsAPI returned non-ok status: {data}")
#         return []

#     # If the topic-filtered query returns too little (common for small
#     # towns/areas), fall back to a looser location-only query so the
#     # user still gets something instead of an empty state.
#     articles_raw = data.get('articles', [])
#     if len(articles_raw) < 3:
#         logger.info("[NEWS FETCH] Sparse results, retrying with broader location-only query")
#         fallback_params = dict(params)
#         fallback_params['q'] = f'"{area_name}"' if area_name else f'"{city}"'
#         resp = requests.get(url, params=fallback_params, timeout=10)
#         data = resp.json()
#         if data.get('status') == 'ok':
#             articles_raw = data.get('articles', [])

#     articles = []
#     for a in articles_raw[:20]:
#         articles.append({
#             'title': clean_text(a.get('title')),
#             'description': clean_text(a.get('description')),
#             'source': a.get('source', {}).get('name'),
#             'url': a.get('url'),
#             'published_at': a.get('publishedAt')
#         })
#     return articles


# def summarize_news(articles, area_name, city):
#     """
#     Use Groq to FILTER for real-estate-buyer relevance and condense the
#     relevant articles into 3-4 short points. Explicitly told to discard
#     crime/celebrity/generic-city news that doesn't affect a buying decision.
#     """
#     if not articles:
#         return []

#     articles_text = "\n\n".join([
#         f"- {a['title']}: {a['description']}" for a in articles if a['title']
#     ])

#     location_label = area_name or city

#     prompt = f"""You are screening local news for someone deciding whether to BUY a house or flat in {location_label}, {city}.

# ARTICLES:
# {articles_text}

# TASK:
# 1. From the articles above, keep ONLY the ones that would matter to a home buyer:
#    - New infrastructure or transit (roads, metro, flyovers)
#    - New residential/commercial development or major projects
#    - Utilities and civic services (water, power, sanitation)
#    - Genuine safety/security developments (e.g. new police station, better lighting) —
#      NOT routine crime-blotter stories
#    - Schools, hospitals, connectivity, or major economic investment in the area
# 2. Discard anything generic to the wider city that isn't tied to this specific area,
#    and discard crime, politics, celebrity, or entertainment stories unless they
#    directly involve real estate or development.
# 3. If NOTHING qualifies, return an empty "points" list — do not force irrelevant
#    stories in just to hit a count.
# 4. Otherwise, write 3-4 bullet points (12-20 words each), in your own words,
#    each ending on a complete sentence. Do not cut off mid-sentence.

# Respond in this exact JSON format and nothing else:
# {{
#   "points": ["point 1", "point 2", "point 3"]
# }}
# """

#     try:
#         completion = groq_client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.2,
#             max_tokens=500
#         )

#         raw = completion.choices[0].message.content.strip()
#         clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.DOTALL).strip()
#         match = re.search(r'\{.*\}', clean, re.DOTALL)
#         if match:
#             points = json.loads(match.group()).get('points', [])
#             # belt-and-suspenders: strip any lingering truncation artifacts
#             return [clean_text(p) for p in points if p and clean_text(p)]
#         return []
#     except Exception as e:
#         logger.error(f"[NEWS SUMMARIZE ERROR] {e}")
#         return []


# # ============================================================
# # GET /api/news/area?zip_code=110001
# # ============================================================

# @news_bp.route('/area', methods=['GET'])
# def get_area_news():
#     try:
#         from app import supabase

#         zip_code = request.args.get('zip_code', '').strip()
#         if not zip_code:
#             return jsonify({'error': 'zip_code is required'}), 400

#         # ── Check cache first ────────────────────────────────
#         cache_result = supabase.table('area_news_cache') \
#             .select('*') \
#             .eq('zip_code', zip_code) \
#             .execute()

#         if cache_result.data:
#             cached = cache_result.data[0]
#             fetched_at = datetime.fromisoformat(cached['fetched_at'].replace('Z', '+00:00'))
#             age = datetime.now(timezone.utc) - fetched_at

#             if age < timedelta(hours=CACHE_TTL_HOURS):
#                 logger.info(f"[AREA NEWS] Cache hit for {zip_code}")
#                 return jsonify({
#                     'success': True,
#                     'zip_code': zip_code,
#                     'location': {
#                         'area_name': cached.get('area_name'),
#                         'city': cached['city'],
#                         'formatted_address': cached['formatted_address'],
#                         'lat': cached['lat'],
#                         'lng': cached['lng']
#                     },
#                     'summary_points': cached['summary_points'],
#                     'articles': cached['articles'],
#                     'cached': True
#                 }), 200

#         # ── Cache miss or stale — fetch fresh ────────────────
#         location = zip_to_location(zip_code)
#         if not location or not location.get('city'):
#             return jsonify({'error': 'Could not resolve zip code to a location'}), 404

#         articles = fetch_news(location['area_name'], location['city'])
#         points = summarize_news(articles, location['area_name'], location['city'])

#         # ── Upsert into cache ─────────────────────────────────
#         supabase.table('area_news_cache').upsert({
#             'zip_code': zip_code,
#             'area_name': location['area_name'],
#             'city': location['city'],
#             'formatted_address': location['formatted_address'],
#             'lat': location['lat'],
#             'lng': location['lng'],
#             'summary_points': points,
#             'articles': articles,
#             'fetched_at': datetime.now(timezone.utc).isoformat()
#         }, on_conflict='zip_code').execute()

#         return jsonify({
#             'success': True,
#             'zip_code': zip_code,
#             'location': location,
#             'summary_points': points,
#             'articles': articles,
#             'cached': False
#         }), 200

#     except Exception as e:
#         logger.error(f"[AREA NEWS ERROR] {e}")
#         return jsonify({'error': 'Failed to fetch area news', 'details': str(e)}), 500


# # ============================================================
# # HEALTH CHECK
# # GET /api/news/health
# # ============================================================

# @news_bp.route('/health', methods=['GET'])
# def health():
#     return jsonify({
#         'status': 'healthy',
#         'module': 'area_news',
#         'endpoints': [
#             'GET /api/news/area?zip_code=110001 — fetch and summarize local news for a zip code'
#         ]
#     }), 200

"""
news_routes.py — Local Area News for a given zip code
Flow: zip_code -> geocode to neighborhood/city (Google Maps) -> fetch targeted
      real-estate-relevant news (Google News RSS, free) -> clean + filter +
      summarize (Groq) -> cache in Supabase (area_news_cache)
"""

from flask import Blueprint, request, jsonify
import os
import json
import re
import logging
import requests
import feedparser
from bs4 import BeautifulSoup
from googlenewsdecoder import new_decoderv1
from urllib.parse import quote_plus
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from groq import Groq

logger = logging.getLogger(__name__)
news_bp = Blueprint('news', __name__, url_prefix='/api/news')

groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  # reuse your existing key

CACHE_TTL_HOURS = 6  # how long before cached news is considered stale

# Topic hints appended to the search — expanded to cover what an actual
# home buyer cares about: new builder/developer activity, not just generic
# civic infrastructure.
RELEVANCE_TERMS = [
    # New development / builder activity — the main thing buyers want
    'new project', 'project launch', 'residential project', 'apartment',
    'flats', 'residential complex', 'gated community', 'township',
    'builder', 'developer', 'possession', 'RERA', 'under construction',
    # Civic infrastructure that affects property value
    'infrastructure', 'metro', 'construction', 'housing', 'road',
    'flyover', 'water supply', 'electricity', 'school', 'hospital',
    'connectivity', 'commercial complex', 'IT park', 'mall'
]

# Terms that reliably signal a story is NOT relevant to a home buyer —
# used as Google search '-exclusions' to keep crime/entertainment noise
# (which is what was flooding results) out of the candidate pool.
EXCLUDE_TERMS = [
    'crime', 'murder', 'accident', 'police', 'shooting', 'arrest',
    'red light', 'championship', 'youtube', 'celebrity', 'bollywood',
    'cricket', 'movie', 'election'
]


# ─── Helpers ────────────────────────────────────────────────

def zip_to_location(zip_code, locality_hint=None):
    """
    Convert zip code (optionally combined with a locality/society text hint
    from the frontend, e.g. what the user typed in an address field) to a
    specific area name using Google Geocoding API.

    A bare 6-digit Indian PIN code covers a large postal zone spanning many
    localities/societies — Google's geocoder almost never has a
    'neighborhood' component for a bare PIN, so without a locality_hint the
    best we can resolve to is usually just the city. Passing locality_hint
    (raw text like "Hari Nagar Society" or "Alkapuri") dramatically improves
    precision, since it lets Google match against an actual place name
    instead of guessing from the PIN alone.
    """
    # If we have real locality text, geocode "<locality>, <pin>" directly —
    # this is the only reliable way to get sub-city precision in India.
    address_query = f"{locality_hint}, {zip_code}" if locality_hint else zip_code

    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {'address': address_query, 'key': GOOGLE_MAPS_KEY}
    resp = requests.get(url, params=params, timeout=10)
    data = resp.json()

    logger.info(f"[GEOCODE] status={data.get('status')} for query='{address_query}'")

    if data.get('status') != 'OK' or not data.get('results'):
        logger.warning(f"[GEOCODE] Failed for query='{address_query}': {data.get('status')}")
        return None

    result = data['results'][0]
    components = result.get('address_components', [])

    def find_component(*type_names):
        for c in components:
            types = c.get('types', [])
            if any(t in types for t in type_names):
                return c['long_name']
        return None

    neighborhood = find_component('neighborhood')
    sublocality = (
        find_component('sublocality_level_1', 'sublocality')
        or find_component('sublocality_level_2')
        or find_component('sublocality_level_3')
    )
    city = find_component('locality') or find_component('administrative_area_level_2')
    state = find_component('administrative_area_level_1')

    # Prefer the user's own locality text if geocoding still only resolved
    # to city level — it's more specific than what Google gave us back.
    area_name = neighborhood or sublocality or locality_hint or city

    logger.info(
        f"[GEOCODE] Resolved query='{address_query}' -> "
        f"area='{area_name}', city='{city}' "
        f"(neighborhood={neighborhood!r}, sublocality={sublocality!r})"
    )

    return {
        'area_name': area_name,
        'city': city,
        'state': state,
        'formatted_address': result.get('formatted_address'),
        'lat': result['geometry']['location']['lat'],
        'lng': result['geometry']['location']['lng']
    }


def clean_text(text):
    """Strip HTML/truncation artifacts and avoid mid-sentence cutoffs."""
    if not text:
        return ''

    # Google News RSS descriptions are HTML — strip tags.
    text = re.sub(r'<[^>]+>', '', text).strip()
    text = re.sub(r'\s*\[\+\d+\s*chars\]\s*$', '', text).strip()
    text = re.sub(r'\u2026\s*$', '', text).strip()

    if not text:
        return ''

    if text[-1] not in '.!?':
        last_period = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
        if last_period > 40:
            text = text[:last_period + 1]

    return text.strip()


def build_queries(area_name, city):
    """
    Build a list of location-only Google News search queries — deliberately
    NOT combined with topic OR-lists or exclude minus-terms in the query
    string itself. Stuffing 20+ OR terms and a dozen exclusions into one
    query degrades Google News' matching quality (there's a practical
    complexity ceiling), which was causing genuinely relevant area-specific
    articles to disappear entirely from results.

    Instead: cast the widest reasonable net here, then do ALL topic
    relevance and exclusion filtering in Python (article_mentions_area,
    is_excluded) and in the LLM summarization step, where it actually
    works reliably.
    """
    queries = []
    if area_name and city and area_name != city:
        queries.append(f'"{area_name}" "{city}"')
    if area_name:
        queries.append(f'"{area_name}"')
    if city:
        queries.append(f'"{city}"')
    return queries


def resolve_real_url(google_news_url, timeout=6):
    """
    Google News RSS 'link' URLs are encoded redirect wrappers, not direct
    article URLs — a plain requests.get() just lands on Google's own page
    (which is why we were getting Google's generic boilerplate description
    back). This decodes the actual publisher URL Google's redirect encodes.
    """
    try:
        result = new_decoderv1(google_news_url, interval=1)
        if result and result.get('status') and result.get('decoded_url'):
            return result['decoded_url']
    except Exception as e:
        logger.debug(f"[URL DECODE] Failed for {google_news_url}: {e}")
    return None


def fetch_real_description(url, timeout=6):
    """
    Fetch the ACTUAL publisher article (after decoding the Google News
    redirect) and pull its real meta description — usually 1-3 genuine
    sentences written by the publisher, unlike the RSS feed's duplicate
    title.
    """
    real_url = resolve_real_url(url, timeout=timeout) or url

    try:
        resp = requests.get(
            real_url,
            timeout=timeout,
            allow_redirects=True,
            headers={'User-Agent': 'Mozilla/5.0 (compatible; PropDeckNewsBot/1.0)'}
        )
        if resp.status_code != 200:
            return None

        soup = BeautifulSoup(resp.text, 'html.parser')

        for selector in [
            {'property': 'og:description'},
            {'name': 'description'},
            {'name': 'twitter:description'},
        ]:
            tag = soup.find('meta', attrs=selector)
            if tag and tag.get('content'):
                desc = tag['content'].strip()
                # Skip Google's own generic boilerplate if it slips through
                if 'aggregated from sources all over the world' in desc.lower():
                    continue
                if len(desc) > 30:
                    return clean_text(desc)

        return None
    except Exception:
        return None


def enrich_descriptions(articles, max_workers=6):
    """
    Fetch real descriptions for a batch of articles in parallel (network
    I/O bound, so threads are fine here). Articles where the fetch fails
    or times out just keep their original RSS description as a fallback.
    """
    if not articles:
        return articles

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_article = {
            executor.submit(fetch_real_description, a['url']): a
            for a in articles
        }
        for future in as_completed(future_to_article, timeout=15):
            article = future_to_article[future]
            try:
                real_desc = future.result()
                if real_desc:
                    article['description'] = real_desc
            except Exception:
                pass  # keep original RSS description on any failure

    return articles


def article_mentions_area(article, area_name):
    """Does the article's title/description actually contain the area name?"""
    if not area_name:
        return False
    haystack = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return area_name.lower() in haystack


def article_mentions_city(article, city):
    if not city:
        return False
    haystack = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return city.lower() in haystack


def article_is_excluded(article):
    """Python-side exclusion check — dropping the exclude terms from the
    Google query string (see build_queries) meant this filtering needs to
    happen here instead."""
    haystack = f"{article.get('title', '')} {article.get('description', '')}".lower()
    return any(term in haystack for term in EXCLUDE_TERMS)


def fetch_news(area_name, city):
    """
    Fetch recent news via Google News RSS (free, no API key, no rate limit).

    Returns TWO tiers:
      - area_specific: articles mentioning BOTH the area name AND the city
        (when both are known) — this dual requirement is what actually
        prevents cross-city contamination (e.g. Alkapuri exists in both
        Vadodara and Bhopal; requiring both names present rules out the
        wrong one)
      - city_wide: articles that only mention the city, used as capped
        filler if area_specific coverage is thin

    Topic relevance and junk exclusion are NOT baked into the search query
    (that degraded matching quality) — they're applied here in Python and
    in the LLM summarization step instead.
    """
    seen_urls = set()
    area_specific = []
    city_wide = []

    for query in build_queries(area_name, city):
        rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
        logger.info(f"[NEWS FETCH] Query: {query}")

        try:
            feed = feedparser.parse(rss_url)
            logger.info(f"[NEWS FETCH] Got {len(feed.entries)} entries for query='{query}'")
        except Exception as e:
            logger.error(f"[NEWS FETCH ERROR] {e} for query='{query}'")
            continue

        for entry in feed.entries[:25]:
            url = entry.get('link')
            if not url or url in seen_urls:
                continue
            seen_urls.add(url)

            source = ''
            if hasattr(entry, 'source') and entry.source:
                source = entry.source.get('title', '')

            article = {
                'title': clean_text(entry.get('title', '')),
                'description': clean_text(entry.get('summary', '')),
                'source': source,
                'url': url,
                'published_at': entry.get('published', '')
            }

            if article_is_excluded(article):
                continue  # drop crime/entertainment/etc noise immediately

            mentions_area = article_mentions_area(article, area_name)
            mentions_city = article_mentions_city(article, city)

            if mentions_area and (not city or mentions_city):
                # Requires BOTH area and city (when city is known) — this
                # is what prevents e.g. Bhopal's Alkapuri leaking into
                # Vadodara results.
                area_specific.append(article)
            elif mentions_city:
                city_wide.append(article)
            # else: mentions neither — pure noise, discard

        if len(area_specific) >= 8:
            break

    logger.info(
        f"[NEWS FETCH] area_specific={len(area_specific)}, "
        f"city_wide(candidate)={len(city_wide)}"
    )

    city_wide_allowance = max(0, 5 - len(area_specific))
    combined = area_specific[:12] + city_wide[:city_wide_allowance]

    combined = enrich_descriptions(combined)

    for a in combined:
        a['scope'] = 'area' if article_mentions_area(a, area_name) else 'city'

    return combined


def summarize_news(articles, area_name, city):
    """
    Use Groq to FILTER for real-estate-buyer relevance and condense the
    relevant articles into 3-4 short points. This is where relevance
    filtering actually happens now (not at the search-query level), since
    the LLM is much better at judging relevance than a keyword query.
    """
    if not articles:
        logger.info("[NEWS SUMMARIZE] No articles to summarize")
        return []

    articles_text = "\n\n".join([
        f"- [{a.get('scope', 'city').upper()}] {a['title']}: {a['description']}"
        for a in articles if a['title']
    ])

    location_label = area_name or city

    prompt = f"""You are screening local news for someone deciding whether to BUY a house or flat in {location_label}, {city}.

Each article below is tagged [AREA] (specifically about {location_label}) or [CITY] (about {city} generally, not necessarily {location_label}).

ARTICLES:
{articles_text}

TASK:
1. From the articles above, keep ONLY the ones that would matter to a home buyer:
   - New residential/commercial project launches, builder/developer activity, possession updates, RERA news
   - New infrastructure or transit (roads, metro, flyovers) near or serving the area
   - Utilities and civic services (water, power, sanitation)
   - Genuine safety/security developments — NOT routine crime-blotter stories
   - Schools, hospitals, connectivity, or major economic investment in the area
2. STRONGLY prefer [AREA]-tagged articles. Only include a [CITY]-tagged article if it is
   a major development that would clearly matter city-wide to a buyer (e.g. a large new
   metro line, a major developer entering the city) — and if you do include one, start
   that point with "Citywide:" so it's clear it isn't specific to {location_label}.
3. Discard crime, politics, celebrity, religious events, or entertainment stories unless
   they directly involve real estate or development.
4. If NOTHING qualifies, return an empty "points" list — do not force irrelevant
   stories in just to hit a count.
5. Otherwise, write 3-4 bullet points (15-25 words each), in your own words, using the
   real description content (not just the headline) where available. Each point must end
   on a complete sentence — do not cut off mid-sentence.

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
        logger.info(f"[NEWS SUMMARIZE] Raw LLM output: {raw[:300]}")
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.DOTALL).strip()
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if match:
            points = json.loads(match.group()).get('points', [])
            return [clean_text(p) for p in points if p and clean_text(p)]
        logger.warning("[NEWS SUMMARIZE] Could not find JSON in LLM output")
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
        locality_hint = request.args.get('locality', '').strip() or None
        if not zip_code:
            return jsonify({'error': 'zip_code is required'}), 400

        # Cache key includes the locality hint so different societies under
        # the same PIN don't share a cache entry.
        cache_key = f"{zip_code}:{locality_hint}" if locality_hint else zip_code

        # ── Check cache first ────────────────────────────────
        cache_result = supabase.table('area_news_cache') \
            .select('*') \
            .eq('zip_code', cache_key) \
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
        location = zip_to_location(zip_code, locality_hint)
        if not location or not location.get('city'):
            return jsonify({'error': 'Could not resolve zip code to a location'}), 404

        articles = fetch_news(location['area_name'], location['city'])
        points = summarize_news(articles, location['area_name'], location['city'])

        logger.info(
            f"[AREA NEWS] zip={zip_code} locality_hint={locality_hint!r} "
            f"resolved_area='{location['area_name']}' "
            f"articles_fetched={len(articles)} summary_points={len(points)}"
        )

        # ── Upsert into cache ─────────────────────────────────
        supabase.table('area_news_cache').upsert({
            'zip_code': cache_key,
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
        'source': 'Google News RSS (free)',
        'endpoints': [
            'GET /api/news/area?zip_code=110001 — fetch and summarize local news for a zip code'
        ]
    }), 200