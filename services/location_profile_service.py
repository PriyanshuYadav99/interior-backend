"""
Builds a localized "profile" for a lat/lng — currency, climate, transit
names, emergency number — used to fill in the Life Echo prompt template
instead of hardcoded Canadian/Indian values. Runs once per location, at
registration time, and gets cached in client_locations.config.
"""

import os
import json
import logging
from groq import Groq
from services.geo_service import gmaps

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv('GROQ_API_KEY')
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

FALLBACK_PROFILE = {
    'currency_code': 'USD',
    'currency_symbol': '$',
    'climate_note': 'a typical regional climate',
    'transport_examples': ['local transit', 'taxi', 'private vehicle'],
    'emergency_number': 'local emergency services',
    'landmark_context': 'the surrounding neighborhood',
}


def _reverse_geocode_components(lat, lng):
    """Pull country/city out of a Maps reverse-geocode call."""
    if not gmaps:
        return {}
    try:
        results = gmaps.reverse_geocode((lat, lng))
        if not results:
            return {}
        components = results[0].get('address_components', [])
        out = {}
        for c in components:
            types = c.get('types', [])
            if 'country' in types:
                out['country'] = c['long_name']
                out['country_code'] = c['short_name']
            if 'locality' in types or 'administrative_area_level_1' in types:
                out.setdefault('city', c['long_name'])
        out['formatted_address'] = results[0].get('formatted_address')
        return out
    except Exception as e:
        logger.error(f"[GEO_COMPONENTS] {e}")
        return {}


def build_location_profile(lat, lng):
    """
    One-time profile generation for a new location. Returns a dict that
    gets merged into client_locations.config and reused for every Life
    Echo prompt for that client from then on — no repeated API calls.
    """
    geo = _reverse_geocode_components(lat, lng)
    country = geo.get('country', 'Unknown')
    city = geo.get('city') or geo.get('formatted_address', 'Unknown')

    profile = {
        'country': country,
        'city': city,
        'formatted_address': geo.get('formatted_address'),
    }

    if not groq_client:
        logger.warning('[LOCATION_PROFILE] GROQ_API_KEY not set, using fallback profile')
        profile.update(FALLBACK_PROFILE)
        return profile

    prompt = f"""Location: {city}, {country} (lat {lat}, lng {lng}).

Return ONLY a raw JSON object, no markdown fences, no commentary, with exactly these keys:
{{
  "currency_code": "3-letter ISO currency code actually used in this country, e.g. AED, INR, CAD, USD",
  "currency_symbol": "the symbol/label people locally use for prices, e.g. AED, ₹, $",
  "climate_note": "one sentence describing this location's typical climate/weather pattern",
  "transport_examples": ["3 to 5 real local transport options or brand names used in this city"],
  "emergency_number": "the local emergency services phone number",
  "landmark_context": "a short phrase naming the general type of district/area"
}}"""

    try:
        completion = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a precise local-knowledge assistant. Reply with raw JSON only."},
                {"role": "user", "content": prompt},
            ],
            model="openai/gpt-oss-120b",
            temperature=0.2,
            max_tokens=400,
        )
        raw = completion.choices[0].message.content.strip()
        if raw.startswith('```'):
            raw = raw.strip('`')
            raw = raw.split('\n', 1)[1] if raw.lower().startswith('json') else raw
        data = json.loads(raw)
        profile.update(data)
        logger.info(f"[LOCATION_PROFILE] ✅ Built profile for {city}, {country}: {data.get('currency_code')}")
    except Exception as e:
        logger.error(f"[LOCATION_PROFILE] LLM profile generation failed, using fallback: {e}")
        profile.update(FALLBACK_PROFILE)

    return profile