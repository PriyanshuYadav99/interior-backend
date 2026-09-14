"""
properties_routes.py — Properties dashboard, AI outreach segments, bulk send.

Covers your flow:
  1-2. GET  /api/admin/properties                       -> property cards (image 1)
  3.   GET  /api/admin/properties/<key>/outreach         -> segment counts + AI message (image 2)
       POST /api/admin/properties/<key>/send-outreach    -> send to every lead in chosen segment(s)
  4.   (leads list itself is admin_routes.py's existing /api/admin/leads?section=<key>, image 3)

Register in app.py:
    from properties_routes import properties_bp
    app.register_blueprint(properties_bp)
"""

from flask import Blueprint, request, jsonify
import logging
import os
import re
import json
from datetime import datetime, timedelta, timezone

from routes.admin_routes import builder_required  # reuse existing auth decorator
from services.outreach_dispatch import dispatch_message

logger = logging.getLogger(__name__)
properties_bp = Blueprint('properties', __name__, url_prefix='/api/admin/properties')

NEW_LEAD_WINDOW_DAYS = 7
INACTIVE_WINDOW_DAYS = 14


# ---------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------

def _parse(ts):
    try:
        return datetime.fromisoformat(ts.replace('Z', '+00:00'))
    except Exception:
        return datetime.min.replace(tzinfo=timezone.utc)


def _get_property(supabase, client_name, section_key):
    result = supabase.table('property_sections') \
        .select('*') \
        .eq('client_name', client_name) \
        .eq('section_key', section_key) \
        .eq('is_active', True) \
        .execute()
    return result.data[0] if result.data else None


def _get_property_leads(supabase, client_name, section_key):
    return supabase.table('users') \
        .select('*') \
        .eq('client_name', client_name) \
        .eq('property_section', section_key) \
        .execute().data or []


def _last_activity_map(supabase, user_ids):
    """{user_id: latest created_at string} from user_activity_logs."""
    if not user_ids:
        return {}
    logs = supabase.table('user_activity_logs') \
        .select('user_id, created_at') \
        .in_('user_id', user_ids) \
        .execute().data or []
    latest = {}
    for l in logs:
        uid, ts = l.get('user_id'), l.get('created_at')
        if not uid or not ts:
            continue
        if uid not in latest or ts > latest[uid]:
            latest[uid] = ts
    return latest


def _segment_leads(leads, activity_map):
    """Hot / New / Inactive buckets. A lead can land in more than one."""
    now = datetime.now(timezone.utc)
    new_cutoff = now - timedelta(days=NEW_LEAD_WINDOW_DAYS)
    inactive_cutoff = now - timedelta(days=INACTIVE_WINDOW_DAYS)

    hot, new, inactive = [], [], []

    for u in leads:
        if u.get('lead_temperature') == 'HOT':
            hot.append(u)

        created_at = u.get('created_at')
        if created_at and _parse(created_at) >= new_cutoff and not u.get('last_contacted_at'):
            new.append(u)

        last_activity = activity_map.get(u['id'])
        activity_dt = _parse(last_activity) if last_activity else None
        if not activity_dt or activity_dt < inactive_cutoff:
            inactive.append(u)

    return hot, new, inactive


def _property_card(supabase, client_name, section):
    key = section['section_key']
    leads = _get_property_leads(supabase, client_name, key)
    activity_map = _last_activity_map(supabase, [u['id'] for u in leads])
    hot, new, inactive = _segment_leads(leads, activity_map)

    return {
        'id': key,
        'name': section.get('section_name'),
        'location': section.get('location', ''),
        'image_url': section.get('image_url', ''),
        'type': section.get('property_type'),
        'new_leads': len(new),
        'hot_leads': len(hot),
        'total_leads': len(leads),
    }


def _generate_action_list(card, groq_client):
    """5-point AI action list shown on each property card (image 1)."""
    prompt = f"""You are a real estate sales operations assistant.
Property: {card['name']}
Hot leads: {card['hot_leads']}
New leads: {card['new_leads']}
Total leads: {card['total_leads']}

Generate exactly 5 short, punchy action items (5-8 words each) telling the
sales team what to do next for this property. Mix urgency (hot leads),
follow-up (new leads), and general strategy. Return ONLY a JSON array of
5 strings, nothing else."""
    try:
        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=500,
            reasoning_effort="low"
        )
        text = completion.choices[0].message.content.strip()
        match = re.search(r'\[.*\]', text, re.DOTALL)
        return json.loads(match.group()) if match else []
    except Exception as e:
        logger.error(f"[ACTION LIST] {e}")
        return [
            f"Contact {card['hot_leads']} hot leads immediately",
            f"Follow up with {card['new_leads']} new leads",
            "Match leads with preferred unit types",
            "Schedule property/virtual tours",
            "Launch personalized AI outreach"
        ]


# ---------------------------------------------------------------
# 1-2. LIST PROPERTIES  →  GET /api/admin/properties
# ---------------------------------------------------------------

@properties_bp.route('', methods=['GET'])
@builder_required
def list_properties():
    try:
        from app import supabase
        from groq import Groq
        groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

        client_name = request.builder['client_name']

        sections = supabase.table('property_sections') \
            .select('*') \
            .eq('client_name', client_name) \
            .eq('is_active', True) \
            .order('display_order') \
            .execute().data or []

        properties = []
        for s in sections:
            card = _property_card(supabase, client_name, s)
            card['ai_action_list'] = _generate_action_list(card, groq_client)
            properties.append(card)

        return jsonify({'success': True, 'properties': properties}), 200

    except Exception as e:
        logger.error(f"[LIST PROPERTIES] {e}")
        return jsonify({'error': 'Failed to load properties'}), 500


# ---------------------------------------------------------------
# 3a. OUTREACH PREVIEW →  GET /api/admin/properties/<key>/outreach?channel=sms
# ---------------------------------------------------------------

@properties_bp.route('/<section_key>/outreach', methods=['GET'])
@builder_required
def get_outreach_preview(section_key):
    try:
        from app import supabase
        from groq import Groq
        groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

        client_name = request.builder['client_name']
        section = _get_property(supabase, client_name, section_key)
        if not section:
            return jsonify({'error': 'Property not found'}), 404

        leads = _get_property_leads(supabase, client_name, section_key)
        activity_map = _last_activity_map(supabase, [u['id'] for u in leads])
        hot, new, inactive = _segment_leads(leads, activity_map)

        channel = request.args.get('channel', 'sms')  # sms | whatsapp | email

        prompt = f"""Write a short, warm outreach message template from a real estate
sales agent for the property "{section.get('section_name')}", to be sent via {channel}.

Use merge placeholders exactly like {{{{First Name}}}} and {{{{Unit Type}}}}.
Mention the property has options that match the lead's interest.
End with a soft call-to-action to arrange a viewing or share more details.
Keep it under 60 words. Return ONLY the message text, nothing else."""

        completion = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=450,
            reasoning_effort="low"
        )
        message = completion.choices[0].message.content.strip().strip('"')

        return jsonify({
            'success': True,
            'property': section.get('section_name'),
            'segments': {
                'hot_leads':      {'count': len(hot), 'label': 'High intent leads, ready for immediate follow-up.'},
                'new_leads':      {'count': len(new), 'label': 'Recently generated leads, not yet contacted.'},
                'inactive_leads': {'count': len(inactive), 'label': 'No recent engagement, re-engage with AI.'}
            },
            'channel': channel,
            'message': message
        }), 200

    except Exception as e:
        logger.error(f"[OUTREACH PREVIEW] {e}")
        return jsonify({'error': 'Failed to build outreach preview'}), 500


# ---------------------------------------------------------------
# 3b. SEND BULK OUTREACH → POST /api/admin/properties/<key>/send-outreach
# body: { "segments": ["hot","new"], "channel": "sms", "message": "Hi {{First Name}}..." }
# ---------------------------------------------------------------

@properties_bp.route('/<section_key>/send-outreach', methods=['POST'])
@builder_required
def send_bulk_outreach(section_key):
    try:
        from app import supabase

        data = request.get_json() or {}
        segments = data.get('segments', [])
        channel = data.get('channel', 'sms')
        message_template = data.get('message', '')

        if not segments or not message_template:
            return jsonify({'error': 'segments and message are required'}), 400

        client_name = request.builder['client_name']
        section = _get_property(supabase, client_name, section_key)
        if not section:
            return jsonify({'error': 'Property not found'}), 404

        leads = _get_property_leads(supabase, client_name, section_key)
        activity_map = _last_activity_map(supabase, [u['id'] for u in leads])
        hot, new, inactive = _segment_leads(leads, activity_map)

        bucket_map = {'hot': hot, 'new': new, 'inactive': inactive}
        seen_ids, targets = set(), []
        for seg in segments:
            for u in bucket_map.get(seg, []):
                if u['id'] not in seen_ids:
                    seen_ids.add(u['id'])
                    targets.append(u)

        sent, failed = 0, 0
        for u in targets:
            first_name = (u.get('full_name') or 'there').split(' ')[0]
            personalized = message_template \
                .replace('{{First Name}}', first_name) \
                .replace('{{Unit Type}}', u.get('property_section', section_key))

            ok, err = dispatch_message(u, channel, personalized)

            supabase.table('outreach_logs').insert({
                'user_id': u['id'],
                'client_name': client_name,
                'property_section': section_key,
                'channel': channel,
                'message': personalized,
                'segment': ','.join(segments),
                'status': 'sent' if ok else 'failed',
                'error': err
            }).execute()

            if ok:
                sent += 1
                supabase.table('users').update({
                    'last_contacted_at': datetime.now(timezone.utc).isoformat()
                }).eq('id', u['id']).execute()
            else:
                failed += 1

        return jsonify({
            'success': True,
            'targeted': len(targets),
            'sent': sent,
            'failed': failed
        }), 200

    except Exception as e:
        logger.error(f"[SEND BULK OUTREACH] {e}")
        return jsonify({'error': 'Failed to send outreach', 'details': str(e)}), 500


# ---------------------------------------------------------------
# Optional: manually refresh AI temperature scores for a property
# (also a good candidate to call from services/scheduler.py on a timer)
# ---------------------------------------------------------------

@properties_bp.route('/<section_key>/refresh-scores', methods=['POST'])
@builder_required
def refresh_scores(section_key):
    try:
        from app import supabase
        from routes.ai_routes import refresh_lead_temperature

        client_name = request.builder['client_name']
        leads = _get_property_leads(supabase, client_name, section_key)

        updated = sum(1 for u in leads if refresh_lead_temperature(u['id'], supabase))

        return jsonify({'success': True, 'updated': updated, 'total': len(leads)}), 200

    except Exception as e:
        logger.error(f"[REFRESH SCORES] {e}")
        return jsonify({'error': 'Failed to refresh scores'}), 500