

# """
# admin_routes.py — PropDesk Builder Admin Dashboard
# Each builder (Skyline, Ellington, etc.) has a separate login.
# Uses: builders table (login), property_sections table (dashboard cards),
#       users table (leads), user_generations table (images).
# """

# from flask import Blueprint, request, jsonify
# from functools import wraps
# import logging
# import os
# from datetime import datetime, timedelta
# import secrets
# import hashlib

# logger = logging.getLogger(__name__)
# admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# # ─── In-memory session store ────────────────────────────────
# builder_sessions = {}

# # ─── Helpers ────────────────────────────────────────────────

# def generate_token():
#     return secrets.token_hex(32)

# def hash_password(password):
#     return hashlib.sha256(password.encode()).hexdigest()

# def verify_token(token):
#     if not token or token not in builder_sessions:
#         return None
#     session = builder_sessions[token]
#     if datetime.now() > session['expires_at']:
#         del builder_sessions[token]
#         return None
#     return session

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
# # Body: { "username": "skyline_admin", "password": "..." }
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

#         builder_sessions[token] = {
#             'username': username,
#             'client_name': builder['client_name'],
#             'company_name': builder.get('company_name', ''),
#             'property_name': builder.get('property_name', ''),
#             'builder_id': builder['id'],
#             'expires_at': datetime.now() + timedelta(hours=24)
#         }

#         logger.info(f"[LOGIN] Success: {username} ({builder['client_name']})")

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
# # Returns: property section cards with lead counts
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
# # section param is optional — omit to get all leads
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
# # 4. LEAD DETAILS
# # GET /api/admin/leads/<user_id>
# # Returns full user info + all generated images
# # ============================================================

# @admin_bp.route('/leads/<user_id>', methods=['GET'])
# @builder_required
# def get_lead_details(user_id):
#     try:
#         from app import supabase

#         client_name = request.builder['client_name']

#         user_result = supabase.table('users') \
#             .select('*') \
#             .eq('id', user_id) \
#             .execute()

#         if not user_result.data:
#             return jsonify({'error': 'Lead not found'}), 404

#         u = user_result.data[0]

#         # Security: builder can only see their own leads
#         if u.get('client_name') != client_name:
#             return jsonify({'error': 'Unauthorized'}), 403

#         gens_result = supabase.table('user_generations') \
#             .select('*') \
#             .eq('user_id', user_id) \
#             .order('created_at', desc=True) \
#             .execute()

#         images = []
#         for g in (gens_result.data or []):
#             images.append({
#                 'id': g.get('generation_id', g.get('id')),
#                 'image_url': g.get('image_url', ''),
#                 'room_type': g.get('room_type', 'N/A'),
#                 'style': g.get('style', 'N/A'),
#                 'created_at': g.get('created_at', ''),
#                 'downloaded': g.get('downloaded', False),
#                 'download_count': g.get('download_count', 0)
#             })

#         return jsonify({
#             'success': True,
#             'lead': {
#                 'id': u['id'],
#                 'name': u.get('full_name', 'Unknown'),
#                 'phone': f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
#                 'email': u.get('email', 'N/A'),
#                 'registration_date': u.get('created_at', ''),
#                 'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0),
#                 'images': images
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
#         today = datetime.now().date().isoformat()

#         total_leads   = supabase.table('users').select('id', count='exact').eq('client_name', client_name).execute()
#         total_gens    = supabase.table('user_generations').select('id', count='exact').eq('client_name', client_name).execute()
#         today_leads   = supabase.table('users').select('id', count='exact').eq('client_name', client_name).gte('created_at', today).execute()
#         today_gens    = supabase.table('user_generations').select('id', count='exact').eq('client_name', client_name).gte('created_at', today).execute()

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
#         token = request.headers.get('Authorization', '').replace('Bearer ', '').strip()
#         builder_sessions.pop(token, None)
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

        # Save session to Supabase
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
# ============================================================

@admin_bp.route('/leads/<user_id>', methods=['GET'])
@builder_required
def get_lead_details(user_id):
    try:
        from app import supabase
        client_name = request.builder['client_name']

        user_result = supabase.table('users') \
            .select('*') \
            .eq('id', user_id) \
            .execute()

        if not user_result.data:
            return jsonify({'error': 'Lead not found'}), 404

        u = user_result.data[0]

        if u.get('client_name') != client_name:
            return jsonify({'error': 'Unauthorized'}), 403

        sessions_result = supabase.table('sessions') \
            .select('session_id') \
            .eq('user_id', user_id) \
            .execute()

        session_ids = [s['session_id'] for s in (sessions_result.data or [])]

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

        return jsonify({
            'success': True,
            'lead': {
                'id': u['id'],
                'name': u.get('full_name', 'Unknown'),
                'phone': f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
                'email': u.get('email', 'N/A'),
                'registration_date': u.get('created_at', ''),
                'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0),
                'images': images
            }
        }), 200

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
                'total_leads': total_leads.count or 0,
                'total_generations': total_gens.count or 0,
                'today_leads': today_leads.count or 0,
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
                'id': u['id'],
                'name': u.get('full_name', 'Unknown'),
                'phone': f"+{u.get('country_code', '91')} {u.get('phone_number', 'N/A')}",
                'email': u.get('email', 'N/A'),
                'inquiry_date': u.get('created_at', ''),
                'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0)
            })

        return jsonify({
            'success': True,
            'query': q,
            'results': results,
            'count': len(results)
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