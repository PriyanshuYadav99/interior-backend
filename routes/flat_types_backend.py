"""
flat_types_backend.py — copy this ONE route into routes/design_routes.py
(the file with @design_bp routes — the one with simple_register, generate_design, etc.)

Public, no-auth endpoint that the FRONTEND calls on page load to get the real
list of unit types for whichever client is loaded (?client=ellington etc).
Reads the exact same property_sections table your admin dashboard already uses,
so it is automatically always in sync — add/remove a property in Supabase and
this endpoint (and therefore the pills on the public site) update with zero
code changes or redeploys.

GET /api/flat-types/<client_name>
  -> only returns ACTIVE sections (is_active = true), same rule the admin
     dashboard/property-filter dropdown already follows, so what a visitor
     can click always matches what's actually for sale.
"""


@design_bp.route('/api/flat-types/<client_name>', methods=['GET'])
def get_flat_types(client_name):
    try:
        VALID_CLIENTS = ['skyline', 'ellington', 'sothebys']
        if client_name not in VALID_CLIENTS:
            return jsonify({'error': f'Invalid client. Must be one of: {VALID_CLIENTS}'}), 400

        sections = supabase.table('property_sections') \
            .select('section_key, section_name, property_type, display_order') \
            .eq('client_name', client_name) \
            .eq('is_active', True) \
            .order('display_order') \
            .execute().data or []

        flat_types = [{
            'id': s['section_key'],
            'name': s.get('property_type') or s['section_name'],
        } for s in sections]

        return jsonify({'success': True, 'client_name': client_name, 'flat_types': flat_types}), 200

    except Exception as e:
        logger.error(f"[FLAT TYPES] Error: {e}")
        return jsonify({'error': 'Failed to load flat types'}), 500