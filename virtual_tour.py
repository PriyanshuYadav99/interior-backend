# """
# Virtual Tour Module - Single File Version
# Provides nearby places search and directions using Google Maps/Places API
# """

# from flask import Blueprint, request, jsonify
# import os
# import logging
# import googlemaps
# from math import radians, sin, cos, sqrt, atan2
# from datetime import datetime

# logger = logging.getLogger(__name__)

# # ============================================================
# # CONFIGURATION
# # ============================================================

# # Initialize Google Maps client
# GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
# gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None

# # Category mapping
# CATEGORY_MAPPING = {
#     'dining': ['restaurant', 'cafe', 'food'],
#     'education': ['school', 'university', 'library'],
#     'nature': ['park', 'garden', 'natural_feature'],
#     'health': ['hospital', 'pharmacy', 'doctor', 'clinic'],
#     'transit': ['transit_station', 'bus_station', 'subway_station'],
#     'shop': ['shopping_mall', 'store', 'supermarket'],
#     'gym': ['gym', 'fitness_center', 'sports_complex']
# }

# # ============================================================
# # CREATE BLUEPRINT
# # ============================================================

# virtual_tour_bp = Blueprint('virtual_tour', __name__, url_prefix='/api/virtual-tour')

# # ============================================================
# # UTILITY FUNCTIONS
# # ============================================================

# def calculate_distance(coord1, coord2):
#     """
#     Calculate distance between two coordinates using Haversine formula
#     coord1, coord2: tuples of (lat, lng)
#     Returns: distance in kilometers
#     """
#     # Earth's radius in kilometers
#     R = 6371.0
    
#     lat1, lon1 = radians(coord1[0]), radians(coord1[1])
#     lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    
#     dlat = lat2 - lat1
#     dlon = lon2 - lon1
    
#     a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
#     c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
#     distance = R * c
    
#     return distance


# def geocode_address(address):
#     """
#     Convert address to coordinates (lat, lng)
#     """
#     try:
#         if not gmaps:
#             return None
            
#         geocode_result = gmaps.geocode(address)
#         if geocode_result:
#             location = geocode_result[0]['geometry']['location']
#             return (location['lat'], location['lng'])
#         return None
#     except Exception as e:
#         logger.error(f"[GEOCODE ERROR] {str(e)}")
#         return None


# def search_nearby_places(location, place_types, radius=10000):
#     """
#     Search for nearby places of specific types
#     location: tuple (lat, lng)
#     place_types: list of place types
#     radius: search radius in meters (default 10km)
#     """
#     try:
#         if not gmaps:
#             return []
            
#         all_places = []
#         seen_place_ids = set()
        
#         for place_type in place_types:
#             places_result = gmaps.places_nearby(
#                 location=location,
#                 radius=radius,
#                 type=place_type
#             )
            
#             for place in places_result.get('results', []):
#                 place_id = place['place_id']
                
#                 # Avoid duplicates
#                 if place_id in seen_place_ids:
#                     continue
#                 seen_place_ids.add(place_id)
                
#                 # Get photo URL if available
#                 photo_url = None
#                 if place.get('photos'):
#                     photo_reference = place['photos'][0]['photo_reference']
#                     photo_url = f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=400&photo_reference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"
                
#                 all_places.append({
#                     'place_id': place_id,
#                     'name': place['name'],
#                     'address': place.get('vicinity', ''),
#                     'lat': place['geometry']['location']['lat'],
#                     'lng': place['geometry']['location']['lng'],
#                     'rating': place.get('rating'),
#                     'user_ratings_total': place.get('user_ratings_total', 0),
#                     'types': place.get('types', []),
#                     'photo_url': photo_url,
#                     'is_open': place.get('opening_hours', {}).get('open_now')
#                 })
        
#         return all_places
        
#     except Exception as e:
#         logger.error(f"[PLACES SEARCH ERROR] {str(e)}")
#         return []


# def get_directions(origin, destination, mode='driving'):
#     """
#     Get directions between two points
#     mode: driving, walking, transit, bicycling
#     """
#     try:
#         if not gmaps:
#             return None
            
#         directions_result = gmaps.directions(
#             origin=origin,
#             destination=destination,
#             mode=mode,
#             departure_time=datetime.now()
#         )
        
#         if not directions_result:
#             return None
        
#         route = directions_result[0]
#         leg = route['legs'][0]
        
#         return {
#             'distance': {
#                 'text': leg['distance']['text'],
#                 'value': leg['distance']['value']  # in meters
#             },
#             'duration': {
#                 'text': leg['duration']['text'],
#                 'value': leg['duration']['value']  # in seconds
#             },
#             'start_address': leg['start_address'],
#             'end_address': leg['end_address'],
#             'steps': [
#                 {
#                     'instruction': step['html_instructions'],
#                     'distance': step['distance']['text'],
#                     'duration': step['duration']['text']
#                 }
#                 for step in leg['steps']
#             ],
#             'polyline': route['overview_polyline']['points']
#         }
        
#     except Exception as e:
#         logger.error(f"[DIRECTIONS ERROR] {str(e)}")
#         return None


# def get_place_details(place_id):
#     """
#     Get detailed information about a specific place
#     """
#     try:
#         if not gmaps:
#             return None
            
#         place_details = gmaps.place(place_id)
        
#         if not place_details or 'result' not in place_details:
#             return None
        
#         result = place_details['result']
        
#         # Get photos
#         photos = []
#         if result.get('photos'):
#             for photo in result['photos'][:5]:  # Get up to 5 photos
#                 photo_reference = photo['photo_reference']
#                 photos.append(
#                     f"https://maps.googleapis.com/maps/api/place/photo?maxwidth=800&photo_reference={photo_reference}&key={GOOGLE_MAPS_API_KEY}"
#                 )
        
#         return {
#             'place_id': result['place_id'],
#             'name': result['name'],
#             'address': result.get('formatted_address', ''),
#             'phone': result.get('formatted_phone_number'),
#             'website': result.get('website'),
#             'rating': result.get('rating'),
#             'user_ratings_total': result.get('user_ratings_total', 0),
#             'price_level': result.get('price_level'),
#             'opening_hours': result.get('opening_hours', {}).get('weekday_text', []),
#             'reviews': [
#                 {
#                     'author': review['author_name'],
#                     'rating': review['rating'],
#                     'text': review['text'],
#                     'time': review['relative_time_description']
#                 }
#                 for review in result.get('reviews', [])[:3]  # Get top 3 reviews
#             ],
#             'photos': photos,
#             'types': result.get('types', [])
#         }
        
#     except Exception as e:
#         logger.error(f"[PLACE DETAILS ERROR] {str(e)}")
#         return None


# # ============================================================
# # ROUTES
# # ============================================================

# @virtual_tour_bp.route('/health', methods=['GET'])
# def health():
#     """Health check for virtual tour"""
#     return jsonify({
#         'status': 'healthy',
#         'module': 'virtual_tour',
#         'version': '1.0.0',
#         'google_maps_configured': bool(gmaps)
#     }), 200


# @virtual_tour_bp.route('/search', methods=['POST'])
# def search_nearby():
#     """
#     Search for nearby places based on location and category
    
#     Request Body:
#     {
#         "location": "address or lat,lng",
#         "category": "dining|education|nature|health|transit|shop|gym",
#         "radius": 10000 (optional, default 10km in meters)
#     }
#     """
#     try:
#         if not gmaps:
#             return jsonify({
#                 'error': 'Google Maps API not configured',
#                 'details': 'GOOGLE_MAPS_API_KEY environment variable not set'
#             }), 500
        
#         data = request.get_json()
        
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400
        
#         location = data.get('location')
#         category = data.get('category', 'dining')
#         radius = data.get('radius', 10000)  # 10km in meters
        
#         if not location:
#             return jsonify({'error': 'Location is required'}), 400
        
#         logger.info(f"[VIRTUAL TOUR] Searching for {category} near: {location}")
        
#         # Get coordinates from address if needed
#         coordinates = geocode_address(location)
#         if not coordinates:
#             return jsonify({'error': 'Invalid location or unable to geocode'}), 400
        
#         # Get place types for the category
#         place_types = CATEGORY_MAPPING.get(category.lower(), ['restaurant'])
        
#         # Search for places
#         places = search_nearby_places(
#             location=coordinates,
#             place_types=place_types,
#             radius=radius
#         )
        
#         # Calculate distances and format response
#         formatted_places = []
#         for place in places:
#             place_coords = (place['lat'], place['lng'])
#             distance = calculate_distance(coordinates, place_coords)
            
#             formatted_places.append({
#                 'id': place['place_id'],
#                 'name': place['name'],
#                 'address': place.get('address', ''),
#                 'rating': place.get('rating', 0),
#                 'distance': round(distance, 2),
#                 'coordinates': {
#                     'lat': place['lat'],
#                     'lng': place['lng']
#                 },
#                 'photo_url': place.get('photo_url', ''),
#                 'types': place.get('types', []),
#                 'is_open': place.get('is_open', None)
#             })
        
#         # Sort by distance
#         formatted_places.sort(key=lambda x: x['distance'])
        
#         logger.info(f"[VIRTUAL TOUR] ✅ Found {len(formatted_places)} places")
        
#         return jsonify({
#             'success': True,
#             'origin': {
#                 'lat': coordinates[0],
#                 'lng': coordinates[1]
#             },
#             'category': category,
#             'places': formatted_places,
#             'count': len(formatted_places)
#         }), 200
        
#     except Exception as e:
#         logger.error(f"[VIRTUAL TOUR ERROR] {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             'error': 'Internal server error',
#             'details': str(e)
#         }), 500


# @virtual_tour_bp.route('/directions', methods=['POST'])
# def directions():
#     """
#     Get directions between origin and destination
    
#     Request Body:
#     {
#         "origin": "lat,lng",
#         "destination": "lat,lng",
#         "mode": "driving|walking|transit|bicycling" (optional, default: driving)
#     }
#     """
#     try:
#         if not gmaps:
#             return jsonify({
#                 'error': 'Google Maps API not configured'
#             }), 500
        
#         data = request.get_json()
#         origin = data.get('origin')
#         destination = data.get('destination')
#         mode = data.get('mode', 'driving')
        
#         if not origin or not destination:
#             return jsonify({'error': 'Origin and destination are required'}), 400
        
#         logger.info(f"[DIRECTIONS] Getting {mode} directions from {origin} to {destination}")
        
#         directions_data = get_directions(origin, destination, mode)
        
#         if not directions_data:
#             return jsonify({'error': 'Unable to get directions'}), 404
        
#         return jsonify({
#             'success': True,
#             'directions': directions_data
#         }), 200
        
#     except Exception as e:
#         logger.error(f"[DIRECTIONS ERROR] {str(e)}")
#         return jsonify({
#             'error': 'Internal server error',
#             'details': str(e)
#         }), 500


# @virtual_tour_bp.route('/place-details/<place_id>', methods=['GET'])
# def place_details(place_id):
#     """
#     Get detailed information about a specific place
    
#     Parameters:
#         place_id: Google Places ID
#     """
#     try:
#         if not gmaps:
#             return jsonify({
#                 'error': 'Google Maps API not configured'
#             }), 500
        
#         logger.info(f"[PLACE DETAILS] Getting details for place: {place_id}")
        
#         details = get_place_details(place_id)
        
#         if not details:
#             return jsonify({'error': 'Place not found'}), 404
        
#         return jsonify({
#             'success': True,
#             'place': details
#         }), 200
        
#     except Exception as e:
#         logger.error(f"[PLACE DETAILS ERROR] {str(e)}")
#         return jsonify({
#             'error': 'Internal server error',
#             'details': str(e)
#         }), 500

"""
Virtual Tour Module - Single File Version
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

# Initialize Google Maps client
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None

# ✅ Default search radius: 5km (5000 meters)
DEFAULT_SEARCH_RADIUS = 5000

# Category mapping
CATEGORY_MAPPING = {
    'dining': ['restaurant', 'cafe', 'food'],
    'education': ['school', 'university', 'library'],
    'nature': ['park', 'garden', 'natural_feature'],
    'health': ['hospital', 'pharmacy', 'doctor', 'clinic'],
    'transport': ['transit_station', 'bus_station', 'subway_station'],
    'shop': ['shopping_mall', 'store', 'supermarket'],
    'gym': ['gym', 'fitness_center', 'sports_complex']
}

# ============================================================
# CREATE BLUEPRINT
# ============================================================

virtual_tour_bp = Blueprint('virtual_tour', __name__, url_prefix='/api/virtual-tour')

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def calculate_distance(coord1, coord2):
    """
    Calculate distance between two coordinates using Haversine formula
    coord1, coord2: tuples of (lat, lng)
    Returns: distance in kilometers
    """
    # Earth's radius in kilometers
    R = 6371.0
    
    lat1, lon1 = radians(coord1[0]), radians(coord1[1])
    lat2, lon2 = radians(coord2[0]), radians(coord2[1])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    distance = R * c
    
    return distance


def geocode_address(address):
    """
    Convert address to coordinates (lat, lng)
    """
    try:
        if not gmaps:
            return None
            
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            return (location['lat'], location['lng'])
        return None
    except Exception as e:
        logger.error(f"[GEOCODE ERROR] {str(e)}")
        return None


def search_nearby_places(location, place_types, radius=DEFAULT_SEARCH_RADIUS):
    """
    Search for nearby places of specific types
    location: tuple (lat, lng)
    place_types: list of place types
    radius: search radius in meters (default 5km)
    """
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
            
            for place in places_result.get('results', []):
                place_id = place['place_id']
                
                # Avoid duplicates
                if place_id in seen_place_ids:
                    continue
                seen_place_ids.add(place_id)
                
                # Get photo URL if available
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


def get_directions(origin, destination, mode='driving'):
    """
    Get directions between two points
    mode: driving, walking, transit, bicycling
    """
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
                'value': leg['distance']['value']  # in meters
            },
            'duration': {
                'text': leg['duration']['text'],
                'value': leg['duration']['value']  # in seconds
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
    """
    Get detailed information about a specific place
    """
    try:
        if not gmaps:
            return None
            
        place_details = gmaps.place(place_id)
        
        if not place_details or 'result' not in place_details:
            return None
        
        result = place_details['result']
        
        # Get photos
        photos = []
        if result.get('photos'):
            for photo in result['photos'][:5]:  # Get up to 5 photos
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
                for review in result.get('reviews', [])[:3]  # Get top 3 reviews
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
    """Health check for virtual tour"""
    return jsonify({
        'status': 'healthy',
        'module': 'virtual_tour',
        'version': '1.0.0',
        'google_maps_configured': bool(gmaps),
        'default_radius_km': DEFAULT_SEARCH_RADIUS / 1000
    }), 200


@virtual_tour_bp.route('/search', methods=['POST'])
def search_nearby():
    """
    Search for nearby places based on location and category
    
    Request Body:
    {
        "location": "address or lat,lng",
        "category": "dining|education|nature|health|transit|shop|gym",
        "radius": 5000 (optional, default 5km in meters)
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
        radius = data.get('radius', DEFAULT_SEARCH_RADIUS)  # Default 5km
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        logger.info(f"[VIRTUAL TOUR] Searching for {category} near: {location} (radius: {radius}m)")
        
        # Get coordinates from address if needed
        coordinates = geocode_address(location)
        if not coordinates:
            return jsonify({'error': 'Invalid location or unable to geocode'}), 400
        
        # Get place types for the category
        place_types = CATEGORY_MAPPING.get(category.lower(), ['restaurant'])
        
        # Search for places
        places = search_nearby_places(
            location=coordinates,
            place_types=place_types,
            radius=radius
        )
        
        # Calculate distances and format response
        formatted_places = []
        for place in places:
            place_coords = (place['lat'], place['lng'])
            distance = calculate_distance(coordinates, place_coords)
            
            formatted_places.append({
                'id': place['place_id'],
                'name': place['name'],
                'address': place.get('address', ''),
                'rating': place.get('rating', 0),
                'distance': round(distance, 2),
                'coordinates': {
                    'lat': place['lat'],
                    'lng': place['lng']
                },
                'photo_url': place.get('photo_url', ''),
                'types': place.get('types', []),
                'is_open': place.get('is_open', None)
            })
        
        # Sort by distance
        formatted_places.sort(key=lambda x: x['distance'])
        
        logger.info(f"[VIRTUAL TOUR] ✅ Found {len(formatted_places)} places within {radius/1000}km")
        
        return jsonify({
            'success': True,
            'origin': {
                'lat': coordinates[0],
                'lng': coordinates[1]
            },
            'category': category,
            'places': formatted_places,
            'count': len(formatted_places),
            'radius_km': radius / 1000
        }), 200
        
    except Exception as e:
        logger.error(f"[VIRTUAL TOUR ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@virtual_tour_bp.route('/directions', methods=['POST'])
def directions():
    """
    Get directions between origin and destination
    
    Request Body:
    {
        "origin": "lat,lng",
        "destination": "lat,lng",
        "mode": "driving|walking|transit|bicycling" (optional, default: driving)
    }
    """
    try:
        if not gmaps:
            return jsonify({
                'error': 'Google Maps API not configured'
            }), 500
        
        data = request.get_json()
        origin = data.get('origin')
        destination = data.get('destination')
        mode = data.get('mode', 'driving')
        
        if not origin or not destination:
            return jsonify({'error': 'Origin and destination are required'}), 400
        
        logger.info(f"[DIRECTIONS] Getting {mode} directions from {origin} to {destination}")
        
        directions_data = get_directions(origin, destination, mode)
        
        if not directions_data:
            return jsonify({'error': 'Unable to get directions'}), 404
        
        return jsonify({
            'success': True,
            'directions': directions_data
        }), 200
        
    except Exception as e:
        logger.error(f"[DIRECTIONS ERROR] {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@virtual_tour_bp.route('/place-details/<place_id>', methods=['GET'])
def place_details(place_id):
    """
    Get detailed information about a specific place
    
    Parameters:
        place_id: Google Places ID
    """
    try:
        if not gmaps:
            return jsonify({
                'error': 'Google Maps API not configured'
            }), 500
        
        logger.info(f"[PLACE DETAILS] Getting details for place: {place_id}")
        
        details = get_place_details(place_id)
        
        if not details:
            return jsonify({'error': 'Place not found'}), 404
        
        return jsonify({
            'success': True,
            'place': details
        }), 200
        
    except Exception as e:
        logger.error(f"[PLACE DETAILS ERROR] {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500