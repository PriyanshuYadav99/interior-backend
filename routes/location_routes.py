"""
Location routes — the API surface for registering and looking up
client → coordinates → profile mappings.

POST /api/location/resolve      -> create-or-fetch a client's location
GET  /api/location/<client_name> -> read-only fetch of what's on file
"""

import logging
from flask import Blueprint, request, jsonify

from services.location_service import get_or_create_location, get_location_by_client

logger = logging.getLogger(__name__)
location_bp = Blueprint('location', __name__, url_prefix='/api/location')


@location_bp.route('/resolve', methods=['POST', 'OPTIONS'])
def resolve_location():
    if request.method == 'OPTIONS':
        return '', 204
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        lat, lng = data.get('lat'), data.get('lng')
        if lat is None or lng is None:
            return jsonify({'error': 'lat and lng are required'}), 400

        location, created = get_or_create_location(
            lat=lat, lng=lng,
            client_name=data.get('client_name'),
            name=data.get('name'),
            config=data.get('config'),
        )
        return jsonify({'success': True, 'created': created, 'location': location}), 200

    except Exception as e:
        logger.error(f"[LOCATION_RESOLVE] {e}")
        return jsonify({'error': 'Failed to resolve location', 'details': str(e)}), 500


@location_bp.route('/<client_name>', methods=['GET'])
def get_location(client_name):
    try:
        location = get_location_by_client(client_name)
        if not location:
            return jsonify({'error': 'No location on file for this client'}), 404
        return jsonify({'success': True, 'location': location}), 200
    except Exception as e:
        logger.error(f"[LOCATION_GET] {e}")
        return jsonify({'error': 'Failed to fetch location'}), 500