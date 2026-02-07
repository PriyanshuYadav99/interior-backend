"""
admin_routes.py - Multi-Builder Admin Dashboard
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import logging
import os
from datetime import datetime, timedelta
import secrets
import hashlib

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# ============================================================
# CONFIGURATION
# ============================================================

SUPER_ADMIN_USERNAME = os.getenv('SUPER_ADMIN_USERNAME', 'superadmin')
SUPER_ADMIN_PASSWORD = os.getenv('SUPER_ADMIN_PASSWORD', 'super123')

admin_sessions = {}
builder_sessions = {}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def generate_token():
    return secrets.token_hex(32)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_token(token, session_store):
    if not token or token not in session_store:
        return None
    session = session_store[token]
    if datetime.now() > session['expires_at']:
        del session_store[token]
        return None
    return session

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        session = verify_token(token, admin_sessions)
        if session:
            request.user = {'type': 'superadmin', 'username': session['username']}
            return f(*args, **kwargs)
        
        session = verify_token(token, builder_sessions)
        if session:
            request.user = {
                'type': 'builder',
                'client_name': session['client_name'],
                'username': session['username'],
                'company_name': session.get('company_name', '')
            }
            return f(*args, **kwargs)
        
        return jsonify({'error': 'Unauthorized'}), 401
    return decorated

# ============================================================
# 1. AUTHENTICATION
# ============================================================

@admin_bp.route('/login', methods=['POST', 'OPTIONS'])
def admin_login():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        if username == SUPER_ADMIN_USERNAME and password == SUPER_ADMIN_PASSWORD:
            token = generate_token()
            admin_sessions[token] = {
                'username': username,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(hours=24)
            }
            
            logger.info(f"[SUPER ADMIN] Login: {username}")
            
            return jsonify({
                'success': True,
                'token': token,
                'user_type': 'superadmin',
                'username': username
            }), 200
        
        return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        logger.error(f"[ADMIN LOGIN] Error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@admin_bp.route('/builder/login', methods=['POST', 'OPTIONS'])
def builder_login():
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        from app import supabase
        
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        password_hash = hash_password(password)
        
        result = supabase.table('builders')\
            .select('*')\
            .eq('username', username)\
            .eq('password_hash', password_hash)\
            .eq('is_active', True)\
            .execute()
        
        if not result.data:
            logger.warning(f"[BUILDER LOGIN] Failed: {username}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        builder = result.data[0]
        token = generate_token()
        builder_sessions[token] = {
            'username': username,
            'client_name': builder['client_name'],
            'company_name': builder['company_name'],
            'builder_id': builder['id'],
            'created_at': datetime.now(),
            'expires_at': datetime.now() + timedelta(hours=24)
        }
        
        logger.info(f"[BUILDER LOGIN] Success: {username} ({builder['client_name']})")
        
        return jsonify({
            'success': True,
            'token': token,
            'user_type': 'builder',
            'username': username,
            'client_name': builder['client_name'],
            'company_name': builder['company_name'],
            'property_name': builder['property_name']
        }), 200
    
    except Exception as e:
        logger.error(f"[BUILDER LOGIN] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Login failed'}), 500


# ============================================================
# 2. DASHBOARD
# ============================================================

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard():
    try:
        from app import supabase
        
        user = request.user
        
        if user['type'] == 'superadmin':
            builders_result = supabase.table('builders')\
                .select('*')\
                .eq('is_active', True)\
                .order('created_at')\
                .execute()
            
            properties = []
            for builder in builders_result.data:
                leads_count = supabase.table('users')\
                    .select('id', count='exact')\
                    .eq('client_name', builder['client_name'])\
                    .execute()
                
                properties.append({
                    'id': builder['client_name'],
                    'name': builder['property_name'],
                    'type': builder['property_type'],
                    'company_name': builder['company_name'],
                    'leads': leads_count.count or 0
                })
        else:
            client_name = user['client_name']
            
            builder_result = supabase.table('builders')\
                .select('*')\
                .eq('client_name', client_name)\
                .execute()
            
            if not builder_result.data:
                return jsonify({'error': 'Builder not found'}), 404
            
            builder = builder_result.data[0]
            
            leads_count = supabase.table('users')\
                .select('id', count='exact')\
                .eq('client_name', client_name)\
                .execute()
            
            properties = [{
                'id': builder['client_name'],
                'name': builder['property_name'],
                'type': builder['property_type'],
                'company_name': builder['company_name'],
                'leads': leads_count.count or 0
            }]
        
        return jsonify({
            'success': True,
            'properties': properties,
            'user_type': user['type']
        }), 200
    
    except Exception as e:
        logger.error(f"[DASHBOARD] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to load dashboard'}), 500


# ============================================================
# 3. PROPERTY LEADS
# ============================================================

@admin_bp.route('/property/<property_id>/leads', methods=['GET'])
@admin_required
def get_property_leads(property_id):
    try:
        from app import supabase
        
        user = request.user
        
        if user['type'] == 'builder' and user['client_name'] != property_id:
            return jsonify({'error': 'Unauthorized'}), 403
        
        builder_result = supabase.table('builders')\
            .select('property_name, company_name')\
            .eq('client_name', property_id)\
            .execute()
        
        if not builder_result.data:
            return jsonify({'error': 'Property not found'}), 404
        
        property_info = builder_result.data[0]
        
        users_result = supabase.table('users')\
            .select('*')\
            .eq('client_name', property_id)\
            .order('created_at', desc=True)\
            .execute()
        
        leads = []
        for user_data in users_result.data:
            leads.append({
                'id': user_data['id'],
                'name': user_data.get('full_name', 'Unknown'),
                'phone': f"+{user_data.get('country_code', '91')} {user_data.get('phone_number', 'N/A')}",
                'email': user_data.get('email', 'N/A'),
                'inquiry_date': user_data.get('created_at', ''),
                'total_generations': user_data.get('total_generations', 0)
            })
        
        return jsonify({
            'success': True,
            'property_id': property_id,
            'property_name': property_info['property_name'],
            'leads': leads,
            'total_leads': len(leads)
        }), 200
    
    except Exception as e:
        logger.error(f"[PROPERTY LEADS] Error: {e}")
        return jsonify({'error': 'Failed to load leads'}), 500


# ============================================================
# 4. LEAD DETAILS
# ============================================================

@admin_bp.route('/lead/<user_id>', methods=['GET'])
@admin_required
def get_lead_details(user_id):
    try:
        from app import supabase
        
        user_result = supabase.table('users')\
            .select('*')\
            .eq('id', user_id)\
            .execute()
        
        if not user_result.data:
            return jsonify({'error': 'Lead not found'}), 404
        
        user_data = user_result.data[0]
        
        if request.user['type'] == 'builder':
            if user_data.get('client_name') != request.user['client_name']:
                return jsonify({'error': 'Unauthorized'}), 403
        
        generations_result = supabase.table('user_generations')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('created_at', desc=True)\
            .execute()
        
        generations = []
        for gen in generations_result.data:
            generations.append({
                'id': gen.get('generation_id', gen.get('id')),
                'image_url': gen.get('image_url', ''),
                'room_type': gen.get('room_type', 'N/A'),
                'style': gen.get('style', 'N/A'),
                'created_at': gen.get('created_at', ''),
                'downloaded': gen.get('downloaded', False),
                'download_count': gen.get('download_count', 0)
            })
        
        lead_details = {
            'id': user_data['id'],
            'name': user_data.get('full_name', 'Unknown'),
            'phone': f"+{user_data.get('country_code', '91')} {user_data.get('phone_number', 'N/A')}",
            'email': user_data.get('email', 'N/A'),
            'registration_date': user_data.get('created_at', ''),
            'total_generations': user_data.get('total_generations', 0),
            'ip_address': user_data.get('ip_address', 'N/A'),
            'generations': generations
        }
        
        return jsonify({
            'success': True,
            'lead': lead_details
        }), 200
    
    except Exception as e:
        logger.error(f"[LEAD DETAILS] Error: {e}")
        return jsonify({'error': 'Failed to load lead details'}), 500


# ============================================================
# 5. ANALYTICS
# ============================================================

@admin_bp.route('/analytics', methods=['GET'])
@admin_required
def get_analytics():
    try:
        from app import supabase
        
        user = request.user
        today = datetime.now().date().isoformat()
        
        if user['type'] == 'builder':
            client_name = user['client_name']
            
            total_users = supabase.table('users')\
                .select('id', count='exact')\
                .eq('client_name', client_name)\
                .execute()
            
            total_gens = supabase.table('user_generations')\
                .select('id', count='exact')\
                .eq('client_name', client_name)\
                .execute()
            
            today_users = supabase.table('users')\
                .select('id', count='exact')\
                .eq('client_name', client_name)\
                .gte('created_at', today)\
                .execute()
            
            today_gens = supabase.table('user_generations')\
                .select('id', count='exact')\
                .eq('client_name', client_name)\
                .gte('created_at', today)\
                .execute()
        else:
            total_users = supabase.table('users').select('id', count='exact').execute()
            total_gens = supabase.table('user_generations').select('id', count='exact').execute()
            today_users = supabase.table('users').select('id', count='exact').gte('created_at', today).execute()
            today_gens = supabase.table('user_generations').select('id', count='exact').gte('created_at', today).execute()
        
        return jsonify({
            'success': True,
            'analytics': {
                'total_leads': total_users.count or 0,
                'total_generations': total_gens.count or 0,
                'today_leads': today_users.count or 0,
                'today_generations': today_gens.count or 0
            }
        }), 200
    
    except Exception as e:
        logger.error(f"[ANALYTICS] Error: {e}")
        return jsonify({'error': 'Failed to load analytics'}), 500


# ============================================================
# 6. SEARCH
# ============================================================

@admin_bp.route('/search', methods=['GET'])
@admin_required
def search_leads():
    try:
        from app import supabase
        
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query required'}), 400
        
        user = request.user
        search_query = supabase.table('users').select('*')
        
        if user['type'] == 'builder':
            search_query = search_query.eq('client_name', user['client_name'])
        
        search_query = search_query.or_(
            f"full_name.ilike.%{query}%,email.ilike.%{query}%,phone_number.ilike.%{query}%"
        ).order('created_at', desc=True)
        
        results_data = search_query.execute()
        
        results = []
        for user_data in (results_data.data or []):
            results.append({
                'id': user_data['id'],
                'name': user_data.get('full_name', 'Unknown'),
                'phone': f"+{user_data.get('country_code', '91')} {user_data.get('phone_number', 'N/A')}",
                'email': user_data.get('email', 'N/A'),
                'registration_date': user_data.get('created_at', ''),
                'total_generations': user_data.get('total_generations', 0)
            })
        
        return jsonify({
            'success': True,
            'query': query,
            'results': results,
            'count': len(results)
        }), 200
    
    except Exception as e:
        logger.error(f"[SEARCH] Error: {e}")
        return jsonify({'error': 'Search failed'}), 500


# ============================================================
# 7. LOGOUT
# ============================================================

@admin_bp.route('/logout', methods=['POST'])
@admin_required
def logout():
    try:
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if token in admin_sessions:
            del admin_sessions[token]
        elif token in builder_sessions:
            del builder_sessions[token]
        
        return jsonify({'success': True, 'message': 'Logged out'}), 200
    
    except Exception as e:
        logger.error(f"[LOGOUT] Error: {e}")
        return jsonify({'error': 'Logout failed'}), 500