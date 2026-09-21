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
# 3a. PROPERTY DROPDOWN OPTIONS   (NEW)
# GET /api/admin/property-filter
# ============================================================

@admin_bp.route('/property-filter', methods=['GET'])
@builder_required
def get_property_filter():
    try:
        from app import supabase
        client_name = request.builder['client_name']   # a builder only ever sees ITS OWN properties

        sections = supabase.table('property_sections') \
            .select('section_key, section_name, property_type, display_order') \
            .eq('client_name', client_name) \
            .eq('is_active', True) \
            .order('display_order') \
            .execute().data or []

        # distinct leads per property: interest rows + the legacy users.property_section value
        interests = supabase.table('user_property_interests') \
            .select('user_id, property_section') \
            .eq('client_name', client_name) \
            .execute().data or []
        users = supabase.table('users') \
            .select('id, property_section') \
            .eq('client_name', client_name) \
            .execute().data or []

        leads_by_section = {}
        for r in interests:
            if r.get('user_id') and r.get('property_section'):
                leads_by_section.setdefault(r['property_section'], set()).add(r['user_id'])
        for u in users:
            if u.get('property_section'):
                leads_by_section.setdefault(u['property_section'], set()).add(u['id'])

        options = [{
            'key': s['section_key'],
            'name': s['section_name'],
            'type': s.get('property_type'),
            'leads': len(leads_by_section.get(s['section_key'], ())),
        } for s in sections]

        return jsonify({
            'success': True,
            'total_leads': len(users),   # shown on the "All properties" option
            'options': options,
        }), 200

    except Exception as e:
        logger.error(f"[PROPERTY FILTER] Error: {e}")
        return jsonify({'error': 'Failed to load property filter'}), 500


# ============================================================
# 3b. LEADS LIST   (UPDATED: status filter, pagination, status + intent_score)
# GET /api/admin/leads?section=1bhk&status=hot&page=1&limit=8
#
#   section : property key from /property-filter   (optional; omit = all properties)
#   status  : hot | warm | cold | new              (optional; omit = all leads)
#   page, limit : pagination                       (optional; omit limit = return everything, as before)
# ============================================================

@admin_bp.route('/leads', methods=['GET'])
@builder_required
def get_leads():
    try:
        from app import supabase
        from routes.lead_insights import format_phone

        client_name = request.builder['client_name']
        section = request.args.get('section', '').strip()
        status_filter = request.args.get('status', '').strip().lower()

        def _int_arg(name, default, lo, hi):
            try:
                return min(max(int(request.args.get(name, default)), lo), hi)
            except (TypeError, ValueError):
                return default

        page = _int_arg('page', 1, 1, 100000)
        limit = _int_arg('limit', 0, 0, 100) if request.args.get('limit') else 0

        def _paged(leads_list):
            total = len(leads_list)
            if limit:
                start = (page - 1) * limit
                leads_list = leads_list[start:start + limit]
            return {
                'success': True,
                'section': section or 'all',
                'status': status_filter or 'all',
                'leads': leads_list,
                'total': total,
                'page': page if limit else 1,
                'limit': limit or total,
                'total_pages': (-(-total // limit)) if limit else 1,
            }

        # ── Find which users have an interest matching this section (if filtering) ──
        if section:
            interest_rows = supabase.table('user_property_interests') \
                .select('user_id') \
                .eq('client_name', client_name) \
                .eq('property_section', section) \
                .execute().data or []
            interest_user_ids = {r['user_id'] for r in interest_rows if r.get('user_id')}

            legacy_users = supabase.table('users') \
                .select('id') \
                .eq('client_name', client_name) \
                .eq('property_section', section) \
                .execute().data or []
            legacy_user_ids = {u['id'] for u in legacy_users}

            user_ids = list(interest_user_ids | legacy_user_ids)

            if not user_ids:
                return jsonify(_paged([])), 200

            query = supabase.table('users') \
                .select('*') \
                .eq('client_name', client_name) \
                .in_('id', user_ids) \
                .order('created_at', desc=True)
        else:
            query = supabase.table('users') \
                .select('*') \
                .eq('client_name', client_name) \
                .order('created_at', desc=True)

        result = query.execute()
        users = result.data or []
        user_ids_all = [u['id'] for u in users]

        # ── chip labels: section_key -> property_type ("2bhk" -> "2BHK", "villa" -> "Villa") ──
        type_rows = supabase.table('property_sections') \
            .select('section_key, property_type') \
            .eq('client_name', client_name) \
            .execute().data or []
        type_by_key = {r['section_key']: r.get('property_type') or r['section_key'] for r in type_rows}

        # ── Pull ALL property interests for these users in one go ──
        all_interests = []
        if user_ids_all:
            all_interests = supabase.table('user_property_interests') \
                .select('user_id, property_section') \
                .in_('user_id', user_ids_all) \
                .execute().data or []

        interests_by_user = {}
        for i in all_interests:
            uid = i['user_id']
            sec = i.get('property_section')
            if not sec:
                continue
            interests_by_user.setdefault(uid, set()).add(sec)

        leads = []
        for u in users:
            uid = u['id']
            unit_interests = sorted(interests_by_user.get(uid, set()))
            # Fallback: if no interest rows yet, show the legacy single value so nothing looks empty
            if not unit_interests and u.get('property_section'):
                unit_interests = [u['property_section']]

            temp = (u.get('lead_temperature') or '').lower()
            status = temp if temp in ('hot', 'warm', 'cold') else 'new'
            if status_filter and status != status_filter:
                continue

            leads.append({
                'id': uid,
                'name': u.get('full_name', 'Unknown'),
                'phone': format_phone(u),
                'email': u.get('email', 'N/A'),
                'inquiry_date': u.get('created_at', ''),
                'total_generations': (u.get('total_generations', 0) or 0) + (u.get('pre_registration_generations', 0) or 0),
                'unit_interest': unit_interests,                                          # keys, as before
                'unit_interest_labels': [type_by_key.get(k, k) for k in unit_interests],  # chips: "1BHK", "Villa"
                'status': status.title(),                                                 # Hot / Warm / Cold / New
                'intent_score': u.get('lead_score'),
            })

        return jsonify(_paged(leads)), 200

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
        from routes.lead_insights import build_lead_detail
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

        # ── section_key -> display name (e.g. 2bhk -> "2BR") ──
        secs = supabase.table('property_sections') \
            .select('section_key, section_name') \
            .eq('client_name', client_name) \
            .execute().data or []
        section_names = {s['section_key']: s['section_name'] for s in secs}

        # ── Everything the modal needs (images, tools, insights, messages...) ──
        lead_response = build_lead_detail(
            supabase, u, section_names,
            property_name=request.builder.get('property_name', ''),
            force_ai=request.args.get('refresh') == 'true',
            debug=request.args.get('debug') == 'true',
        )

        # ── YOUR ORIGINAL: Lead Temperature (AI scoring) ────
        temperature_data = None
        if request.args.get('include_temperature', '').lower() == 'true':
            try:
                from routes.ai_routes import build_lead_payload   # was `from ai_routes` (wrong path)
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

                    temperature_prompt = f"""You are an expert Real Estate Sales Analyst AI for PropDeck. Your job is to analyze a prospective buyer's platform activity and categorize their lead temperature (HOT, WARM, or COLD) based on a strict scoring matrix.

You will be provided with a JSON payload of the user's session data.

Evaluate the lead using the following 100-point scoring system:

1. Session Duration (Max 40 points)
   - 7+ minutes = 40 pts
   - 4 to 7 minutes = 30 pts
   - 2 to 4 minutes = 20 pts
   - Less than 1 minute = 10 pts

2. Design Consistency (Max 20 points)
   - 1 unique design style across all generated rooms = 20 pts (High focus)
   - 2 unique design styles = 15 pts (Exploring)
   - 3 or more unique styles = 5 pts (Scattered browsing)

3. Tool Engagement Depth (Max 20 points)
   - Used both 'LifeEcho' and 'Virtual Tour' = 20 pts
   - Used only one of the tools = 10 pts

4. Intent Specificity (Max 20 points)
   - LifeEcho scenarios or Virtual Tour locations include high-intent life events
     (keywords: health, daycare, elderly, school, hospital, accessibility, pets) = 20 pts
   - Scenarios only focus on generic convenience
     (keywords: shopping, market, metro, transport) = 10 pts

Scoring Thresholds:
- HOT:  70 to 100 points
- WARM: 40 to 69 points
- COLD: Less than 40 points

OUTPUT FORMAT:
You must return a valid JSON object with the following structure exactly. Do not include markdown formatting or extra text outside the JSON.
{{
  "score": <integer>,
  "temperature": "<HOT|WARM|COLD>",
  "reasoning": "<1-2 sentences explaining how the score was calculated based on the data>",
  "sales_strategy": "<1-2 sentences giving the sales team actionable advice on how to pitch this specific lead based on their LifeEcho scenarios, Virtual Tour locations, and design choices>"
}}

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

        # Your AI result wins over the saved/fallback score
        if temperature_data:
            lead_response['temperature'] = temperature_data
            if temperature_data.get('score') is not None:
                lead_response['intent_score'] = temperature_data['score']

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
        from routes.lead_insights import format_phone
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
                'phone':             format_phone(u),
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