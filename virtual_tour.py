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

# # ✅ Default search radius: 5km (5000 meters)
# DEFAULT_SEARCH_RADIUS = 5000

# # Category mapping
# CATEGORY_MAPPING = {
#     'dining': ['restaurant', 'cafe', 'food'],
#     'education': ['school', 'university', 'library'],
#     'nature': ['park', 'garden', 'natural_feature'],
#     'health': ['hospital', 'pharmacy', 'doctor', 'clinic'],
#     'transport': ['transit_station', 'bus_station', 'subway_station'],
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


# def search_nearby_places(location, place_types, radius=DEFAULT_SEARCH_RADIUS):
#     """
#     Search for nearby places of specific types
#     location: tuple (lat, lng)
#     place_types: list of place types
#     radius: search radius in meters (default 5km)
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
#         'google_maps_configured': bool(gmaps),
#         'default_radius_km': DEFAULT_SEARCH_RADIUS / 1000
#     }), 200


# @virtual_tour_bp.route('/search', methods=['POST'])
# def search_nearby():
#     """
#     Search for nearby places based on location and category
    
#     Request Body:
#     {
#         "location": "address or lat,lng",
#         "category": "dining|education|nature|health|transit|shop|gym",
#         "radius": 5000 (optional, default 5km in meters)
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
#         radius = data.get('radius', DEFAULT_SEARCH_RADIUS)  # Default 5km
        
#         if not location:
#             return jsonify({'error': 'Location is required'}), 400
        
#         logger.info(f"[VIRTUAL TOUR] Searching for {category} near: {location} (radius: {radius}m)")
        
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
        
#         logger.info(f"[VIRTUAL TOUR] ✅ Found {len(formatted_places)} places within {radius/1000}km")
        
#         return jsonify({
#             'success': True,
#             'origin': {
#                 'lat': coordinates[0],
#                 'lng': coordinates[1]
#             },
#             'category': category,
#             'places': formatted_places,
#             'count': len(formatted_places),
#             'radius_km': radius / 1000
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
# """
# Virtual Tour Module - Enhanced Version
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

# # ✅ Default search radius: 5km (5000 meters)
# DEFAULT_SEARCH_RADIUS = 5000

# # ✅ IMPROVED Category mapping with correct Google Places types
# CATEGORY_MAPPING = {
#     'dining': ['restaurant', 'cafe', 'bakery', 'meal_takeaway', 'meal_delivery'],
#     'education': ['school', 'university', 'library', 'secondary_school', 'primary_school'],
#     'nature': ['park', 'campground', 'rv_park', 'tourist_attraction'],
#     'health': ['hospital', 'pharmacy', 'doctor', 'dentist', 'physiotherapist', 'health'],
#     'transport': ['transit_station', 'bus_station', 'subway_station', 'train_station', 'airport'],
#     'shop': ['shopping_mall', 'supermarket', 'grocery_or_supermarket', 'convenience_store', 'store'],
#     'gym': ['gym', 'stadium', 'spa']
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
#             logger.error("[GEOCODE] Google Maps client not initialized")
#             return None
        
#         logger.info(f"[GEOCODE] Geocoding address: {address}")
#         geocode_result = gmaps.geocode(address)
        
#         if geocode_result:
#             location = geocode_result[0]['geometry']['location']
#             coordinates = (location['lat'], location['lng'])
#             logger.info(f"[GEOCODE] ✅ Success: {address} → {coordinates}")
#             return coordinates
        
#         logger.warning(f"[GEOCODE] ⚠️ No results for address: {address}")
#         return None
        
#     except Exception as e:
#         logger.error(f"[GEOCODE ERROR] {str(e)}")
#         return None


# def search_nearby_places(location, place_types, radius=DEFAULT_SEARCH_RADIUS):
#     """
#     Search for nearby places of specific types
#     location: tuple (lat, lng)
#     place_types: list of place types
#     radius: search radius in meters (default 5km)
#     """
#     try:
#         if not gmaps:
#             logger.error("[PLACES SEARCH] Google Maps client not initialized")
#             return []
        
#         logger.info(f"[PLACES SEARCH] Searching at {location} for types: {place_types} within {radius}m")
        
#         all_places = []
#         seen_place_ids = set()
        
#         for place_type in place_types:
#             logger.info(f"[PLACES SEARCH] Querying type: {place_type}")
            
#             places_result = gmaps.places_nearby(
#                 location=location,
#                 radius=radius,
#                 type=place_type
#             )
            
#             results = places_result.get('results', [])
#             logger.info(f"[PLACES SEARCH] Found {len(results)} results for {place_type}")
            
#             for place in results:
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
        
#         logger.info(f"[PLACES SEARCH] ✅ Total unique places found: {len(all_places)}")
#         return all_places
        
#     except Exception as e:
#         logger.error(f"[PLACES SEARCH ERROR] {str(e)}")
#         import traceback
#         traceback.print_exc()
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
#         'version': '1.1.0',
#         'google_maps_configured': bool(gmaps),
#         'default_radius_km': DEFAULT_SEARCH_RADIUS / 1000,
#         'available_categories': list(CATEGORY_MAPPING.keys())
#     }), 200


# @virtual_tour_bp.route('/search', methods=['POST'])
# def search_nearby():
#     """
#     Search for nearby places based on location and category
    
#     Request Body:
#     {
#         "location": "address or lat,lng string",
#         "category": "dining|education|nature|health|transport|shop|gym",
#         "radius": 5000 (optional, default 5km in meters)
#     }
    
#     Examples:
#     - location: "Connaught Place, New Delhi"
#     - location: "28.6139,77.2090"
#     """
#     try:
#         if not gmaps:
#             logger.error("[SEARCH] Google Maps API not configured")
#             return jsonify({
#                 'error': 'Google Maps API not configured',
#                 'details': 'GOOGLE_MAPS_API_KEY environment variable not set'
#             }), 500
        
#         data = request.get_json()
        
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400
        
#         location = data.get('location')
#         category = data.get('category', 'dining')
#         radius = data.get('radius', DEFAULT_SEARCH_RADIUS)  # Default 5km
        
#         if not location:
#             return jsonify({'error': 'Location is required'}), 400
        
#         logger.info(f"[SEARCH] 🔍 Request - Category: {category}, Location: {location}, Radius: {radius}m")
        
#         # ✅ CRITICAL: Parse location - could be address or "lat,lng"
#         coordinates = None
        
#         # Check if location is already in "lat,lng" format
#         if ',' in str(location):
#             try:
#                 parts = str(location).split(',')
#                 if len(parts) == 2:
#                     lat = float(parts[0].strip())
#                     lng = float(parts[1].strip())
#                     coordinates = (lat, lng)
#                     logger.info(f"[SEARCH] ✅ Using provided coordinates: {coordinates}")
#             except ValueError:
#                 logger.warning(f"[SEARCH] ⚠️ Failed to parse as coordinates, will geocode: {location}")
        
#         # If not coordinates, geocode the address
#         if not coordinates:
#             logger.info(f"[SEARCH] 🌍 Geocoding address: {location}")
#             coordinates = geocode_address(location)
            
#             if not coordinates:
#                 logger.error(f"[SEARCH] ❌ Geocoding failed for: {location}")
#                 return jsonify({
#                     'error': 'Invalid location or unable to geocode',
#                     'location_provided': location
#                 }), 400
        
#         # Get place types for the category
#         place_types = CATEGORY_MAPPING.get(category.lower(), ['restaurant'])
#         logger.info(f"[SEARCH] 📍 Searching for types: {place_types}")
        
#         # Search for places
#         places = search_nearby_places(
#             location=coordinates,
#             place_types=place_types,
#             radius=radius
#         )
        
#         if not places:
#             logger.warning(f"[SEARCH] ⚠️ No places found for category '{category}' at {coordinates}")
#             return jsonify({
#                 'success': True,
#                 'origin': {
#                     'lat': coordinates[0],
#                     'lng': coordinates[1]
#                 },
#                 'category': category,
#                 'places': [],
#                 'count': 0,
#                 'radius_km': radius / 1000,
#                 'message': f'No {category} places found within {radius/1000}km'
#             }), 200
        
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
#                 'user_ratings_total': place.get('user_ratings_total', 0),
#                 'distance': round(distance, 2),
#                 'coordinates': {
#                     'lat': place['lat'],
#                     'lng': place['lng']
#                 },
#                 'photo_url': place.get('photo_url', ''),
#                 'types': place.get('types', []),
#                 'is_open': place.get('is_open', None)
#             })
        
#         # Sort by distance (closest first)
#         formatted_places.sort(key=lambda x: x['distance'])
        
#         logger.info(f"[SEARCH] ✅ SUCCESS - Found {len(formatted_places)} places")
#         logger.info(f"[SEARCH] 📊 Top 3 results: {[p['name'] for p in formatted_places[:3]]}")
        
#         return jsonify({
#             'success': True,
#             'origin': {
#                 'lat': coordinates[0],
#                 'lng': coordinates[1]
#             },
#             'category': category,
#             'places': formatted_places,
#             'count': len(formatted_places),
#             'radius_km': radius / 1000
#         }), 200
        
#     except Exception as e:
#         logger.error(f"[SEARCH ERROR] ❌ {str(e)}")
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

# Initialize Google Maps client
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY) if GOOGLE_MAPS_API_KEY else None

# ✅ Default search radius: 5km (5000 meters)
DEFAULT_SEARCH_RADIUS = 5000

# ✅ Apartment coordinates (VERDE BY SOBHA, Dubai)
APARTMENT_COORDINATES = {
    'lat': 25.0694755,
    'lng': 55.1468862,
    'name': 'VERDE BY SOBHA'
}

# Category mapping
CATEGORY_MAPPING = {
    'dining': ['restaurant', 'cafe', 'bakery', 'meal_takeaway', 'meal_delivery'],
    'education': ['school', 'university', 'library', 'secondary_school', 'primary_school'],
    'nature': ['park', 'campground', 'rv_park', 'tourist_attraction'],
    'health': ['hospital', 'pharmacy', 'doctor', 'dentist', 'physiotherapist', 'health'],
    'transport': ['transit_station', 'bus_station', 'subway_station', 'train_station', 'airport'],
    'shop': ['shopping_mall', 'supermarket', 'grocery_or_supermarket', 'convenience_store', 'store'],
    'gym': ['gym', 'stadium', 'spa']
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
    R = 6371.0  # Earth's radius in kilometers
    
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
            logger.error("[GEOCODE] Google Maps client not initialized")
            return None
        
        logger.info(f"[GEOCODE] Geocoding address: {address}")
        geocode_result = gmaps.geocode(address)
        
        if geocode_result:
            location = geocode_result[0]['geometry']['location']
            coordinates = (location['lat'], location['lng'])
            formatted_address = geocode_result[0].get('formatted_address', address)
            logger.info(f"[GEOCODE] ✅ Success: {address} → {coordinates}")
            return {
                'coordinates': coordinates,
                'formatted_address': formatted_address,
                'place_name': geocode_result[0].get('address_components', [{}])[0].get('long_name', address)
            }
        
        logger.warning(f"[GEOCODE] ⚠️ No results for address: {address}")
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
            logger.error("[PLACES SEARCH] Google Maps client not initialized")
            return []
        
        logger.info(f"[PLACES SEARCH] Searching at {location} for types: {place_types} within {radius}m")
        
        all_places = []
        seen_place_ids = set()
        
        for place_type in place_types:
            logger.info(f"[PLACES SEARCH] Querying type: {place_type}")
            
            places_result = gmaps.places_nearby(
                location=location,
                radius=radius,
                type=place_type
            )
            
            results = places_result.get('results', [])
            logger.info(f"[PLACES SEARCH] Found {len(results)} results for {place_type}")
            
            for place in results:
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
        
        logger.info(f"[PLACES SEARCH] ✅ Total unique places found: {len(all_places)}")
        return all_places
        
    except Exception as e:
        logger.error(f"[PLACES SEARCH ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
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
        'version': '2.0.0',
        'google_maps_configured': bool(gmaps),
        'default_radius_km': DEFAULT_SEARCH_RADIUS / 1000,
        'available_categories': list(CATEGORY_MAPPING.keys()),
        'apartment': APARTMENT_COORDINATES
    }), 200


@virtual_tour_bp.route('/search', methods=['POST'])
def search_nearby():
    """
    ✅ FIXED: Two modes of search:
    
    MODE 1: Category-based search (is_custom_search = False)
    - Search for category places near apartment
    - Returns multiple places within radius
    
    MODE 2: Custom location search (is_custom_search = True)
    - Geocode the custom location
    - Return ONLY that location with distance from apartment
    - Ignore category and radius
    
    Request Body:
    {
        "location": "address or lat,lng string",
        "category": "dining|education|...",
        "radius": 5000,
        "is_custom_search": true/false
    }
    """
    try:
        if not gmaps:
            logger.error("[SEARCH] Google Maps API not configured")
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
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        logger.info(f"[SEARCH] 🔍 Mode: {'CUSTOM' if is_custom_search else 'CATEGORY'}")
        logger.info(f"[SEARCH] Location: {location}, Category: {category}, Radius: {radius}m")
        
        # ✅ MODE 1: CUSTOM LOCATION SEARCH
        if is_custom_search:
            logger.info("[SEARCH] 📍 Custom location mode - Geocoding user input...")
            
            # Geocode the custom location
            geocode_result = geocode_address(location)
            
            if not geocode_result:
                logger.error(f"[SEARCH] ❌ Failed to geocode: {location}")
                return jsonify({
                    'error': 'Could not find location',
                    'location_provided': location,
                    'suggestion': 'Try a more specific address (e.g., "Burj Khalifa, Dubai")'
                }), 400
            
            custom_coords = geocode_result['coordinates']
            place_name = geocode_result['place_name']
            formatted_address = geocode_result['formatted_address']
            
            # Calculate distance from apartment
            apartment_coords = (APARTMENT_COORDINATES['lat'], APARTMENT_COORDINATES['lng'])
            distance = calculate_distance(apartment_coords, custom_coords)
            
            logger.info(f"[SEARCH] ✅ Found: {place_name}")
            logger.info(f"[SEARCH] 📏 Distance from apartment: {distance:.2f}km")
            
            # Return ONLY this one location
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
        
        # ✅ MODE 2: CATEGORY-BASED SEARCH (near apartment)
        else:
            logger.info("[SEARCH] 📂 Category mode - Searching near apartment...")
            
            # Parse apartment coordinates
            apartment_coords = (APARTMENT_COORDINATES['lat'], APARTMENT_COORDINATES['lng'])
            
            # Get place types for the category
            place_types = CATEGORY_MAPPING.get(category.lower(), ['restaurant'])
            logger.info(f"[SEARCH] 📍 Searching for types: {place_types}")
            
            # Search for places
            places = search_nearby_places(
                location=apartment_coords,
                place_types=place_types,
                radius=radius
            )
            
            if not places:
                logger.warning(f"[SEARCH] ⚠️ No places found for category '{category}'")
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
            
            # Calculate distances and format response
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
            
            # Sort by distance (closest first)
            formatted_places.sort(key=lambda x: x['distance'])
            
            logger.info(f"[SEARCH] ✅ SUCCESS - Found {len(formatted_places)} places")
            
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
    """Get directions between origin and destination"""
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
    """Get detailed information about a specific place"""
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