"""
Location service — single source of truth for client → coordinates → profile.

Handles create-or-fetch for the client_locations table. On first creation
for a given lat/lng, it also triggers build_location_profile() to generate
the currency/climate/transport data used by scenario.py's Life Echo prompts.
Subsequent lookups are cheap reads — no repeated LLM calls.
"""

import logging
from services.external_clients import supabase
from services.geo_service import reverse_geocode
from services.location_profile_service import build_location_profile

logger = logging.getLogger(__name__)

COORD_PRECISION = 6  # ~0.11m at the equator — enough to treat "same pin" as a dupe


def _round(val):
    return round(float(val), COORD_PRECISION)


def get_or_create_location(lat, lng, client_name=None, name=None, config=None):
    """
    Look up a location by client_name (if given) or by lat/lng, and create
    it — including its Life Echo profile — if nothing matches.
    Returns (location_row, created_bool).
    """
    if not supabase:
        raise RuntimeError('Database not configured')

    lat, lng = _round(lat), _round(lng)

    # 1. Prefer client_name — lets a client's pin be nudged later without
    #    spawning a duplicate row.
    if client_name:
        existing = supabase.table('client_locations') \
            .select('*').eq('client_name', client_name).execute()
        if existing.data:
            logger.info(f"[LOCATION] Found existing location for client_name='{client_name}'")
            return existing.data[0], False

    # 2. Otherwise dedupe on the coordinate pair itself.
    existing = supabase.table('client_locations') \
        .select('*').eq('lat', lat).eq('lng', lng).execute()
    if existing.data:
        logger.info(f"[LOCATION] Found existing location for lat={lat}, lng={lng}")
        return existing.data[0], False

    # 3. Nothing found — create it, building the Life Echo profile once.
    resolved_name = name or reverse_geocode(lat, lng) or f"Location {lat},{lng}"

    logger.info(f"[LOCATION] Creating new location '{resolved_name}' for client_name='{client_name}'")
    profile = build_location_profile(lat, lng)
    merged_config = {**profile, **(config or {})}  # explicit config overrides the auto-built profile

    row = {
        'client_name': client_name,
        'lat': lat,
        'lng': lng,
        'location_name': resolved_name,
        'config': merged_config,
    }
    created = supabase.table('client_locations').insert(row).execute()
    if not created.data:
        raise RuntimeError('Failed to create location')

    logger.info(f"[LOCATION] ✅ Created with profile: currency={profile.get('currency_code')}, city={profile.get('city')}")
    return created.data[0], True


def get_location_by_client(client_name):
    """Read-only lookup — used by scenario.py and virtual_tour.py. No creation."""
    if not supabase:
        return None
    result = supabase.table('client_locations') \
        .select('*').eq('client_name', client_name).execute()
    return result.data[0] if result.data else None