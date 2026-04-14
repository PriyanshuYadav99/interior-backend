
# """
# admin_routes.py — PropDesk Builder Admin Dashboard
# Sessions stored in Supabase (persistent across restarts).
# """

# from flask import Blueprint, request, jsonify
# from functools import wraps
# import logging
# from datetime import datetime, timedelta, timezone
# import secrets
# import hashlib

# logger = logging.getLogger(__name__)
# admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# # ─── Helpers ────────────────────────────────────────────────

# def generate_token():
#     return secrets.token_hex(32)

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def verify_token(token):
#     if not token:
#         return None
#     try:
#         from app import supabase
#         now = datetime.now(timezone.utc).isoformat()

#         result = supabase.table('builder_sessions') \
#             .select('*') \
#             .eq('token', token) \
#             .gt('expires_at', now) \
#             .execute()

#         if not result.data:
#             return None

#         session = result.data[0]
#         return {
#             'username': session['username'],
#             'client_name': session['client_name'],
#             'company_name': session.get('company_name', ''),
#             'property_name': session.get('property_name', ''),
#             'builder_id': session['builder_id']
#         }
#     except Exception as e:
#         logger.error(f"[VERIFY_TOKEN] Error: {e}")
#         return None

# def builder_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
#         session = verify_token(token)
#         if not session:
#             return jsonify({'error': 'Unauthorized'}), 401
#         request.builder = session
#         return f(*args, **kwargs)
#     return decorated


# # ============================================================
# # 1. LOGIN
# # POST /api/admin/login
# # ============================================================

# @admin_bp.route('/login', methods=['POST', 'OPTIONS'])
# def builder_login():
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         from app import supabase

#         data = request.get_json()
#         if not data:
#             return jsonify({'error': 'JSON body required'}), 400

#         username = data.get('username', '').strip()
#         password = data.get('password', '').strip()

#         if not username or not password:
#             return jsonify({'error': 'Username and password required'}), 400

#         result = supabase.table('builders') \
#             .select('*') \
#             .eq('username', username) \
#             .eq('password_hash', hash_password(password)) \
#             .eq('is_active', True) \
#             .execute()

#         if not result.data:
#             logger.warning(f"[LOGIN] Failed: {username}")
#             return jsonify({'error': 'Invalid credentials'}), 401

#         builder = result.data[0]
#         token = generate_token()
#         expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

#         supabase.table('builder_sessions').insert({
#             'token': token,
#             'username': username,
#             'client_name': builder['client_name'],
#             'company_name': builder.get('company_name', ''),
#             'property_name': builder.get('property_name', ''),
#             'builder_id': builder['id'],
#             'expires_at': expires_at.isoformat()
#         }).execute()

#         logger.info(f"[LOGIN] Success: {username}")

#         return jsonify({
#             'success': True,
#             'token': token,
#             'client_name': builder['client_name'],
#             'company_name': builder.get('company_name', ''),
#             'property_name': builder.get('property_name', '')
#         }), 200

#     except Exception as e:
#         logger.error(f"[LOGIN] Error: {e}")
#         return jsonify({'error': 'Login failed'}), 500


# # ============================================================
# # 2. DASHBOARD
# # GET /api/admin/dashboard
# # ============================================================

# @admin_bp.route('/dashboard', methods=['GET'])
# @builder_required
# def get_dashboard():
#     try:
#         from app import supabase
#         client_name = request.builder['client_name']

#         sections_result = supabase.table('property_sections') \
#             .select('*') \
#             .eq('client_name', client_name) \
#             .eq('is_active', True) \
#             .order('display_order') \
#             .execute()

#         sections = []
#         for s in (sections_result.data or []):
#             count = supabase.table('users') \
#                 .select('id', count='exact') \
#                 .eq('client_name', client_name) \
#                 .execute()

#             sections.append({
#                 'id': s['section_key'],
#                 'name': s['section_name'],
#                 'type': s['property_type'],
#                 'leads': count.count or 0
#             })

#         return jsonify({
#             'success': True,
#             'company_name': request.builder['company_name'],
#             'property_name': request.builder['property_name'],
#             'sections': sections
#         }), 200

#     except Exception as e:
#         logger.error(f"[DASHBOARD] Error: {e}")
#         return jsonify({'error': 'Failed to load dashboard'}), 500


# # ============================================================
# # 3. LEADS LIST
# # GET /api/admin/leads?section=2bhk
# # ============================================================

# @admin_bp.route('/leads', methods=['GET'])
# @builder_required
# def get_leads():
#     try:
#         from app import supabase
#         client_name = request.builder['client_name']
#         section = request.args.get('section', '').strip()

#         query = supabase.table('users') \
#             .select('*') \
#             .eq('client_name', client_name) \
#             .order('created_at', desc=True)

#         if section:
#             query = query.eq('property_section', section)

#         result = query.execute()

#         leads = []
#         for u in (result.data or []):
#             leads.append({
#                 'id': u['id'],
#                 'name': u.get('full_name', 'Unknown'),
#                 'phone': f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
#                 'email': u.get('email', 'N/A'),
#                 'inquiry_date': u.get('created_at', ''),
#                 'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0)
#             })

#         return jsonify({
#             'success': True,
#             'section': section or 'all',
#             'leads': leads,
#             'total': len(leads)
#         }), 200

#     except Exception as e:
#         logger.error(f"[LEADS] Error: {e}")
#         return jsonify({'error': 'Failed to load leads'}), 500


# # ============================================================
# # 4. LEAD DETAILS — UPDATED
# # GET /api/admin/leads/<user_id>
# # ============================================================

# @admin_bp.route('/leads/<user_id>', methods=['GET'])
# @builder_required
# def get_lead_details(user_id):
#     try:
#         from app import supabase
#         client_name = request.builder['client_name']

#         # ── Fetch user ──────────────────────────────────────
#         user_result = supabase.table('users') \
#             .select('*') \
#             .eq('id', user_id) \
#             .execute()

#         if not user_result.data:
#             return jsonify({'error': 'Lead not found'}), 404

#         u = user_result.data[0]

#         if u.get('client_name') != client_name:
#             return jsonify({'error': 'Unauthorized'}), 403

#         # ── Fetch sessions ──────────────────────────────────
#         sessions_result = supabase.table('sessions') \
#             .select('session_id') \
#             .eq('user_id', user_id) \
#             .execute()

#         session_ids = [s['session_id'] for s in (sessions_result.data or [])]

#         # ── Fetch generated images ──────────────────────────
#         if session_ids:
#             gens_result = supabase.table('user_generations') \
#                 .select('*') \
#                 .or_(f"user_id.eq.{user_id},session_id.in.({','.join(session_ids)})") \
#                 .order('created_at', desc=True) \
#                 .execute()
#         else:
#             gens_result = supabase.table('user_generations') \
#                 .select('*') \
#                 .eq('user_id', user_id) \
#                 .order('created_at', desc=True) \
#                 .execute()

#         seen = set()
#         images = []
#         for g in (gens_result.data or []):
#             key = g.get('generation_id') or g.get('id')
#             if key in seen:
#                 continue
#             seen.add(key)
#             images.append({
#                 'id': key,
#                 'image_url': g.get('image_url', ''),
#                 'room_type': g.get('room_type', 'N/A'),
#                 'style': g.get('style', 'N/A'),
#                 'created_at': g.get('created_at', ''),
#                 'downloaded': g.get('downloaded', False),
#                 'download_count': g.get('download_count', 0)
#             })

#         # ── Fetch activity logs (tools used + time spent) ───
#         activity_result = supabase.table('user_activity_logs') \
#             .select('*') \
#             .eq('user_id', user_id) \
#             .execute()

#         activity_data = activity_result.data or []

#         # Aggregate tools used and total time per tool
#         tools_summary = {}
#         for a in activity_data:
#             tool = a.get('tool_name') or a.get('activity_type') or 'unknown'
#             secs = a.get('time_spent_seconds', 0) or 0
#             if tool not in tools_summary:
#                 tools_summary[tool] = {
#                     'tool': tool,
#                     'total_time_seconds': 0,
#                     'sessions_count': 0
#                 }
#             tools_summary[tool]['total_time_seconds'] += secs
#             tools_summary[tool]['sessions_count'] += 1

#         tools_used = list(tools_summary.values())
#         total_time_seconds = sum(t['total_time_seconds'] for t in tools_used)

#         # ── Fetch virtual tour selections ───────────────────
#         vt_result = supabase.table('user_tool_selections') \
#             .select('*') \
#             .eq('user_id', user_id) \
#             .eq('tool_name', 'virtual_tour') \
#             .order('created_at', desc=True) \
#             .execute()

#         vt_selections = []
#         for v in (vt_result.data or []):
#             vt_selections.append({
#                 'category': v.get('vt_category'),
#                 'place_name': v.get('vt_place_name'),
#                 'place_id': v.get('vt_place_id'),
#                 'photo_url': v.get('vt_photo_url'),
#                 'distance': v.get('vt_distance'),
#                 'rating': v.get('vt_rating'),
#                 'viewed_at': v.get('created_at')
#             })

#         # Unique categories explored
#         vt_categories = list({
#             v['category'] for v in vt_selections if v['category']
#         })

#         # ── Fetch LifeEcho selections ───────────────────────
#         le_result = supabase.table('user_tool_selections') \
#             .select('*') \
#             .eq('user_id', user_id) \
#             .eq('tool_name', 'lifeecho') \
#             .order('created_at', desc=True) \
#             .execute()

#         lifeecho_selections = []
#         for l in (le_result.data or []):
#             lifeecho_selections.append({
#     'scenario_id': l.get('lifeecho_scenario_id'),
#     'scenario_title': l.get('lifeecho_scenario_title'),
#     'scenario_icon': l.get('lifeecho_scenario_icon', 'clock'),
#     'is_custom': l.get('lifeecho_is_custom', False),
#     'custom_text': l.get('lifeecho_custom_text'),
#     'selected_at': l.get('created_at')
# })

#         # ── Build final response ────────────────────────────
#         return jsonify({
#             'success': True,
#             'lead': {
#                 # Basic info
#                 'id': u['id'],
#                 'name': u.get('full_name', 'Unknown'),
#                 'phone': f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
#                 'email': u.get('email', 'N/A'),
#                 'registration_date': u.get('created_at', ''),
#                 'property_section': u.get('property_section'),

#                 # Design generations
#                 'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0),
#                 'images': images,

#                 # Time spent + tools
#                 'total_time_spent_seconds': total_time_seconds,
#                 'total_time_spent_minutes': round(total_time_seconds / 60, 1),
#                 'tools_used': tools_used,

#                 # Virtual tour
#                 'virtual_tour': {
#                     'categories_explored': vt_categories,
#                     'places_viewed': vt_selections
#                 },

#                 # LifeEcho
#                 'lifeecho': {
#                     'total_scenarios_viewed': len(lifeecho_selections),
#                     'scenarios': lifeecho_selections
#                 }
#             }
#         }), 200

#     except Exception as e:
#         logger.error(f"[LEAD DETAILS] Error: {e}")
#         return jsonify({'error': 'Failed to load lead details'}), 500


# # ============================================================
# # 5. ANALYTICS
# # GET /api/admin/analytics
# # ============================================================

# @admin_bp.route('/analytics', methods=['GET'])
# @builder_required
# def get_analytics():
#     try:
#         from app import supabase
#         client_name = request.builder['client_name']
#         today = datetime.now(timezone.utc).date().isoformat()

#         total_leads = supabase.table('users').select('id', count='exact').eq('client_name', client_name).execute()
#         total_gens  = supabase.table('user_generations').select('id', count='exact').eq('client_name', client_name).execute()
#         today_leads = supabase.table('users').select('id', count='exact').eq('client_name', client_name).gte('created_at', today).execute()
#         today_gens  = supabase.table('user_generations').select('id', count='exact').eq('client_name', client_name).gte('created_at', today).execute()

#         return jsonify({
#             'success': True,
#             'analytics': {
#                 'total_leads': total_leads.count or 0,
#                 'total_generations': total_gens.count or 0,
#                 'today_leads': today_leads.count or 0,
#                 'today_generations': today_gens.count or 0
#             }
#         }), 200

#     except Exception as e:
#         logger.error(f"[ANALYTICS] Error: {e}")
#         return jsonify({'error': 'Failed to load analytics'}), 500


# # ============================================================
# # 6. SEARCH
# # GET /api/admin/search?q=amit
# # ============================================================

# @admin_bp.route('/search', methods=['GET'])
# @builder_required
# def search_leads():
#     try:
#         from app import supabase
#         client_name = request.builder['client_name']
#         q = request.args.get('q', '').strip()

#         if not q:
#             return jsonify({'error': 'Search query required'}), 400

#         result = supabase.table('users') \
#             .select('*') \
#             .eq('client_name', client_name) \
#             .or_(f"full_name.ilike.%{q}%,email.ilike.%{q}%,phone_number.ilike.%{q}%") \
#             .order('created_at', desc=True) \
#             .execute()

#         results = []
#         for u in (result.data or []):
#             results.append({
#                 'id': u['id'],
#                 'name': u.get('full_name', 'Unknown'),
#                 'phone': f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
#                 'email': u.get('email', 'N/A'),
#                 'inquiry_date': u.get('created_at', ''),
#                 'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0)
#             })

#         return jsonify({
#             'success': True,
#             'query': q,
#             'results': results,
#             'count': len(results)
#         }), 200

#     except Exception as e:
#         logger.error(f"[SEARCH] Error: {e}")
#         return jsonify({'error': 'Search failed'}), 500


# # ============================================================
# # 7. LOGOUT
# # POST /api/admin/logout
# # ============================================================

# @admin_bp.route('/logout', methods=['POST'])
# @builder_required
# def logout():
#     try:
#         from app import supabase
#         token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()

#         supabase.table('builder_sessions') \
#             .delete() \
#             .eq('token', token) \
#             .execute()

#         return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
#     except Exception as e:
#         logger.error(f"[LOGOUT] Error: {e}")
#         return jsonify({'error': 'Logout failed'}), 500

"""
admin_routes.py — PropDesk Builder Admin Dashboard
Sessions stored in Supabase (persistent across restarts).
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging
from datetime import datetime, timedelta, timezone
import secrets
import hashlib

logger = logging.getLogger(__name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


# ─── Helpers ────────────────────────────────────────────────

def generate_token():
    return secrets.token_hex(32)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_token(token):
    if not token:
        return None
    try:
        from app import supabase
        now = datetime.now(timezone.utc).isoformat()

        result = supabase.table('builder_sessions') \
            .select('*') \
            .eq('token', token) \
            .gt('expires_at', now) \
            .execute()

        if not result.data:
            return None

        session = result.data[0]
        return {
            'username': session['username'],
            'client_name': session['client_name'],
            'company_name': session.get('company_name', ''),
            'property_name': session.get('property_name', ''),
            'builder_id': session['builder_id']
        }
    except Exception as e:
        logger.error(f"[VERIFY_TOKEN] Error: {e}")
        return None

def builder_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
        session = verify_token(token)
        if not session:
            return jsonify({'error': 'Unauthorized'}), 401
        request.builder = session
        return f(*args, **kwargs)
    return decorated


# ============================================================
# 1. LOGIN
# POST /api/admin/login
# ============================================================

@admin_bp.route('/login', methods=['POST', 'OPTIONS'])
def builder_login():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from app import supabase

        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        result = supabase.table('builders') \
            .select('*') \
            .eq('username', username) \
            .eq('password_hash', hash_password(password)) \
            .eq('is_active', True) \
            .execute()

        if not result.data:
            logger.warning(f"[LOGIN] Failed: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401

        builder = result.data[0]
        token = generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        supabase.table('builder_sessions').insert({
            'token': token,
            'username': username,
            'client_name': builder['client_name'],
            'company_name': builder.get('company_name', ''),
            'property_name': builder.get('property_name', ''),
            'builder_id': builder['id'],
            'expires_at': expires_at.isoformat()
        }).execute()

        logger.info(f"[LOGIN] Success: {username}")

        return jsonify({
            'success': True,
            'token': token,
            'client_name': builder['client_name'],
            'company_name': builder.get('company_name', ''),
            'property_name': builder.get('property_name', '')
        }), 200

    except Exception as e:
        logger.error(f"[LOGIN] Error: {e}")
        return jsonify({'error': 'Login failed'}), 500


# ============================================================
# 2. DASHBOARD
# GET /api/admin/dashboard
# ============================================================

@admin_bp.route('/dashboard', methods=['GET'])
@builder_required
def get_dashboard():
    try:
        from app import supabase
        client_name = request.builder['client_name']

        sections_result = supabase.table('property_sections') \
            .select('*') \
            .eq('client_name', client_name) \
            .eq('is_active', True) \
            .order('display_order') \
            .execute()

        sections = []
        for s in (sections_result.data or []):
            count = supabase.table('users') \
                .select('id', count='exact') \
                .eq('client_name', client_name) \
                .execute()

            sections.append({
                'id': s['section_key'],
                'name': s['section_name'],
                'type': s['property_type'],
                'leads': count.count or 0
            })

        return jsonify({
            'success': True,
            'company_name': request.builder['company_name'],
            'property_name': request.builder['property_name'],
            'sections': sections
        }), 200

    except Exception as e:
        logger.error(f"[DASHBOARD] Error: {e}")
        return jsonify({'error': 'Failed to load dashboard'}), 500


# ============================================================
# 3. LEADS LIST
# GET /api/admin/leads?section=2bhk
# ============================================================

@admin_bp.route('/leads', methods=['GET'])
@builder_required
def get_leads():
    try:
        from app import supabase
        client_name = request.builder['client_name']
        section = request.args.get('section', '').strip()

        query = supabase.table('users') \
            .select('*') \
            .eq('client_name', client_name) \
            .order('created_at', desc=True)

        if section:
            query = query.eq('property_section', section)

        result = query.execute()

        leads = []
        for u in (result.data or []):
            leads.append({
                'id': u['id'],
                'name': u.get('full_name', 'Unknown'),
                'phone': f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
                'email': u.get('email', 'N/A'),
                'inquiry_date': u.get('created_at', ''),
                'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0)
            })

        return jsonify({
            'success': True,
            'section': section or 'all',
            'leads': leads,
            'total': len(leads)
        }), 200

    except Exception as e:
        logger.error(f"[LEADS] Error: {e}")
        return jsonify({'error': 'Failed to load leads'}), 500


# ============================================================
# 4. LEAD DETAILS
# GET /api/admin/leads/<user_id>
# GET /api/admin/leads/<user_id>?include_temperature=true   ← opt-in AI scoring
# ============================================================

@admin_bp.route('/leads/<user_id>', methods=['GET'])
@builder_required
def get_lead_details(user_id):
    try:
        from app import supabase
        client_name = request.builder['client_name']

        # ── Fetch user ──────────────────────────────────────
        user_result = supabase.table('users') \
            .select('*') \
            .eq('id', user_id) \
            .execute()

        if not user_result.data:
            return jsonify({'error': 'Lead not found'}), 404

        u = user_result.data[0]

        if u.get('client_name') != client_name:
            return jsonify({'error': 'Unauthorized'}), 403

        # ── Fetch sessions ──────────────────────────────────
        sessions_result = supabase.table('sessions') \
            .select('session_id') \
            .eq('user_id', user_id) \
            .execute()

        session_ids = [s['session_id'] for s in (sessions_result.data or [])]

        # ── Fetch generated images ──────────────────────────
        if session_ids:
            gens_result = supabase.table('user_generations') \
                .select('*') \
                .or_(f"user_id.eq.{user_id},session_id.in.({','.join(session_ids)})") \
                .order('created_at', desc=True) \
                .execute()
        else:
            gens_result = supabase.table('user_generations') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .execute()

        seen = set()
        images = []
        for g in (gens_result.data or []):
            key = g.get('generation_id') or g.get('id')
            if key in seen:
                continue
            seen.add(key)
            images.append({
                'id': key,
                'image_url': g.get('image_url', ''),
                'room_type': g.get('room_type', 'N/A'),
                'style': g.get('style', 'N/A'),
                'created_at': g.get('created_at', ''),
                'downloaded': g.get('downloaded', False),
                'download_count': g.get('download_count', 0)
            })

        # ── Fetch activity logs ─────────────────────────────
        activity_result = supabase.table('user_activity_logs') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()

        activity_data = activity_result.data or []

        tools_summary = {}
        for a in activity_data:
            tool = a.get('tool_name') or a.get('activity_type') or 'unknown'
            secs = a.get('time_spent_seconds', 0) or 0
            if tool not in tools_summary:
                tools_summary[tool] = {
                    'tool': tool,
                    'total_time_seconds': 0,
                    'sessions_count': 0
                }
            tools_summary[tool]['total_time_seconds'] += secs
            tools_summary[tool]['sessions_count'] += 1

        tools_used = list(tools_summary.values())
        total_time_seconds = sum(t['total_time_seconds'] for t in tools_used)

        # ── Fetch virtual tour selections ───────────────────
        vt_result = supabase.table('user_tool_selections') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('tool_name', 'virtual_tour') \
            .order('created_at', desc=True) \
            .execute()

        vt_selections = []
        for v in (vt_result.data or []):
            vt_selections.append({
                'category':   v.get('vt_category'),
                'place_name': v.get('vt_place_name'),
                'place_id':   v.get('vt_place_id'),
                'photo_url':  v.get('vt_photo_url'),
                'distance':   v.get('vt_distance'),
                'rating':     v.get('vt_rating'),
                'viewed_at':  v.get('created_at')
            })

        vt_categories = list({v['category'] for v in vt_selections if v['category']})

        # ── Fetch LifeEcho selections ───────────────────────
        le_result = supabase.table('user_tool_selections') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('tool_name', 'lifeecho') \
            .order('created_at', desc=True) \
            .execute()

        lifeecho_selections = []
        for l in (le_result.data or []):
            lifeecho_selections.append({
                'scenario_id':    l.get('lifeecho_scenario_id'),
                'scenario_title': l.get('lifeecho_scenario_title'),
                'scenario_icon':  l.get('lifeecho_scenario_icon', 'clock'),
                'is_custom':      l.get('lifeecho_is_custom', False),
                'custom_text':    l.get('lifeecho_custom_text'),
                'selected_at':    l.get('created_at')
            })

        # ── Optional: Lead Temperature (AI scoring) ─────────
        temperature_data = None
        if request.args.get('include_temperature', '').lower() == 'true':
            try:
                from ai_routes import build_lead_payload
                from groq import Groq
                import os, json, re

                groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))
                lead_data, _ = build_lead_payload(user_id, supabase)

                if lead_data:
                    design_styles  = list({img['style'] for img in lead_data.get('images', []) if img.get('style')})
                    vt_info        = lead_data.get('virtual_tour', {})
                    le_info        = lead_data.get('lifeecho', {})
                    tools_list     = list({t['tool'] for t in lead_data.get('tools_used', []) if t.get('tool')})
                    scenario_texts = [
                        s.get('scenario_title') or s.get('custom_text', '')
                        for s in le_info.get('scenarios', [])
                    ]
                    vt_places = [p['place_name'] for p in vt_info.get('places_viewed', []) if p.get('place_name')]

                    lead_payload_dict = {
                        "total_time_spent_minutes": lead_data.get('total_time_spent_minutes', 0),
                        "unique_design_styles":     design_styles,
                        "tools_used":               tools_list,
                        "lifeecho_scenarios":       scenario_texts,
                        "virtual_tour_places":      vt_places,
                        "virtual_tour_categories":  vt_info.get('categories_explored', [])
                    }

                    # ── FIX: use json.dumps(lead_payload_dict) directly in the f-string ──
                    temperature_prompt = f"""You are an expert Real Estate Sales Analyst AI for PropDeck. Analyze the buyer activity and return lead temperature.

Scoring (100 pts total):
1. Session Duration (max 40 pts): 20+ min=40, 10-19=30, 3-9=20, <3=10
2. Design Consistency (max 20 pts): 1 style=20, 2 styles=10, 3+ styles=0
3. Tool Engagement Depth (max 20 pts): both lifeecho+virtual_tour=20, one=10, neither=0
4. Intent Specificity (max 20 pts): high-intent keywords (health,daycare,elderly,school,hospital,accessibility,pets)=20, generic (shopping,market,metro,transport)=10, none=0

Thresholds: HOT=75-100, WARM=45-74, COLD<45

Return ONLY valid JSON, no markdown:
{{"score":<int>,"temperature":"HOT|WARM|COLD","reasoning":"1-2 sentences","sales_strategy":"1-2 sentences"}}

USER SESSION DATA:
{json.dumps(lead_payload_dict, indent=2)}"""

                    comp = groq_client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "user", "content": temperature_prompt}],
                        temperature=0.3,
                        max_tokens=400
                    )

                    raw = comp.choices[0].message.content.strip()
                    clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.DOTALL).strip()
                    match = re.search(r'\{.*\}', clean, re.DOTALL)
                    if match:
                        temperature_data = json.loads(match.group())

            except Exception as te:
                logger.error(f"[TEMPERATURE IN DETAILS] Non-fatal error: {te}")
                temperature_data = None

        # ── Build final response ────────────────────────────
        lead_response = {
            'id':                u['id'],
            'name':              u.get('full_name', 'Unknown'),
            'phone':             f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
            'email':             u.get('email', 'N/A'),
            'registration_date': u.get('created_at', ''),
            'property_section':  u.get('property_section'),

            'total_generations':      (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0),
            'images':                 images,

            'total_time_spent_seconds': total_time_seconds,
            'total_time_spent_minutes': round(total_time_seconds / 60, 1),
            'tools_used':               tools_used,

            'virtual_tour': {
                'categories_explored': vt_categories,
                'places_viewed':       vt_selections
            },

            'lifeecho': {
                'total_scenarios_viewed': len(lifeecho_selections),
                'scenarios':              lifeecho_selections
            }
        }

        if temperature_data:
            lead_response['temperature'] = temperature_data

        return jsonify({'success': True, 'lead': lead_response}), 200

    except Exception as e:
        logger.error(f"[LEAD DETAILS] Error: {e}")
        return jsonify({'error': 'Failed to load lead details'}), 500


# ============================================================
# 5. ANALYTICS
# GET /api/admin/analytics
# ============================================================

@admin_bp.route('/analytics', methods=['GET'])
@builder_required
def get_analytics():
    try:
        from app import supabase
        client_name = request.builder['client_name']
        today = datetime.now(timezone.utc).date().isoformat()

        total_leads = supabase.table('users').select('id', count='exact').eq('client_name', client_name).execute()
        total_gens  = supabase.table('user_generations').select('id', count='exact').eq('client_name', client_name).execute()
        today_leads = supabase.table('users').select('id', count='exact').eq('client_name', client_name).gte('created_at', today).execute()
        today_gens  = supabase.table('user_generations').select('id', count='exact').eq('client_name', client_name).gte('created_at', today).execute()

        return jsonify({
            'success': True,
            'analytics': {
                'total_leads':       total_leads.count or 0,
                'total_generations': total_gens.count or 0,
                'today_leads':       today_leads.count or 0,
                'today_generations': today_gens.count or 0
            }
        }), 200

    except Exception as e:
        logger.error(f"[ANALYTICS] Error: {e}")
        return jsonify({'error': 'Failed to load analytics'}), 500


# ============================================================
# 6. SEARCH
# GET /api/admin/search?q=amit
# ============================================================

@admin_bp.route('/search', methods=['GET'])
@builder_required
def search_leads():
    try:
        from app import supabase
        client_name = request.builder['client_name']
        q = request.args.get('q', '').strip()

        if not q:
            return jsonify({'error': 'Search query required'}), 400

        result = supabase.table('users') \
            .select('*') \
            .eq('client_name', client_name) \
            .or_(f"full_name.ilike.%{q}%,email.ilike.%{q}%,phone_number.ilike.%{q}%") \
            .order('created_at', desc=True) \
            .execute()

        results = []
        for u in (result.data or []):
            results.append({
                'id':                u['id'],
                'name':              u.get('full_name', 'Unknown'),
                'phone':             f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
                'email':             u.get('email', 'N/A'),
                'inquiry_date':      u.get('created_at', ''),
                'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0)
            })

        return jsonify({
            'success': True,
            'query':   q,
            'results': results,
            'count':   len(results)
        }), 200

    except Exception as e:
        logger.error(f"[SEARCH] Error: {e}")
        return jsonify({'error': 'Search failed'}), 500


# ============================================================
# 7. LOGOUT
# POST /api/admin/logout
# ============================================================

@admin_bp.route('/logout', methods=['POST'])
@builder_required
def logout():
    try:
        from app import supabase
        token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()

        supabase.table('builder_sessions') \
            .delete() \
            .eq('token', token) \
            .execute()

        return jsonify({'success': True, 'message': 'Logged out successfully'}), 200
    except Exception as e:
        logger.error(f"[LOGOUT] Error: {e}")
        return jsonify({'error': 'Logout failed'}), 500