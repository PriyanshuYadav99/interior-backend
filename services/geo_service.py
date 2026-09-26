import os
import logging
import googlemaps

logger = logging.getLogger(__name__)

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None


def reverse_geocode(lat, lng):
    """Best-effort human-readable name for a lat/lng pair."""
    if not gmaps:
        return None
    try:
        results = gmaps.reverse_geocode((lat, lng))
        if results:
            return results[0].get('formatted_address')
    except Exception as e:
        logger.error(f"[REVERSE_GEOCODE] {e}")
    return None