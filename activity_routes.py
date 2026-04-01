"""
activity_routes.py — Track user tool usage, time spent,
virtual tour selections and LifeEcho scenario selections
"""

from flask import Blueprint, request, jsonify
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
activity_bp = Blueprint('activity', __name__, url_prefix='/api/activity')


# ============================================================
# HELPER — resolve user_id from session_id if not provided
# ============================================================

def resolve_user_id(supabase, user_id, session_id):
    """If user_id not sent, try to find it from session_id"""
    if user_id:
        return user_id
    if not session_id:
        return None
    try:
        result = supabase.table('sessions') \
            .select('user_id') \
            .eq('session_id', session_id) \
            .execute()
        if result.data and result.data[0].get('user_id'):
            return result.data[0]['user_id']
    except Exception as e:
        logger.error(f"[RESOLVE_USER] Error: {e}")
    return None


# ============================================================
# 1. LOG TOOL USAGE + TIME SPENT
# POST /api/activity/log
#
# Call this when user LEAVES a tool (you know time spent)
#
# Body:
# {
#   "session_id": "abc123",         required
#   "user_id": "uuid",              optional (if logged in)
#   "client_name": "skyline",       required
#   "tool_name": "room_design",     required — one of:
#                                   "room_design", "virtual_tour", "lifeecho"
#   "time_spent_seconds": 120       required
# }
# ============================================================

@activity_bp.route('/log', methods=['POST', 'OPTIONS'])
def log_activity():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from app import supabase

        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        # ── Validate required fields ────────────────────────
        session_id  = data.get('session_id', '').strip()
        client_name = data.get('client_name', '').strip()
        tool_name   = data.get('tool_name', '').strip()
        time_spent  = data.get('time_spent_seconds', 0)
        user_id     = data.get('user_id', '').strip() or None

        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400
        if not client_name:
            return jsonify({'error': 'client_name is required'}), 400
        if not tool_name:
            return jsonify({'error': 'tool_name is required'}), 400

        valid_tools = ['room_design', 'virtual_tour', 'lifeecho']
        if tool_name not in valid_tools:
            return jsonify({
                'error': f'Invalid tool_name. Must be one of: {", ".join(valid_tools)}'
            }), 400

        if not isinstance(time_spent, (int, float)) or time_spent < 0:
            return jsonify({'error': 'time_spent_seconds must be a positive number'}), 400

        # ── Resolve user_id from session if not provided ────
        resolved_user_id = resolve_user_id(supabase, user_id, session_id)

        # ── Insert activity log ─────────────────────────────
        insert_data = {
            'session_id': session_id,
            'client_name': client_name,
            'tool_name': tool_name,
            'time_spent_seconds': int(time_spent),
            'updated_at': datetime.now(timezone.utc).isoformat()
        }

        if resolved_user_id:
            insert_data['user_id'] = resolved_user_id

        result = supabase.table('user_activity_logs') \
            .insert(insert_data) \
            .execute()

        logger.info(f"[ACTIVITY LOG] tool={tool_name} time={time_spent}s session={session_id}")

        return jsonify({
            'success': True,
            'message': 'Activity logged successfully',
            'data': {
                'tool_name': tool_name,
                'time_spent_seconds': int(time_spent),
                'session_id': session_id,
                'user_id': resolved_user_id
            }
        }), 200

    except Exception as e:
        logger.error(f"[ACTIVITY LOG ERROR] {e}")
        return jsonify({'error': 'Failed to log activity', 'details': str(e)}), 500


# ============================================================
# 2. LOG TOOL SELECTION (Virtual Tour place / LifeEcho scenario)
# POST /api/activity/selection
#
# Body for Virtual Tour:
# {
#   "session_id": "abc123",
#   "user_id": "uuid",              optional
#   "client_name": "skyline",
#   "tool_name": "virtual_tour",
#   "vt_category": "dining",
#   "vt_place_name": "Nando's JBR",
#   "vt_place_id": "ChIJ..."
# }
#
# Body for LifeEcho (pre-generated scenario):
# {
#   "session_id": "abc123",
#   "user_id": "uuid",              optional
#   "client_name": "skyline",
#   "tool_name": "lifeecho",
#   "lifeecho_scenario_id": 5,
#   "lifeecho_scenario_title": "School Run Without the Morning Rush",
#   "lifeecho_is_custom": false
# }
#
# Body for LifeEcho (custom scenario):
# {
#   "session_id": "abc123",
#   "user_id": "uuid",              optional
#   "client_name": "skyline",
#   "tool_name": "lifeecho",
#   "lifeecho_is_custom": true,
#   "lifeecho_custom_text": "What if I need to reach airport at 4am?"
# }
# ============================================================

@activity_bp.route('/selection', methods=['POST', 'OPTIONS'])
def log_selection():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        from app import supabase

        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON body required'}), 400

        # ── Validate required fields ────────────────────────
        session_id  = data.get('session_id', '').strip()
        client_name = data.get('client_name', '').strip()
        tool_name   = data.get('tool_name', '').strip()
        user_id     = data.get('user_id', '').strip() or None

        if not session_id:
            return jsonify({'error': 'session_id is required'}), 400
        if not client_name:
            return jsonify({'error': 'client_name is required'}), 400
        if not tool_name:
            return jsonify({'error': 'tool_name is required'}), 400

        valid_tools = ['virtual_tour', 'lifeecho']
        if tool_name not in valid_tools:
            return jsonify({
                'error': f'Invalid tool_name. Must be one of: {", ".join(valid_tools)}'
            }), 400

        # ── Resolve user_id from session if not provided ────
        resolved_user_id = resolve_user_id(supabase, user_id, session_id)

        # ── Build insert data based on tool ─────────────────
        insert_data = {
            'session_id': session_id,
            'client_name': client_name,
            'tool_name': tool_name
        }

        if resolved_user_id:
            insert_data['user_id'] = resolved_user_id

        # Virtual Tour specific fields
        
        if tool_name == 'virtual_tour':
            vt_category   = data.get('vt_category', '').strip()
            vt_place_name = data.get('vt_place_name', '').strip()
            vt_place_id   = data.get('vt_place_id', '').strip()
            vt_photo_url  = data.get('vt_photo_url', '').strip()
            vt_distance   = data.get('vt_distance')
            vt_rating     = data.get('vt_rating')

            if not vt_category:
                return jsonify({'error': 'vt_category is required for virtual_tour'}), 400

            insert_data['vt_category']   = vt_category
            insert_data['vt_place_name'] = vt_place_name or None
            insert_data['vt_place_id']   = vt_place_id or None
            insert_data['vt_photo_url']  = vt_photo_url or None
            insert_data['vt_distance']   = vt_distance or None
            insert_data['vt_rating']     = vt_rating or None

            logger.info(f"[SELECTION] virtual_tour category={vt_category} place={vt_place_name} session={session_id}")

        # LifeEcho specific fields
        elif tool_name == 'lifeecho':
            is_custom   = data.get('lifeecho_is_custom', False)
            custom_text = data.get('lifeecho_custom_text', '').strip()
            scenario_id = data.get('lifeecho_scenario_id')
            scenario_title = data.get('lifeecho_scenario_title', '').strip()

            insert_data['lifeecho_is_custom'] = is_custom

            if is_custom:
                if not custom_text:
                    return jsonify({'error': 'lifeecho_custom_text is required when lifeecho_is_custom is true'}), 400
                insert_data['lifeecho_custom_text'] = custom_text
            else:
                if not scenario_id:
                    return jsonify({'error': 'lifeecho_scenario_id is required for pre-generated scenarios'}), 400
                insert_data['lifeecho_scenario_id']    = scenario_id
                insert_data['lifeecho_scenario_title'] = scenario_title or None
                insert_data['lifeecho_scenario_icon']  = data.get('lifeecho_scenario_icon', 'clock')

            logger.info(f"[SELECTION] lifeecho is_custom={is_custom} scenario_id={scenario_id} session={session_id}")

        # ── Insert selection ────────────────────────────────
        supabase.table('user_tool_selections') \
            .insert(insert_data) \
            .execute()

        return jsonify({
            'success': True,
            'message': 'Selection logged successfully',
            'data': insert_data
        }), 200

    except Exception as e:
        logger.error(f"[SELECTION ERROR] {e}")
        return jsonify({'error': 'Failed to log selection', 'details': str(e)}), 500


# ============================================================
# 3. HEALTH CHECK
# GET /api/activity/health
# ============================================================

@activity_bp.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'healthy',
        'module': 'activity_tracker',
        'endpoints': [
            'POST /api/activity/log       — log tool usage + time spent',
            'POST /api/activity/selection — log virtual tour / lifeecho selection'
        ]
    }), 200