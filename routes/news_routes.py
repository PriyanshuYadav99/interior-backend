
# """
# news_routes.py — Local Area News for a given zip code
# Flow: zip_code -> geocode to neighborhood/city (Google Maps) -> fetch targeted
#       real-estate-relevant news (Google News RSS, free) -> clean + filter +
#       summarize (Groq) -> cache in Supabase (area_news_cache)
# """

# from flask import Blueprint, request, jsonify
# import os
# import json
# import re
# import logging
# import requests
# import feedparser
# from bs4 import BeautifulSoup
# from googlenewsdecoder import new_decoderv1
# from urllib.parse import quote_plus
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from datetime import datetime, timedelta, timezone
# from groq import Groq

# logger = logging.getLogger(__name__)
# news_bp = Blueprint('news', __name__, url_prefix='/api/news')

# groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
# GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  # reuse your existing key

# CACHE_TTL_HOURS = 6  # how long before cached news is considered stale

# # Topic hints appended to the search — expanded to cover what an actual
# # home buyer cares about: new builder/developer activity, not just generic
# # civic infrastructure.
# RELEVANCE_TERMS = [
#     # New development / builder activity — the main thing buyers want
#     'new project', 'project launch', 'residential project', 'apartment',
#     'flats', 'residential complex', 'gated community', 'township',
#     'builder', 'developer', 'possession', 'RERA', 'under construction',
#     # Civic infrastructure that affects property value
#     'infrastructure', 'metro', 'construction', 'housing', 'road',
#     'flyover', 'water supply', 'electricity', 'school', 'hospital',
#     'connectivity', 'commercial complex', 'IT park', 'mall'
# ]

# # Terms that reliably signal a story is NOT relevant to a home buyer —
# # used as Google search '-exclusions' to keep crime/entertainment noise
# # (which is what was flooding results) out of the candidate pool.
# EXCLUDE_TERMS = [
#     'crime', 'murder', 'accident', 'police', 'shooting', 'arrest',
#     'red light', 'championship', 'youtube', 'celebrity', 'bollywood',
#     'cricket', 'movie', 'election'
# ]


# # ─── Helpers ────────────────────────────────────────────────

# def zip_to_location(zip_code, locality_hint=None):
#     """
#     Convert zip code (optionally combined with a locality/society text hint
#     from the frontend, e.g. what the user typed in an address field) to a
#     specific area name using Google Geocoding API.

#     A bare 6-digit Indian PIN code covers a large postal zone spanning many
#     localities/societies — Google's geocoder almost never has a
#     'neighborhood' component for a bare PIN, so without a locality_hint the
#     best we can resolve to is usually just the city. Passing locality_hint
#     (raw text like "Hari Nagar Society" or "Alkapuri") dramatically improves
#     precision, since it lets Google match against an actual place name
#     instead of guessing from the PIN alone.
#     """
#     # If we have real locality text, geocode "<locality>, <pin>" directly —
#     # this is the only reliable way to get sub-city precision in India.
#     address_query = f"{locality_hint}, {zip_code}" if locality_hint else zip_code

#     url = "https://maps.googleapis.com/maps/api/geocode/json"
#     params = {'address': address_query, 'key': GOOGLE_MAPS_KEY}
#     resp = requests.get(url, params=params, timeout=10)
#     data = resp.json()

#     logger.info(f"[GEOCODE] status={data.get('status')} for query='{address_query}'")

#     if data.get('status') != 'OK' or not data.get('results'):
#         logger.warning(f"[GEOCODE] Failed for query='{address_query}': {data.get('status')}")
#         return None

#     result = data['results'][0]
#     components = result.get('address_components', [])

#     def find_component(*type_names):
#         for c in components:
#             types = c.get('types', [])
#             if any(t in types for t in type_names):
#                 return c['long_name']
#         return None

#     neighborhood = find_component('neighborhood')
#     sublocality = (
#         find_component('sublocality_level_1', 'sublocality')
#         or find_component('sublocality_level_2')
#         or find_component('sublocality_level_3')
#     )
#     city = find_component('locality') or find_component('administrative_area_level_2')
#     state = find_component('administrative_area_level_1')

#     # Prefer the user's own locality text if geocoding still only resolved
#     # to city level — it's more specific than what Google gave us back.
#     area_name = neighborhood or sublocality or locality_hint or city

#     logger.info(
#         f"[GEOCODE] Resolved query='{address_query}' -> "
#         f"area='{area_name}', city='{city}' "
#         f"(neighborhood={neighborhood!r}, sublocality={sublocality!r})"
#     )

#     return {
#         'area_name': area_name,
#         'city': city,
#         'state': state,
#         'formatted_address': result.get('formatted_address'),
#         'lat': result['geometry']['location']['lat'],
#         'lng': result['geometry']['location']['lng']
#     }


# def clean_text(text):
#     """Strip HTML/truncation artifacts and avoid mid-sentence cutoffs."""
#     if not text:
#         return ''

#     # Google News RSS descriptions are HTML — strip tags.
#     text = re.sub(r'<[^>]+>', '', text).strip()
#     text = re.sub(r'\s*\[\+\d+\s*chars\]\s*$', '', text).strip()
#     text = re.sub(r'\u2026\s*$', '', text).strip()

#     if not text:
#         return ''

#     if text[-1] not in '.!?':
#         last_period = max(text.rfind('.'), text.rfind('!'), text.rfind('?'))
#         if last_period > 40:
#             text = text[:last_period + 1]

#     return text.strip()


# def build_queries(area_name, city):
#     """
#     Build a list of location-only Google News search queries — deliberately
#     NOT combined with topic OR-lists or exclude minus-terms in the query
#     string itself. Stuffing 20+ OR terms and a dozen exclusions into one
#     query degrades Google News' matching quality (there's a practical
#     complexity ceiling), which was causing genuinely relevant area-specific
#     articles to disappear entirely from results.

#     Instead: cast the widest reasonable net here, then do ALL topic
#     relevance and exclusion filtering in Python (article_mentions_area,
#     is_excluded) and in the LLM summarization step, where it actually
#     works reliably.
#     """
#     queries = []
#     if area_name and city and area_name != city:
#         queries.append(f'"{area_name}" "{city}"')
#     if area_name:
#         queries.append(f'"{area_name}"')
#     if city:
#         queries.append(f'"{city}"')
#     return queries


# def resolve_real_url(google_news_url, timeout=6):
#     """
#     Google News RSS 'link' URLs are encoded redirect wrappers, not direct
#     article URLs — a plain requests.get() just lands on Google's own page
#     (which is why we were getting Google's generic boilerplate description
#     back). This decodes the actual publisher URL Google's redirect encodes.
#     """
#     try:
#         result = new_decoderv1(google_news_url, interval=1)
#         if result and result.get('status') and result.get('decoded_url'):
#             return result['decoded_url']
#     except Exception as e:
#         logger.debug(f"[URL DECODE] Failed for {google_news_url}: {e}")
#     return None


# def fetch_real_description(url, timeout=6):
#     """
#     Fetch the ACTUAL publisher article (after decoding the Google News
#     redirect) and pull its real meta description — usually 1-3 genuine
#     sentences written by the publisher, unlike the RSS feed's duplicate
#     title.
#     """
#     real_url = resolve_real_url(url, timeout=timeout) or url

#     try:
#         resp = requests.get(
#             real_url,
#             timeout=timeout,
#             allow_redirects=True,
#             headers={'User-Agent': 'Mozilla/5.0 (compatible; PropDeckNewsBot/1.0)'}
#         )
#         if resp.status_code != 200:
#             return None

#         soup = BeautifulSoup(resp.text, 'html.parser')

#         for selector in [
#             {'property': 'og:description'},
#             {'name': 'description'},
#             {'name': 'twitter:description'},
#         ]:
#             tag = soup.find('meta', attrs=selector)
#             if tag and tag.get('content'):
#                 desc = tag['content'].strip()
#                 # Skip Google's own generic boilerplate if it slips through
#                 if 'aggregated from sources all over the world' in desc.lower():
#                     continue
#                 if len(desc) > 30:
#                     return clean_text(desc)

#         return None
#     except Exception:
#         return None


# def enrich_descriptions(articles, max_workers=6):
#     """
#     Fetch real descriptions for a batch of articles in parallel (network
#     I/O bound, so threads are fine here). Articles where the fetch fails
#     or times out just keep their original RSS description as a fallback.
#     """
#     if not articles:
#         return articles

#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         future_to_article = {
#             executor.submit(fetch_real_description, a['url']): a
#             for a in articles
#         }
#         for future in as_completed(future_to_article, timeout=15):
#             article = future_to_article[future]
#             try:
#                 real_desc = future.result()
#                 if real_desc:
#                     article['description'] = real_desc
#             except Exception:
#                 pass  # keep original RSS description on any failure

#     return articles


# def article_mentions_area(article, area_name):
#     """Does the article's title/description actually contain the area name?"""
#     if not area_name:
#         return False
#     haystack = f"{article.get('title', '')} {article.get('description', '')}".lower()
#     return area_name.lower() in haystack


# def article_mentions_city(article, city):
#     if not city:
#         return False
#     haystack = f"{article.get('title', '')} {article.get('description', '')}".lower()
#     return city.lower() in haystack


# def article_is_excluded(article):
#     """Python-side exclusion check — dropping the exclude terms from the
#     Google query string (see build_queries) meant this filtering needs to
#     happen here instead."""
#     haystack = f"{article.get('title', '')} {article.get('description', '')}".lower()
#     return any(term in haystack for term in EXCLUDE_TERMS)


# def fetch_news(area_name, city):
#     """
#     Fetch recent news via Google News RSS (free, no API key, no rate limit).

#     Returns TWO tiers:
#       - area_specific: articles mentioning BOTH the area name AND the city
#         (when both are known) — this dual requirement is what actually
#         prevents cross-city contamination (e.g. Alkapuri exists in both
#         Vadodara and Bhopal; requiring both names present rules out the
#         wrong one)
#       - city_wide: articles that only mention the city, used as capped
#         filler if area_specific coverage is thin

#     Topic relevance and junk exclusion are NOT baked into the search query
#     (that degraded matching quality) — they're applied here in Python and
#     in the LLM summarization step instead.
#     """
#     seen_urls = set()
#     area_specific = []
#     city_wide = []

#     for query in build_queries(area_name, city):
#         rss_url = f"https://news.google.com/rss/search?q={quote_plus(query)}&hl=en-IN&gl=IN&ceid=IN:en"
#         logger.info(f"[NEWS FETCH] Query: {query}")

#         try:
#             feed = feedparser.parse(rss_url)
#             logger.info(f"[NEWS FETCH] Got {len(feed.entries)} entries for query='{query}'")
#         except Exception as e:
#             logger.error(f"[NEWS FETCH ERROR] {e} for query='{query}'")
#             continue

#         for entry in feed.entries[:25]:
#             url = entry.get('link')
#             if not url or url in seen_urls:
#                 continue
#             seen_urls.add(url)

#             source = ''
#             if hasattr(entry, 'source') and entry.source:
#                 source = entry.source.get('title', '')

#             article = {
#                 'title': clean_text(entry.get('title', '')),
#                 'description': clean_text(entry.get('summary', '')),
#                 'source': source,
#                 'url': url,
#                 'published_at': entry.get('published', '')
#             }

#             if article_is_excluded(article):
#                 continue  # drop crime/entertainment/etc noise immediately

#             mentions_area = article_mentions_area(article, area_name)
#             mentions_city = article_mentions_city(article, city)

#             if mentions_area and (not city or mentions_city):
#                 # Requires BOTH area and city (when city is known) — this
#                 # is what prevents e.g. Bhopal's Alkapuri leaking into
#                 # Vadodara results.
#                 area_specific.append(article)
#             elif mentions_city:
#                 city_wide.append(article)
#             # else: mentions neither — pure noise, discard

#         if len(area_specific) >= 8:
#             break

#     logger.info(
#         f"[NEWS FETCH] area_specific={len(area_specific)}, "
#         f"city_wide(candidate)={len(city_wide)}"
#     )

#     city_wide_allowance = max(0, 5 - len(area_specific))
#     combined = area_specific[:12] + city_wide[:city_wide_allowance]

#     combined = enrich_descriptions(combined)

#     for a in combined:
#         a['scope'] = 'area' if article_mentions_area(a, area_name) else 'city'

#     return combined


# CARD_CATEGORIES = [
#     "Transit & Commute",
#     "Parks & Recreation",
#     "Commercial & Amenities",
#     "Housing & Development",
#     "Utilities & Safety",
#     "Education & Healthcare",
# ]


# def summarize_news(articles, area_name, city):
#     """
#     Use Groq to FILTER for real-estate-buyer relevance and turn relevant
#     articles into structured 'Local Watch' cards:
#     {category, title, date, bullets[], why_helps}
#     """
#     if not articles:
#         logger.info("[NEWS SUMMARIZE] No articles to summarize")
#         return []

#     articles_text = "\n\n".join([
#         f"- [{a.get('scope', 'city').upper()}] {a['title']}: {a['description']} "
#         f"(published: {a.get('published_at', 'unknown')})"
#         for a in articles if a['title']
#     ])

#     location_label = area_name or city
#     categories_list = ", ".join(CARD_CATEGORIES)

#     prompt = f"""You are screening local news for someone deciding whether to BUY a house or flat in {location_label}, {city}.

# Each article below is tagged [AREA] (specifically about {location_label}) or [CITY] (about {city} generally).

# ARTICLES:
# {articles_text}

# TASK:
# 1. Keep ONLY articles that matter to a home buyer: new residential/commercial project
#    launches, builder/developer activity, possession updates, RERA news, new infrastructure
#    or transit, utilities/civic services, genuine safety developments (not routine crime),
#    schools, hospitals, connectivity, or major economic investment.
# 2. STRONGLY prefer [AREA]-tagged articles. Only include [CITY]-tagged ones if clearly
#    major and city-wide — prefix that title with "Citywide: ".
# 3. Discard crime, politics, celebrity, religious, or entertainment stories unless tied to
#    real estate/development.
# 4. Assign EACH kept article to exactly ONE category from this fixed list: {categories_list}
# 5. For each kept article write:
#    - "title": clear headline in your own words (8-15 words)
#    - "bullets": 1-2 factual points (15-25 words each), your own words
#    - "why_helps": one sentence (15-25 words) on why it matters to a home buyer
#    - "date": published month/year if known, format "Mon YYYY" (e.g. "Sep 2026"), else ""
# 6. If nothing qualifies, return an empty "cards" list.

# Respond in this exact JSON format and nothing else:
# {{
#   "cards": [
#     {{
#       "category": "Transit & Commute",
#       "title": "...",
#       "date": "Sep 2026",
#       "bullets": ["...", "..."],
#       "why_helps": "..."
#     }}
#   ]
# }}
# """

#     try:
#         completion = groq_client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.2,
#             max_tokens=1200
#         )

#         raw = completion.choices[0].message.content.strip()
#         logger.info(f"[NEWS SUMMARIZE] Raw LLM output: {raw[:300]}")
#         clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.DOTALL).strip()
#         match = re.search(r'\{.*\}', clean, re.DOTALL)
#         if not match:
#             logger.warning("[NEWS SUMMARIZE] Could not find JSON in LLM output")
#             return []

#         raw_cards = json.loads(match.group()).get('cards', [])
#         cards = []
#         for i, c in enumerate(raw_cards):
#             category = c.get('category') if c.get('category') in CARD_CATEGORIES else 'Commercial & Amenities'
#             title = clean_text(c.get('title', ''))
#             bullets = [clean_text(b) for b in c.get('bullets', []) if b and clean_text(b)]
#             why_helps = clean_text(c.get('why_helps', ''))
#             if not title or not bullets:
#                 continue
#             cards.append({
#                 'id': f'card-{i}',
#                 'category': category,
#                 'title': title,
#                 'date': c.get('date', ''),
#                 'bullets': bullets,
#                 'why_helps': why_helps,
#             })
#         return cards
#     except Exception as e:
#         logger.error(f"[NEWS SUMMARIZE ERROR] {e}")
#         return []


# def build_categories_summary(cards):
#     """Turn a flat card list into [{name, count}] for the filter pills."""
#     counts = {}
#     for c in cards:
#         counts[c['category']] = counts.get(c['category'], 0) + 1
#     return [{'name': name, 'count': count} for name, count in counts.items()]


# # ============================================================
# # GET /api/news/area?zip_code=110001
# # ============================================================

# @news_bp.route('/area', methods=['GET'])
# def get_area_news():
#     try:
#         from app import supabase

#         zip_code = request.args.get('zip_code', '').strip()
#         locality_hint = request.args.get('locality', '').strip() or None
#         if not zip_code:
#             return jsonify({'error': 'zip_code is required'}), 400

#         # Cache key includes the locality hint so different societies under
#         # the same PIN don't share a cache entry.
#         cache_key = f"{zip_code}:{locality_hint}" if locality_hint else zip_code

#         # ── Check cache first ────────────────────────────────
#         cache_result = supabase.table('area_news_cache') \
#             .select('*') \
#             .eq('zip_code', cache_key) \
#             .execute()

#         if cache_result.data:
#             cached = cache_result.data[0]
#             fetched_at = datetime.fromisoformat(cached['fetched_at'].replace('Z', '+00:00'))
#             age = datetime.now(timezone.utc) - fetched_at

#             if age < timedelta(hours=CACHE_TTL_HOURS):
#                 logger.info(f"[AREA NEWS] Cache hit for {zip_code}")
#                 cards = cached.get('cards') or []
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
#                     'cards': cards,
#                     'categories': build_categories_summary(cards),
#                     'articles': cached['articles'],
#                     'cached': True
#                 }), 200

#         # ── Cache miss or stale — fetch fresh ────────────────
#         location = zip_to_location(zip_code, locality_hint)
#         if not location or not location.get('city'):
#             return jsonify({'error': 'Could not resolve zip code to a location'}), 404

#         articles = fetch_news(location['area_name'], location['city'])
#         cards = summarize_news(articles, location['area_name'], location['city'])

#         logger.info(
#             f"[AREA NEWS] zip={zip_code} locality_hint={locality_hint!r} "
#             f"resolved_area='{location['area_name']}' "
#             f"articles_fetched={len(articles)} cards={len(cards)}"
#         )

#         supabase.table('area_news_cache').upsert({
#             'zip_code': cache_key,
#             'area_name': location['area_name'],
#             'city': location['city'],
#             'formatted_address': location['formatted_address'],
#             'lat': location['lat'],
#             'lng': location['lng'],
#             'cards': cards,
#             'articles': articles,
#             'fetched_at': datetime.now(timezone.utc).isoformat()
#         }, on_conflict='zip_code').execute()

#         return jsonify({
#             'success': True,
#             'zip_code': zip_code,
#             'location': location,
#             'cards': cards,
#             'categories': build_categories_summary(cards),
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
#         'source': 'Google News RSS (free)',
#         'endpoints': [
#             'GET /api/news/area?zip_code=110001 — fetch and summarize local news for a zip code'
#         ]
#     }), 200
"""
news_routes.py — Local Area News for a given zip code
Flow: zip_code -> geocode to neighborhood/city (Google Maps) -> Gemini with
      Google Search grounding finds + summarizes real-estate-relevant local
      news in one call -> cache in Supabase (area_news_cache)

NOTE: This replaces the earlier Google-News-RSS + Groq pipeline. Gemini's
Google Search grounding tool searches live Google Search results itself and
returns structured output plus real grounding citations, so there's no more
RSS scraping, redirect-decoding, or separate meta-description fetching.
"""

from flask import Blueprint, request, jsonify
import os
import json
import re
import logging
import requests
from datetime import datetime, timedelta, timezone
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)
news_bp = Blueprint('news', __name__, url_prefix='/api/news')

gemini_client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))
GOOGLE_MAPS_KEY = os.getenv('GOOGLE_MAPS_API_KEY')  # reuse your existing key

CACHE_TTL_HOURS = 6  # how long before cached news is considered stale

CARD_CATEGORIES = [
    "Transit & Commute",
    "Parks & Recreation",
    "Commercial & Amenities",
    "Housing & Development",
    "Utilities & Safety",
    "Education & Healthcare",
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
            types_ = c.get('types', [])
            if any(t in types_ for t in type_names):
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


def fetch_grounded_cards(area_name, city):
    """
    Use Gemini with Google Search grounding to find AND summarize relevant
    local news for a home buyer in a single call. Gemini searches live
    Google Search results itself (no RSS feed, no scraping) and we ask it
    to return structured JSON cards directly.

    Returns (cards, sources) where sources is the list of real grounding
    citations Gemini actually used, as [{title, url}].
    """
    location_label = area_name or city
    categories_list = ", ".join(CARD_CATEGORIES)

    prompt = f"""Search Google for RECENT local news relevant to someone deciding whether to BUY a house or flat in {location_label}, {city}, India.

Focus your search on:
- New residential/commercial project launches, builder/developer activity, possession updates, RERA news
- New infrastructure or transit (roads, metro, flyovers) near or serving {location_label}
- Utilities and civic services (water, power, sanitation)
- Genuine safety/security developments (not routine crime reports)
- Schools, hospitals, connectivity, or major economic investment in the area

Prefer news specifically about {location_label}. Only include news about {city} generally
if it's a major development that would clearly matter city-wide to a buyer — and if so,
prefix that title with "Citywide: ".

Discard crime, politics, celebrity, religious, or entertainment stories unless tied to
real estate/development. If nothing relevant and recent is found, return an empty list.

For each relevant story you find, assign it to exactly ONE category from this fixed list:
{categories_list}

Respond with ONLY this JSON object and nothing else (no markdown fences, no commentary):
{{
  "cards": [
    {{
      "category": "Transit & Commute",
      "title": "clear headline in your own words, 8-15 words",
      "date": "Mon YYYY or empty string if unknown",
      "bullets": ["1-2 factual points, 15-25 words each, your own words"],
      "why_helps": "one sentence, 15-25 words, on why this matters to a home buyer"
    }}
  ]
}}
"""

    try:
        response = gemini_client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                temperature=0.2,
            ),
        )

        raw = (response.text or "").strip()
        logger.info(f"[NEWS GROUNDING] Raw output: {raw[:300]}")
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.DOTALL).strip()
        match = re.search(r'\{.*\}', clean, re.DOTALL)
        if not match:
            logger.warning("[NEWS GROUNDING] Could not find JSON in Gemini output")
            return None, None

        raw_cards = json.loads(match.group()).get('cards', [])
        cards = []
        for i, c in enumerate(raw_cards):
            category = c.get('category') if c.get('category') in CARD_CATEGORIES else 'Commercial & Amenities'
            title = clean_text(c.get('title', ''))
            bullets = [clean_text(b) for b in c.get('bullets', []) if b and clean_text(b)]
            why_helps = clean_text(c.get('why_helps', ''))
            if not title or not bullets:
                continue
            cards.append({
                'id': f'card-{i}',
                'category': category,
                'title': title,
                'date': c.get('date', ''),
                'bullets': bullets,
                'why_helps': why_helps,
            })

        # Pull the real grounding source links Gemini actually searched and
        # used — these are live Google Search citations, not scraped data.
        sources = []
        try:
            candidate = response.candidates[0]
            grounding = getattr(candidate, 'grounding_metadata', None)
            chunks = getattr(grounding, 'grounding_chunks', None) or []
            for chunk in chunks:
                web = getattr(chunk, 'web', None)
                if web and getattr(web, 'uri', None):
                    sources.append({
                        'title': getattr(web, 'title', '') or '',
                        'url': web.uri,
                    })
        except Exception as e:
            logger.debug(f"[NEWS GROUNDING] Could not extract grounding sources: {e}")

        return cards, sources

    except Exception as e:
        logger.error(f"[NEWS GROUNDING ERROR] {e}")
        return None, None


def build_categories_summary(cards):
    """Turn a flat card list into [{name, count}] for the filter pills."""
    counts = {}
    for c in cards:
        counts[c['category']] = counts.get(c['category'], 0) + 1
    return [{'name': name, 'count': count} for name, count in counts.items()]


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
                cards = cached.get('cards') or []
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
                    'cards': cards,
                    'categories': build_categories_summary(cards),
                    'articles': cached.get('articles') or [],
                    'cached': True
                }), 200

        # ── Cache miss or stale — fetch fresh via Gemini grounding ──
        location = zip_to_location(zip_code, locality_hint)
        if not location or not location.get('city'):
            return jsonify({'error': 'Could not resolve zip code to a location'}), 404

        cards, sources = fetch_grounded_cards(location['area_name'], location['city'])

        if cards is None:
            logger.warning(
                f"[AREA NEWS] Grounded fetch failed for zip={zip_code} "
                f"locality_hint={locality_hint!r} — not caching"
            )
            return jsonify({
                'error': 'Could not fetch local news right now. Please try again shortly.'
            }), 503

        logger.info(
            f"[AREA NEWS] zip={zip_code} locality_hint={locality_hint!r} "
            f"resolved_area='{location['area_name']}' "
            f"cards={len(cards)} sources={len(sources)}"
        )

        supabase.table('area_news_cache').upsert({
            'zip_code': cache_key,
            'area_name': location['area_name'],
            'city': location['city'],
            'formatted_address': location['formatted_address'],
            'lat': location['lat'],
            'lng': location['lng'],
            'cards': cards,
            'articles': sources,
            'fetched_at': datetime.now(timezone.utc).isoformat()
        }, on_conflict='zip_code').execute()

        return jsonify({
            'success': True,
            'zip_code': zip_code,
            'location': location,
            'cards': cards,
            'categories': build_categories_summary(cards),
            'articles': sources,
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
        'source': 'Gemini + Google Search grounding',
        'endpoints': [
            'GET /api/news/area?zip_code=110001 — fetch and summarize local news for a zip code'
        ]
    }), 200