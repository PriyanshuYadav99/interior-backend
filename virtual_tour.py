

"""
Virtual Tour Module - Enhanced Version
Provides nearby places search and directions using Google Maps/Places API
"""

from flask import Blueprint, request, jsonify
import os
import logging
import googlemaps
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None

DEFAULT_SEARCH_RADIUS = 5000

APARTMENT_COORDINATES = {
    'lat': 15.5080647,
    'lng': 73.7719139,
    'name': 'RIO ROYALE'
}

CATEGORY_MAPPING = {
    'dining': ['restaurant', 'cafe', 'bakery', 'meal_takeaway', 'meal_delivery'],
    'education': ['school', 'university', 'library', 'secondary_school', 'primary_school'],
    'nature': ['park', 'campground', 'rv_park', 'tourist_attraction'],
    'health': ['hospital', 'pharmacy', 'doctor', 'dentist', 'physiotherapist', 'health'],
    'transport': ['transit_station', 'bus_station', 'subway_station', 'train_station', 'airport'],
    'shop': ['shopping_mall', 'supermarket', 'grocery_or_supermarket', 'convenience_store', 'store'],
    'gym': ['gym', 'stadium', 'spa']
}

virtual_tour_bp = Blueprint('virtual_tour', __name__, url_prefix='/api/virtual-tour')

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def calculate_distance(coord1, coord2):
    R = 6371.0
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def geocode_address(address):
    try:
        if not gmaps:
            return None
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            coordinates = (location['lat'], location['lng'])
            formatted_address = geocode_result[0].get('formatted_address', address)
            return {
                'coordinates': coordinates,
                'formatted_address': formatted_address,
                'place_name': geocode_result[0].get('address_components', [{}])[0].get('long_name', address)
            }
        return None
    except Exception as e:
        logger.error(f"[GEOCODE ERROR] {str(e)}")
        return None


def search_nearby_places(location, place_types, radius=DEFAULT_SEARCH_RADIUS):
    try:
        if not gmaps:
            return []

        all_places = []
        seen_place_ids = set()

        for place_type in place_types:
            places_result = gmaps.places_nearby(
                location=location,
                radius=radius,
                type=place_type
            )
            results = places_result.get('results', [])
            for place in results:
                place_id = place['place_id']
                if place_id in seen_place_ids:
                    continue
                seen_place_ids.add(place_id)
                photo_url = None
                if place.get('photos'):
                    photo_reference = place['photos'][0]['photo_reference']
                    photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"
                all_places.append({
                    'place_id': place_id,
                    'name': place['name'],
                    'address': place.get('vicinity', ''),
                    'lat': place['geometry']['location']['lat'],
                    'lng': place['geometry']['location']['lng'],
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total', 0),
                    'types': place.get('types', []),
                    'photo_url': photo_url,
                    'is_open': place.get('opening_hours', {}).get('open_now')
                })

        return all_places

    except Exception as e:
        logger.error(f"[PLACES SEARCH ERROR] {str(e)}")
        return []


def search_places_by_keyword(keyword, location, radius=DEFAULT_SEARCH_RADIUS):
    """
    Search for places near apartment using a keyword (e.g. 'Indian restaurant', 'Starbucks')
    Returns top matching places sorted by distance
    """
    try:
        if not gmaps:
            return []

        logger.info(f"[KEYWORD SEARCH] Searching for '{keyword}' near {location}")

        results = gmaps.places_nearby(
            location=location,
            radius=radius,
            keyword=keyword
        )

        places = results.get('results', [])
        logger.info(f"[KEYWORD SEARCH] Found {len(places)} results for '{keyword}'")

        formatted = []
        apartment_coords = (APARTMENT_COORDINATES['lat'], APARTMENT_COORDINATES['lng'])

        for place in places:
            place_id = place['place_id']
            photo_url = None
            if place.get('photos'):
                photo_reference = place['photos'][0]['photo_reference']
                photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"

            place_coords = (
                place['geometry']['location']['lat'],
                place['geometry']['location']['lng']
            )
            distance = calculate_distance(apartment_coords, place_coords)

            formatted.append({
                'id': place_id,
                'name': place['name'],
                'address': place.get('vicinity', ''),
                'rating': place.get('rating', 0),
                'user_ratings_total': place.get('user_ratings_total', 0),
                'distance': round(distance, 2),
                'coordinates': {
                    'lat': place_coords[0],
                    'lng': place_coords[1]
                },
                'photo_url': photo_url,
                'types': place.get('types', []),
                'is_open': place.get('opening_hours', {}).get('open_now'),
                'is_custom': False
            })

        # Sort by distance
        formatted.sort(key=lambda x: x['distance'])
        return formatted

    except Exception as e:
        logger.error(f"[KEYWORD SEARCH ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return []


def get_directions(origin, destination, mode='driving'):
    try:
        if not gmaps:
            return None
        directions_result = gmaps.directions(
            origin=origin,
            destination=destination,
            mode=mode,
            departure_time=datetime.now()
        )
        if not directions_result:
            return None
        route = directions_result[0]
        leg = route['legs'][0]
        return {
            'distance': {
                'text': leg['distance']['text'],
                'value': leg['distance']['value']
            },
            'duration': {
                'text': leg['duration']['text'],
                'value': leg['duration']['value']
            },
            'start_address': leg['start_address'],
            'end_address': leg['end_address'],
            'steps': [
                {
                    'instruction': step['html_instructions'],
                    'distance': step['distance']['text'],
                    'duration': step['duration']['text']
                }
                for step in leg['steps']
            ],
            'polyline': route['overview_polyline']['points']
        }
    except Exception as e:
        logger.error(f"[DIRECTIONS ERROR] {str(e)}")
        return None


def get_place_details(place_id):
    try:
        if not gmaps:
            return None
        place_details = gmaps.place(place_id)
        if not place_details or 'result' not in place_details:
            return None
        result = place_details['result']
        photos = []
        if result.get('photos'):
            for photo in result['photos'][:5]:
                photo_reference = photo['photo_reference']
                photos.append(
                    f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"
                )
        return {
            'place_id': result['place_id'],
            'name': result['name'],
            'address': result.get('formatted_address', ''),
            'phone': result.get('formatted_phone_number'),
            'website': result.get('website'),
            'rating': result.get('rating'),
            'user_ratings_total': result.get('user_ratings_total', 0),
            'price_level': result.get('price_level'),
            'opening_hours': result.get('opening_hours', {}).get('weekday_text', []),
            'reviews': [
                {
                    'author': review['author_name'],
                    'rating': review['rating'],
                    'text': review['text'],
                    'time': review['relative_time_description']
                }
                for review in result.get('reviews', [])[:3]
            ],
            'photos': photos,
            'types': result.get('types', [])
        }
    except Exception as e:
        logger.error(f"[PLACE DETAILS ERROR] {str(e)}")
        return None


# ============================================================
# ROUTES
# ============================================================

@virtual_tour_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'module': 'virtual_tour',
        'version': '2.0.0',
        'google_maps_configured': bool(gmaps),
        'default_radius_km': DEFAULT_SEARCH_RADIUS / 1000,
        'available_categories': list(CATEGORY_MAPPING.keys()),
        'apartment': APARTMENT_COORDINATES
    }), 200


@virtual_tour_bp.route('/search', methods=['POST'])
def search_nearby():
    """
    Three modes of search:

    MODE 1: Category-based search (is_custom_search = False, no keyword)
    - Search for category places near apartment

    MODE 2: Keyword search (is_keyword_search = True)
    - Search for specific keyword near apartment (e.g. 'Indian restaurant', 'Starbucks')
    - Returns multiple matching places sorted by distance

    MODE 3: Custom location search (is_custom_search = True)
    - Geocode a custom address and return distance from apartment

    Request Body:
    {
        "location": "address or lat,lng string",
        "category": "dining|education|...",
        "radius": 5000,
        "is_custom_search": true/false,
        "is_keyword_search": true/false,
        "keyword": "Indian restaurant"
    }
    """
    try:
        if not gmaps:
            return jsonify({
                'error': 'Google Maps API not configured',
                'details': 'GOOGLE_MAPS_API_KEY environment variable not set'
            }), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        location = data.get('location')
        category = data.get('category', 'dining')
        radius = data.get('radius', DEFAULT_SEARCH_RADIUS)
        is_custom_search = data.get('is_custom_search', False)
        is_keyword_search = data.get('is_keyword_search', False)
        keyword = data.get('keyword', '').strip()

        if not location:
            return jsonify({'error': 'Location is required'}), 400

        apartment_coords = (APARTMENT_COORDINATES['lat'], APARTMENT_COORDINATES['lng'])

        # ✅ MODE 2: KEYWORD SEARCH
        if is_keyword_search and keyword:
            logger.info(f"[SEARCH] 🔍 Keyword search mode: '{keyword}'")

            places = search_places_by_keyword(keyword, apartment_coords, radius)

            if not places:
                return jsonify({
                    'success': True,
                    'mode': 'keyword_search',
                    'keyword': keyword,
                    'places': [],
                    'count': 0,
                    'message': f'No results found for "{keyword}" within {radius/1000}km'
                }), 200

            return jsonify({
                'success': True,
                'mode': 'keyword_search',
                'keyword': keyword,
                'origin': {
                    'lat': apartment_coords[0],
                    'lng': apartment_coords[1],
                    'name': APARTMENT_COORDINATES['name']
                },
                'places': places,
                'count': len(places),
                'radius_km': radius / 1000
            }), 200

        # ✅ MODE 3: CUSTOM LOCATION SEARCH
        elif is_custom_search:
            logger.info("[SEARCH] 📍 Custom location mode")

            geocode_result = geocode_address(location)
            if not geocode_result:
                return jsonify({
                    'error': 'Could not find location',
                    'location_provided': location,
                    'suggestion': 'Try a more specific address (e.g., "Burj Khalifa, Dubai")'
                }), 400

            custom_coords = geocode_result['coordinates']
            place_name = geocode_result['place_name']
            formatted_address = geocode_result['formatted_address']
            distance = calculate_distance(apartment_coords, custom_coords)

            return jsonify({
                'success': True,
                'mode': 'custom_location',
                'origin': {
                    'lat': APARTMENT_COORDINATES['lat'],
                    'lng': APARTMENT_COORDINATES['lng'],
                    'name': APARTMENT_COORDINATES['name']
                },
                'places': [
                    {
                        'id': f"custom_{custom_coords[0]}_{custom_coords[1]}",
                        'name': place_name,
                        'address': formatted_address,
                        'rating': 0,
                        'user_ratings_total': 0,
                        'distance': round(distance, 2),
                        'coordinates': {
                            'lat': custom_coords[0],
                            'lng': custom_coords[1]
                        },
                        'photo_url': '',
                        'types': ['custom_location'],
                        'is_open': None,
                        'is_custom': True
                    }
                ],
                'count': 1,
                'message': f'{place_name} is {round(distance, 2)}km from {APARTMENT_COORDINATES["name"]}'
            }), 200

        # ✅ MODE 1: CATEGORY-BASED SEARCH
        else:
            logger.info(f"[SEARCH] 📂 Category mode: {category}")

            place_types = CATEGORY_MAPPING.get(category.lower(), ['restaurant'])
            places = search_nearby_places(
                location=apartment_coords,
                place_types=place_types,
                radius=radius
            )

            if not places:
                return jsonify({
                    'success': True,
                    'mode': 'category_search',
                    'origin': {
                        'lat': apartment_coords[0],
                        'lng': apartment_coords[1],
                        'name': APARTMENT_COORDINATES['name']
                    },
                    'category': category,
                    'places': [],
                    'count': 0,
                    'radius_km': radius / 1000,
                    'message': f'No {category} places found within {radius/1000}km'
                }), 200

            formatted_places = []
            for place in places:
                place_coords = (place['lat'], place['lng'])
                distance = calculate_distance(apartment_coords, place_coords)
                formatted_places.append({
                    'id': place['place_id'],
                    'name': place['name'],
                    'address': place.get('address', ''),
                    'rating': place.get('rating', 0),
                    'user_ratings_total': place.get('user_ratings_total', 0),
                    'distance': round(distance, 2),
                    'coordinates': {
                        'lat': place['lat'],
                        'lng': place['lng']
                    },
                    'photo_url': place.get('photo_url', ''),
                    'types': place.get('types', []),
                    'is_open': place.get('is_open', None),
                    'is_custom': False
                })

            formatted_places.sort(key=lambda x: x['distance'])

            return jsonify({
                'success': True,
                'mode': 'category_search',
                'origin': {
                    'lat': apartment_coords[0],
                    'lng': apartment_coords[1],
                    'name': APARTMENT_COORDINATES['name']
                },
                'category': category,
                'places': formatted_places,
                'count': len(formatted_places),
                'radius_km': radius / 1000
            }), 200

    except Exception as e:
        logger.error(f"[SEARCH ERROR] ❌ {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@virtual_tour_bp.route('/directions', methods=['POST'])
def directions():
    try:
        if not gmaps:
            return jsonify({'error': 'Google Maps API not configured'}), 500
        data = request.get_json()
        origin = data.get('origin')
        destination = data.get('destination')
        mode = data.get('mode', 'driving')
        if not origin or not destination:
            return jsonify({'error': 'Origin and destination are required'}), 400
        directions_data = get_directions(origin, destination, mode)
        if not directions_data:
            return jsonify({'error': 'Unable to get directions'}), 404
        return jsonify({
            'success': True,
            'directions': directions_data
        }), 200
    except Exception as e:
        logger.error(f"[DIRECTIONS ERROR] {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@virtual_tour_bp.route('/place-details/<place_id>', methods=['GET'])
def place_details(place_id):
    try:
        if not gmaps:
            return jsonify({'error': 'Google Maps API not configured'}), 500
        details = get_place_details(place_id)
        if not details:
            return jsonify({'error': 'Place not found'}), 404
        return jsonify({
            'success': True,
            'place': details
        }), 200
    except Exception as e:
        logger.error(f"[PLACE DETAILS ERROR] {str(e)}")
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500