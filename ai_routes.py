

# """
# ai_routes.py — AI-powered Lead Intelligence + WhatsApp Suggestion + Lead Temperature Scoring
# Using Groq API
# """

# from flask import Blueprint, request, jsonify
# import os
# import logging
# from groq import Groq

# logger = logging.getLogger(__name__)
# ai_bp = Blueprint('ai', __name__, url_prefix='/api/ai')

# client = Groq(api_key=os.getenv('GROQ_API_KEY'))


# def build_lead_prompt(lead_data):
#     """Build prompt from lead data"""

#     name = lead_data.get('name', 'Unknown')
    
#     # Images / designs generated
#     images = lead_data.get('images', [])
#     design_styles = list({img['style'] for img in images if img.get('style')})
#     room_types = list({img['room_type'] for img in images if img.get('room_type')})

#     # Virtual tour
#     vt = lead_data.get('virtual_tour', {})
#     categories = vt.get('categories_explored', [])
#     places = [p['place_name'] for p in vt.get('places_viewed', []) if p.get('place_name')]

#     # LifeEcho
#     le = lead_data.get('lifeecho', {})
#     scenarios = [s['scenario_title'] for s in le.get('scenarios', []) if s.get('scenario_title')]

#     # Tools used
#     tools = [t['tool'] for t in lead_data.get('tools_used', [])]
#     time_spent = lead_data.get('total_time_spent_minutes', 0)

#     prompt = f"""
# You are a real estate sales assistant. Analyze this lead's behavior and generate insights.

# LEAD DATA:
# - Name: {name}
# - Total time spent: {time_spent} minutes
# - Tools used: {', '.join(tools) if tools else 'None'}
# - AI Design styles explored: {', '.join(design_styles) if design_styles else 'None'}
# - Room types designed: {', '.join(room_types) if room_types else 'None'}
# - Virtual tour categories: {', '.join(categories) if categories else 'None'}
# - Places viewed in virtual tour: {', '.join(places) if places else 'None'}
# - LifeEcho scenarios selected: {', '.join(scenarios) if scenarios else 'None'}

# Generate TWO things:

# 1. LEAD_INTELLIGENCE: Exactly 5 bullet points for the sales person.
#    - Each point must be 12-15 words
#    - Focus on actionable sales insights only
#    - Mention specific places, styles, scenarios they explored
#    - Start each with an action word like "Highlight", "Pitch", "Mention", "Emphasize", "Suggest"
#    - Example: "Highlight nearby wellness amenities like spas and gyms they explored"
#    - Example: "Pitch quiet and peaceful properties based on their LifeEcho selections"

# 2. WHATSAPP_MESSAGE: A professional WhatsApp message from sales agent to this lead.
#    - Purpose is only to open a dialogue, not to sell
#    - Reference 2-3 specific things they explored (place names, design styles, scenarios)
#    - Be warm, professional, not salesy
#    - Mentioned that we are attaching the interior images they had generated (this will be part of the Whatsapp messages)
#    - End with one simple open ended question
#    - Between 80-120 words strictly
#    - Also tell if they have any questions, they can ask as a message below.

# Respond in this exact JSON format:
# {{
#     "lead_intelligence": [
#         "short point 1",
#         "short point 2",
#         "short point 3",
#         "short point 4",
#         "short point 5"
#     ],
#     "whatsapp_message": "message here"
# }}
# """
#     return prompt


# def build_lead_payload(user_id, supabase):
#     """
#     Shared helper — fetches all activity data for a user and
#     returns a structured dict ready for the temperature scorer.
#     Reused by both /lead-intelligence and /lead-temperature.
#     """
#     user_result = supabase.table('users') \
#         .select('*') \
#         .eq('id', user_id) \
#         .execute()

#     if not user_result.data:
#         return None, 'Lead not found'

#     u = user_result.data[0]

#     # Generated images
#     gens_result = supabase.table('user_generations') \
#         .select('*') \
#         .eq('user_id', user_id) \
#         .execute()

#     images = [
#         {'style': g.get('style'), 'room_type': g.get('room_type')}
#         for g in (gens_result.data or [])
#     ]

#     # Virtual tour selections
#     vt_result = supabase.table('user_tool_selections') \
#         .select('*') \
#         .eq('user_id', user_id) \
#         .eq('tool_name', 'virtual_tour') \
#         .execute()

#     places_viewed = []
#     categories = set()
#     for v in (vt_result.data or []):
#         if v.get('vt_category'):
#             categories.add(v['vt_category'])
#         places_viewed.append({
#             'place_name': v.get('vt_place_name'),
#             'category':   v.get('vt_category')
#         })

#     # LifeEcho selections
#     le_result = supabase.table('user_tool_selections') \
#         .select('*') \
#         .eq('user_id', user_id) \
#         .eq('tool_name', 'lifeecho') \
#         .execute()

#     scenarios = []
#     for l in (le_result.data or []):
#         entry = {}
#         if l.get('lifeecho_scenario_title'):
#             entry['scenario_title'] = l['lifeecho_scenario_title']
#         if l.get('lifeecho_custom_text'):
#             entry['custom_text'] = l['lifeecho_custom_text']
#         if entry:
#             scenarios.append(entry)

#     # Activity logs
#     activity_result = supabase.table('user_activity_logs') \
#         .select('*') \
#         .eq('user_id', user_id) \
#         .execute()

#     tools_used = []
#     total_time = 0
#     for a in (activity_result.data or []):
#         tools_used.append({'tool': a.get('tool_name')})
#         total_time += a.get('time_spent_seconds', 0) or 0

#     payload = {
#         'name': u.get('full_name', 'Unknown'),
#         'images': images,
#         'virtual_tour': {
#             'categories_explored': list(categories),
#             'places_viewed': places_viewed
#         },
#         'lifeecho': {
#             'scenarios': scenarios
#         },
#         'tools_used': tools_used,
#         'total_time_spent_minutes': round(total_time / 60, 1)
#     }

#     return payload, None


# # ============================================================
# # 1. LEAD INTELLIGENCE
# # GET /api/ai/lead-intelligence/<user_id>
# # ============================================================

# @ai_bp.route('/lead-intelligence/<user_id>', methods=['GET'])
# def get_lead_intelligence(user_id):
#     try:
#         from app import supabase

#         lead_data, error = build_lead_payload(user_id, supabase)
#         if error:
#             return jsonify({'error': error}), 404

#         prompt = build_lead_prompt(lead_data)

#         completion = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.7,
#             max_tokens=1000
#         )

#         response_text = completion.choices[0].message.content

#         import json, re
#         json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
#         if not json_match:
#             return jsonify({'error': 'Failed to parse AI response'}), 500

#         ai_data = json.loads(json_match.group())

#         return jsonify({
#             'success': True,
#             'user_id': user_id,
#             'lead_intelligence': ai_data.get('lead_intelligence', []),
#             'whatsapp_message': ai_data.get('whatsapp_message', '')
#         }), 200

#     except Exception as e:
#         logger.error(f"[AI INTELLIGENCE ERROR] {e}")
#         return jsonify({'error': 'Failed to generate intelligence', 'details': str(e)}), 500


# # ============================================================
# # 2. LEAD TEMPERATURE SCORING
# # GET /api/ai/lead-temperature/<user_id>
# #
# # Returns:
# # {
# #   "success": true,
# #   "user_id": "...",
# #   "score": 80,
# #   "temperature": "HOT",
# #   "reasoning": "...",
# #   "sales_strategy": "..."
# # }
# # ============================================================

# @ai_bp.route('/lead-temperature/<user_id>', methods=['GET'])
# def get_lead_temperature(user_id):
#     try:
#         from app import supabase
#         import json, re

#         # ── Build lead payload ──────────────────────────────
#         lead_data, error = build_lead_payload(user_id, supabase)
#         if error:
#             return jsonify({'error': error}), 404

#         # ── Build temperature scoring prompt ────────────────
#         images          = lead_data.get('images', [])
#         design_styles   = list({img['style'] for img in images if img.get('style')})
#         vt              = lead_data.get('virtual_tour', {})
#         le              = lead_data.get('lifeecho', {})
#         tools_used      = list({t['tool'] for t in lead_data.get('tools_used', []) if t.get('tool')})
#         time_spent_min  = lead_data.get('total_time_spent_minutes', 0)

#         # Flatten scenario text for intent keywords
#         scenario_texts = []
#         for s in le.get('scenarios', []):
#             if s.get('scenario_title'):
#                 scenario_texts.append(s['scenario_title'])
#             if s.get('custom_text'):
#                 scenario_texts.append(s['custom_text'])

#         vt_place_names = [
#             p['place_name'] for p in vt.get('places_viewed', []) if p.get('place_name')
#         ]

#         lead_payload = {
#             "total_time_spent_minutes": time_spent_min,
#             "unique_design_styles": design_styles,
#             "tools_used": tools_used,
#             "lifeecho_scenarios": scenario_texts,
#             "virtual_tour_places": vt_place_names,
#             "virtual_tour_categories": vt.get('categories_explored', [])
#         }

#         temperature_prompt = f"""
# You are an expert Real Estate Sales Analyst AI for PropDeck. Your job is to analyze a prospective buyer's platform activity and categorize their lead temperature (HOT, WARM, or COLD) based on a strict scoring matrix.

# You will be provided with a JSON payload of the user's session data.

# Evaluate the lead using the following 100-point scoring system:

# 1. Session Duration (Max 40 points)
#    - 20+ minutes = 40 pts
#    - 10 to 19 minutes = 30 pts
#    - 3 to 9 minutes = 20 pts
#    - Less than 3 minutes = 10 pts

# 2. Design Consistency (Max 20 points)
#    - 1 unique design style across all generated rooms = 20 pts (High focus)
#    - 2 unique design styles = 10 pts (Exploring)
#    - 3 or more unique styles = 0 pts (Scattered browsing)

# 3. Tool Engagement Depth (Max 20 points)
#    - Used both 'lifeecho' and 'virtual_tour' = 20 pts
#    - Used only one of the tools = 10 pts
#    - Used neither = 0 pts

# 4. Intent Specificity (Max 20 points)
#    - LifeEcho scenarios or Virtual Tour locations include high-intent life events
#      (keywords: health, daycare, elderly, school, hospital, accessibility, pets) = 20 pts
#    - Scenarios only focus on generic convenience
#      (keywords: shopping, market, metro, transport) = 10 pts
#    - No scenarios = 0 pts

# Scoring Thresholds:
# - HOT:  75 to 100 points
# - WARM: 45 to 74 points
# - COLD: Less than 45 points

# OUTPUT FORMAT:
# Return a valid JSON object with exactly this structure. No markdown, no extra text outside the JSON.
# {{
#   "score": <integer>,
#   "temperature": "<HOT|WARM|COLD>",
#   "reasoning": "<1-2 sentences explaining how the score was calculated>",
#   "sales_strategy": "<1-2 sentences giving the sales team actionable advice based on this lead's specific activity>"
# }}

# USER SESSION DATA:
# {json.dumps(lead_payload, indent=2)}
# """

#         # ── Call Groq ───────────────────────────────────────
#         completion = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": temperature_prompt}],
#             temperature=0.3,   # lower temp for deterministic scoring
#             max_tokens=400
#         )

#         response_text = completion.choices[0].message.content.strip()

#         # Strip markdown fences if present
#         clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', response_text, flags=re.DOTALL).strip()

#         json_match = re.search(r'\{.*\}', clean, re.DOTALL)
#         if not json_match:
#             return jsonify({'error': 'Failed to parse AI temperature response'}), 500

#         result = json.loads(json_match.group())

#         return jsonify({
#             'success':        True,
#             'user_id':        user_id,
#             'score':          result.get('score'),
#             'temperature':    result.get('temperature'),
#             'reasoning':      result.get('reasoning', ''),
#             'sales_strategy': result.get('sales_strategy', '')
#         }), 200

#     except Exception as e:
#         logger.error(f"[LEAD TEMPERATURE ERROR] {e}")
#         return jsonify({'error': 'Failed to score lead temperature', 'details': str(e)}), 500


# # ============================================================
# # 3. REGENERATE WHATSAPP MESSAGE
# # GET /api/ai/regenerate-whatsapp/<user_id>
# # ============================================================

# @ai_bp.route('/regenerate-whatsapp/<user_id>', methods=['GET'])
# def regenerate_whatsapp(user_id):
#     """Regenerate only the WhatsApp message with a different tone"""
#     try:
#         from app import supabase

#         lead_data, error = build_lead_payload(user_id, supabase)
#         if error:
#             return jsonify({'error': error}), 404

#         images        = lead_data.get('images', [])
#         design_styles = list({img['style'] for img in images if img.get('style')})
#         places        = [p['place_name'] for p in lead_data['virtual_tour'].get('places_viewed', []) if p.get('place_name')]
#         scenarios     = [s.get('scenario_title') or s.get('custom_text', '') for s in lead_data['lifeecho'].get('scenarios', [])]
#         name          = lead_data.get('name', 'the customer')

#         prompt = f"""
# Write a new friendly WhatsApp message from a real estate sales agent to {name}.

# Their activity:
# - Design styles they liked: {', '.join(design_styles) if design_styles else 'None'}
# - Places they explored: {', '.join(places) if places else 'None'}
# - Life scenarios they selected: {', '.join(scenarios) if scenarios else 'None'}

# Make it different from a typical message. Be warm, specific, and end with a soft call to action.
# Keep it under 150 words. Return only the message text, nothing else.
# """

#         completion = client.chat.completions.create(
#             model="llama-3.3-70b-versatile",
#             messages=[{"role": "user", "content": prompt}],
#             temperature=0.9,
#             max_tokens=300
#         )

#         message = completion.choices[0].message.content.strip()

#         return jsonify({
#             'success': True,
#             'whatsapp_message': message
#         }), 200

#     except Exception as e:
#         logger.error(f"[REGENERATE WHATSAPP ERROR] {e}")
#         return jsonify({'error': 'Failed to regenerate message', 'details': str(e)}), 500

"""
ai_routes.py — AI-powered Lead Intelligence + WhatsApp Suggestion + Lead Temperature Scoring
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

1. LEAD_INTELLIGENCE: Exactly 5 bullet points for the sales person.
   - Each point must be 12-15 words
   - Focus on actionable sales insights only
   - Mention specific places, styles, scenarios they explored
   - Start each with an action word like "Highlight", "Pitch", "Mention", "Emphasize", "Suggest"
   - Example: "Highlight nearby wellness amenities like spas and gyms they explored"
   - Example: "Pitch quiet and peaceful properties based on their LifeEcho selections"

2. WHATSAPP_MESSAGE: A professional WhatsApp message from sales agent to this lead.
   - Purpose is only to open a dialogue, not to sell
   - Reference 2-3 specific things they explored (place names, design styles, scenarios)
   - Be warm, professional, not salesy
   - Mentioned that we are attaching the interior images they had generated (this will be part of the Whatsapp messages)
   - End with one simple open ended question
   - Between 80-120 words strictly
   - Also tell if they have any questions, they can ask as a message below.

Respond in this exact JSON format:
{{
    "lead_intelligence": [
        "short point 1",
        "short point 2",
        "short point 3",
        "short point 4",
        "short point 5"
    ],
    "whatsapp_message": "message here"
}}
"""
    return prompt


def build_lead_payload(user_id, supabase):
    """
    Shared helper — fetches all activity data for a user and
    returns a structured dict ready for the temperature scorer.
    Reused by both /lead-intelligence and /lead-temperature.
    """
    user_result = supabase.table('users') \
        .select('*') \
        .eq('id', user_id) \
        .execute()

    if not user_result.data:
        return None, 'Lead not found'

    u = user_result.data[0]

    # Generated images
    gens_result = supabase.table('user_generations') \
        .select('*') \
        .eq('user_id', user_id) \
        .execute()

    images = [
        {'style': g.get('style'), 'room_type': g.get('room_type')}
        for g in (gens_result.data or [])
    ]

    # Virtual tour selections
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
            'category':   v.get('vt_category')
        })

    # LifeEcho selections
    le_result = supabase.table('user_tool_selections') \
        .select('*') \
        .eq('user_id', user_id) \
        .eq('tool_name', 'lifeecho') \
        .execute()

    scenarios = []
    for l in (le_result.data or []):
        entry = {}
        if l.get('lifeecho_scenario_title'):
            entry['scenario_title'] = l['lifeecho_scenario_title']
        if l.get('lifeecho_custom_text'):
            entry['custom_text'] = l['lifeecho_custom_text']
        if entry:
            scenarios.append(entry)

    # Activity logs
    activity_result = supabase.table('user_activity_logs') \
        .select('*') \
        .eq('user_id', user_id) \
        .execute()

    tools_used = []
    total_time = 0
    for a in (activity_result.data or []):
        tools_used.append({'tool': a.get('tool_name')})
        total_time += a.get('time_spent_seconds', 0) or 0

    payload = {
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

    return payload, None


# ============================================================
# 1. LEAD INTELLIGENCE
# GET /api/ai/lead-intelligence/<user_id>
# ============================================================

@ai_bp.route('/lead-intelligence/<user_id>', methods=['GET'])
def get_lead_intelligence(user_id):
    try:
        from app import supabase

        lead_data, error = build_lead_payload(user_id, supabase)
        if error:
            return jsonify({'error': error}), 404

        prompt = build_lead_prompt(lead_data)

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )

        response_text = completion.choices[0].message.content

        import json, re
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


# ============================================================
# 2. LEAD TEMPERATURE SCORING
# GET /api/ai/lead-temperature/<user_id>
#
# Returns:
# {
#   "success": true,
#   "user_id": "...",
#   "score": 80,
#   "temperature": "HOT",
#   "reasoning": "...",
#   "sales_strategy": "..."
# }
# ============================================================

@ai_bp.route('/lead-temperature/<user_id>', methods=['GET'])
def get_lead_temperature(user_id):
    try:
        from app import supabase
        import json, re

        # ── Build lead payload ──────────────────────────────
        lead_data, error = build_lead_payload(user_id, supabase)
        if error:
            return jsonify({'error': error}), 404

        # ── Build temperature scoring prompt ────────────────
        images          = lead_data.get('images', [])
        design_styles   = list({img['style'] for img in images if img.get('style')})
        vt              = lead_data.get('virtual_tour', {})
        le              = lead_data.get('lifeecho', {})
        tools_used      = list({t['tool'] for t in lead_data.get('tools_used', []) if t.get('tool')})
        time_spent_min  = lead_data.get('total_time_spent_minutes', 0)

        # Flatten scenario text for intent keywords
        scenario_texts = []
        for s in le.get('scenarios', []):
            if s.get('scenario_title'):
                scenario_texts.append(s['scenario_title'])
            if s.get('custom_text'):
                scenario_texts.append(s['custom_text'])

        vt_place_names = [
            p['place_name'] for p in vt.get('places_viewed', []) if p.get('place_name')
        ]

        lead_payload = {
            "total_time_spent_minutes": time_spent_min,
            "unique_design_styles": design_styles,
            "tools_used": tools_used,
            "lifeecho_scenarios": scenario_texts,
            "virtual_tour_places": vt_place_names,
            "virtual_tour_categories": vt.get('categories_explored', [])
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
{json.dumps(lead_payload, indent=2)}"""

        # ── Call Groq ───────────────────────────────────────
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": temperature_prompt}],
            temperature=0.3,   # lower temp for deterministic scoring
            max_tokens=400
        )

        response_text = completion.choices[0].message.content.strip()

        # Strip markdown fences if present
        clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', response_text, flags=re.DOTALL).strip()

        json_match = re.search(r'\{.*\}', clean, re.DOTALL)
        if not json_match:
            return jsonify({'error': 'Failed to parse AI temperature response'}), 500

        result = json.loads(json_match.group())

        return jsonify({
            'success':        True,
            'user_id':        user_id,
            'score':          result.get('score'),
            'temperature':    result.get('temperature'),
            'reasoning':      result.get('reasoning', ''),
            'sales_strategy': result.get('sales_strategy', '')
        }), 200

    except Exception as e:
        logger.error(f"[LEAD TEMPERATURE ERROR] {e}")
        return jsonify({'error': 'Failed to score lead temperature', 'details': str(e)}), 500


# ============================================================
# 3. REGENERATE WHATSAPP MESSAGE
# GET /api/ai/regenerate-whatsapp/<user_id>
# ============================================================

@ai_bp.route('/regenerate-whatsapp/<user_id>', methods=['GET'])
def regenerate_whatsapp(user_id):
    """Regenerate only the WhatsApp message with a different tone"""
    try:
        from app import supabase

        lead_data, error = build_lead_payload(user_id, supabase)
        if error:
            return jsonify({'error': error}), 404

        images        = lead_data.get('images', [])
        design_styles = list({img['style'] for img in images if img.get('style')})
        places        = [p['place_name'] for p in lead_data['virtual_tour'].get('places_viewed', []) if p.get('place_name')]
        scenarios     = [s.get('scenario_title') or s.get('custom_text', '') for s in lead_data['lifeecho'].get('scenarios', [])]
        name          = lead_data.get('name', 'the customer')

        prompt = f"""
Write a new friendly WhatsApp message from a real estate sales agent to {name}.

Their activity:
- Design styles they liked: {', '.join(design_styles) if design_styles else 'None'}
- Places they explored: {', '.join(places) if places else 'None'}
- Life scenarios they selected: {', '.join(scenarios) if scenarios else 'None'}

Make it different from a typical message. Be warm, specific, and end with a soft call to action.
Keep it under 150 words. Return only the message text, nothing else.
"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
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