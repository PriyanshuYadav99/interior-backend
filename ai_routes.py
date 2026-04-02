"""
ai_routes.py — AI-powered Lead Intelligence + WhatsApp Suggestion
Using Groq API
"""

from flask import Blueprint, request, jsonify
import os
import logging
from groq import Groq

logger = logging.getLogger(__name__)
ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

client = Groq(api_key=os.getenv('GROQ_API_KEY'))


def build_lead_prompt(lead_data):
    """Build prompt from lead data"""

    name = lead_data.get('name', 'Unknown')
    
    # Images / designs generated
    images = lead_data.get('images', [])
    design_styles = list({img['style'] for img in images if img.get('style')})
    room_types = list({img['room_type'] for img in images if img.get('room_type')})

    # Virtual tour
    vt = lead_data.get('virtual_tour', {})
    categories = vt.get('categories_explored', [])
    places = [p['place_name'] for p in vt.get('places_viewed', []) if p.get('place_name')]

    # LifeEcho
    le = lead_data.get('lifeecho', {})
    scenarios = [s['scenario_title'] for s in le.get('scenarios', []) if s.get('scenario_title')]

    # Tools used
    tools = [t['tool'] for t in lead_data.get('tools_used', [])]
    time_spent = lead_data.get('total_time_spent_minutes', 0)

    prompt = f"""
You are a real estate sales assistant. Analyze this lead's behavior and generate insights.

LEAD DATA:
- Name: {name}
- Total time spent: {time_spent} minutes
- Tools used: {', '.join(tools) if tools else 'None'}
- AI Design styles explored: {', '.join(design_styles) if design_styles else 'None'}
- Room types designed: {', '.join(room_types) if room_types else 'None'}
- Virtual tour categories: {', '.join(categories) if categories else 'None'}
- Places viewed in virtual tour: {', '.join(places) if places else 'None'}
- LifeEcho scenarios selected: {', '.join(scenarios) if scenarios else 'None'}

Generate TWO things:

1. LEAD_INTELLIGENCE: 5-6 bullet points about what this lead is interested in, what to highlight when contacting them, and how to convert them. Be specific based on their activity.

2. WHATSAPP_MESSAGE: A personalized WhatsApp message from the sales agent to this lead. Make it friendly, reference their specific activity (designs, places, scenarios), and end with a soft call to action. Keep it under 150 words.

Respond in this exact JSON format:
{{
    "lead_intelligence": [
        "bullet point 1",
        "bullet point 2",
        "bullet point 3",
        "bullet point 4",
        "bullet point 5"
    ],
    "whatsapp_message": "message here"
}}
"""
    return prompt


@ai_bp.route('/lead-intelligence/<user_id>', methods=['GET'])
def get_lead_intelligence(user_id):
    try:
        from app import supabase

        # ── Fetch user ──────────────────────────────────────
        user_result = supabase.table('users') \
            .select('*') \
            .eq('id', user_id) \
            .execute()

        if not user_result.data:
            return jsonify({'error': 'Lead not found'}), 404

        u = user_result.data[0]

        # ── Fetch images ────────────────────────────────────
        gens_result = supabase.table('user_generations') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()

        images = []
        for g in (gens_result.data or []):
            images.append({
                'style': g.get('style'),
                'room_type': g.get('room_type')
            })

        # ── Fetch virtual tour ──────────────────────────────
        vt_result = supabase.table('user_tool_selections') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('tool_name', 'virtual_tour') \
            .execute()

        places_viewed = []
        categories = set()
        for v in (vt_result.data or []):
            if v.get('vt_category'):
                categories.add(v['vt_category'])
            places_viewed.append({
                'place_name': v.get('vt_place_name'),
                'category': v.get('vt_category')
            })

        # ── Fetch lifeecho ──────────────────────────────────
        le_result = supabase.table('user_tool_selections') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('tool_name', 'lifeecho') \
            .execute()

        scenarios = []
        for l in (le_result.data or []):
            if l.get('lifeecho_scenario_title'):
                scenarios.append({
                    'scenario_title': l['lifeecho_scenario_title']
                })

        # ── Fetch activity ──────────────────────────────────
        activity_result = supabase.table('user_activity_logs') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()

        tools_used = []
        total_time = 0
        for a in (activity_result.data or []):
            tools_used.append({'tool': a.get('tool_name')})
            total_time += a.get('time_spent_seconds', 0) or 0

        # ── Build lead data ─────────────────────────────────
        lead_data = {
            'name': u.get('full_name', 'Unknown'),
            'images': images,
            'virtual_tour': {
                'categories_explored': list(categories),
                'places_viewed': places_viewed
            },
            'lifeecho': {
                'scenarios': scenarios
            },
            'tools_used': tools_used,
            'total_time_spent_minutes': round(total_time / 60, 1)
        }

        # ── Call Groq ───────────────────────────────────────
        prompt = build_lead_prompt(lead_data)

        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )

        response_text = completion.choices[0].message.content

        # ── Parse JSON response ─────────────────────────────
        import json
        import re

        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            return jsonify({'error': 'Failed to parse AI response'}), 500

        ai_data = json.loads(json_match.group())

        return jsonify({
            'success': True,
            'user_id': user_id,
            'lead_intelligence': ai_data.get('lead_intelligence', []),
            'whatsapp_message': ai_data.get('whatsapp_message', '')
        }), 200

    except Exception as e:
        logger.error(f"[AI INTELLIGENCE ERROR] {e}")
        return jsonify({'error': 'Failed to generate intelligence', 'details': str(e)}), 500


@ai_bp.route('/regenerate-whatsapp/<user_id>', methods=['GET'])
def regenerate_whatsapp(user_id):
    """Regenerate only the WhatsApp message with a different tone"""
    try:
        from app import supabase

        user_result = supabase.table('users') \
            .select('*') \
            .eq('id', user_id) \
            .execute()

        if not user_result.data:
            return jsonify({'error': 'Lead not found'}), 404

        u = user_result.data[0]

        gens_result = supabase.table('user_generations') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()

        images = [{'style': g.get('style'), 'room_type': g.get('room_type')} for g in (gens_result.data or [])]

        vt_result = supabase.table('user_tool_selections') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('tool_name', 'virtual_tour') \
            .execute()

        places = [v.get('vt_place_name') for v in (vt_result.data or []) if v.get('vt_place_name')]

        le_result = supabase.table('user_tool_selections') \
            .select('*') \
            .eq('user_id', user_id) \
            .eq('tool_name', 'lifeecho') \
            .execute()

        scenarios = [l.get('lifeecho_scenario_title') for l in (le_result.data or []) if l.get('lifeecho_scenario_title')]

        design_styles = list({img['style'] for img in images if img.get('style')})

        prompt = f"""
Write a new friendly WhatsApp message from a real estate sales agent to {u.get('full_name', 'the customer')}.

Their activity:
- Design styles they liked: {', '.join(design_styles) if design_styles else 'None'}
- Places they explored: {', '.join(places) if places else 'None'}
- Life scenarios they selected: {', '.join(scenarios) if scenarios else 'None'}

Make it different from a typical message. Be warm, specific, and end with a soft call to action.
Keep it under 150 words. Return only the message text, nothing else.
"""

        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=300
        )

        message = completion.choices[0].message.content.strip()

        return jsonify({
            'success': True,
            'whatsapp_message': message
        }), 200

    except Exception as e:
        logger.error(f"[REGENERATE WHATSAPP ERROR] {e}")
        return jsonify({'error': 'Failed to regenerate message', 'details': str(e)}), 500