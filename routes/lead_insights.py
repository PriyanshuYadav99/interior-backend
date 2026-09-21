"""
lead_insights.py — everything the lead-detail modal needs, in one place.

Put this file next to admin_routes.py (routes/lead_insights.py) and import it as
    from routes.lead_insights import build_lead_detail, refresh_intent_score_async

Provides:
  - collect_lead_data / summarize : one consistent read of a lead's activity
  - compute_intent_score          : your 100-point rubric, computed in Python (no LLM needed)
  - get_ai_content                : lead intelligence + living insights + SMS/Email/WhatsApp
                                    (one Groq call, cached on users.ai_content)
  - build_lead_detail             : the full JSON for GET /api/admin/leads/<user_id>
  - refresh_intent_score_async    : call after activity is logged so list statuses stay fresh
"""

import os
import re
import json
import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

TOOL_LABELS = {
    'room_design': 'Room design',
    'lifeecho': 'Living insight',
    'virtual_tour': 'Explore nearby',
    'local_watch': 'Local watch',
}
TOOL_ORDER = ['room_design', 'lifeecho', 'virtual_tour', 'local_watch']
ICONS = {'shield', 'home', 'clock', 'building', 'volume'}

_HIGH_INTENT = re.compile(
    r'\b(health\w*|daycare|elderly|school\w*|hospital\w*|accessib\w*|pets?)\b', re.I)
_GENERIC = re.compile(r'\b(shopping|market\w*|metro|transport\w*)\b', re.I)


# ============================================================
# Small helpers
# ============================================================

def _ts(value):
    """Parse an ISO timestamp into an aware datetime (or None)."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


_DIAL = {'IN': '91', 'US': '1', 'CA': '1', 'AE': '971', 'GB': '44', 'UK': '44',
         'AU': '61', 'SG': '65', 'SA': '966', 'QA': '974', 'PK': '92', 'BD': '880'}


def format_phone(user):
    """country_code may be a dial code ('91') or an ISO code ('US'). Never print '+US ...'."""
    cc = str(user.get('country_code') or '91').strip().lstrip('+')
    if cc.isalpha():
        cc = _DIAL.get(cc.upper(), '')
    num = user.get('phone_number') or 'N/A'
    return f"+{cc} {num}" if cc else str(num)


def _image_url(g):
    # Your save_generation_to_db() takes `generated_image_url`; the column may be named either way.
    return g.get('image_url') or g.get('generated_image_url') or g.get('cloudinary_url') or ''


# ============================================================
# 1. READ + SUMMARISE
# ============================================================

def collect_lead_data(supabase, user):
    """Fetch every row that belongs to this lead (by user_id OR by any of their session_ids)."""
    uid = user['id']

    sess = supabase.table('sessions').select('session_id').eq('user_id', uid).execute().data or []
    sids = [s['session_id'] for s in sess if s.get('session_id')]

    def rows(table):
        q = supabase.table(table).select('*')
        if sids:
            q = q.or_(f"user_id.eq.{uid},session_id.in.({','.join(sids)})")
        else:
            q = q.eq('user_id', uid)
        return q.order('created_at', desc=True).execute().data or []

    seen, gens = set(), []
    for g in rows('user_generations'):
        key = g.get('generation_id') or g.get('id') or id(g)
        if key in seen:
            continue
        seen.add(key)
        gens.append(g)

    interests = supabase.table('user_property_interests') \
        .select('property_section, room_type, style') \
        .eq('user_id', uid).execute().data or []

    return {
        'gens': gens,
        'activity': rows('user_activity_logs'),
        'selections': rows('user_tool_selections'),
        'interests': interests,
    }


def summarize(data, user, section_names=None):
    section_names = section_names or {}
    gens, activity, sels = data['gens'], data['activity'], data['selections']

    # time per tool
    per_tool = {}
    for a in activity:
        t = a.get('tool_name') or a.get('activity_type') or 'unknown'
        secs = int(a.get('time_spent_seconds') or 0)
        d = per_tool.setdefault(t, {'tool': t, 'total_time_seconds': 0, 'sessions_count': 0})
        d['total_time_seconds'] += secs
        d['sessions_count'] += 1
    tools_used = [d for d in per_tool.values() if d['total_time_seconds'] > 0]
    total_secs = sum(d['total_time_seconds'] for d in tools_used)

    # tools used = time logs + anything we can prove from their data
    # (the time log is lost if the tab is closed, the selections/generations are not)
    keys = {d['tool'] for d in tools_used}
    if gens:
        keys.add('room_design')
    for s in sels:
        if s.get('tool_name'):
            keys.add(s['tool_name'])
    keys.discard('unknown')
    ordered = [k for k in TOOL_ORDER if k in keys] + sorted(k for k in keys if k not in TOOL_ORDER)

    vt_rows = [s for s in sels if s.get('tool_name') == 'virtual_tour']
    le_rows = [s for s in sels if s.get('tool_name') == 'lifeecho']

    scenario_texts = [
        (l.get('lifeecho_scenario_title') or l.get('lifeecho_custom_text') or '').strip()
        for l in le_rows
    ]
    scenario_texts = [t for t in scenario_texts if t]

    # unit types visited
    unit_keys = []
    for r in data['interests']:
        sec = r.get('property_section')
        if sec and sec not in unit_keys:
            unit_keys.append(sec)
    if not unit_keys and user.get('property_section'):
        unit_keys = [user['property_section']]

    # freshest timestamp across everything (used to decide if cached AI text is stale)
    stamps = []
    for r in list(activity) + list(sels) + list(gens):
        for col in ('created_at', 'updated_at'):
            dt = _ts(r.get(col))
            if dt:
                stamps.append(dt)

    minutes = round(total_secs / 60)
    if total_secs > 0 and minutes == 0:
        minutes = 1

    return {
        'tools_used': tools_used,
        'tool_keys': ordered,
        'tool_labels': [TOOL_LABELS.get(k, k.replace('_', ' ').title()) for k in ordered],
        'time_spent_seconds': total_secs,
        'time_spent_minutes': minutes,
        'styles': {g['style'] for g in gens if g.get('style')},
        'room_types': {g['room_type'] for g in gens if g.get('room_type')},
        'custom_prompts': [g['custom_prompt'] for g in gens if g.get('custom_prompt')],
        'n_designs': len([g for g in gens if _image_url(g)]),
        'scenario_texts': scenario_texts,
        'vt_rows': vt_rows,
        'le_rows': le_rows,
        'place_names': [v['vt_place_name'] for v in vt_rows if v.get('vt_place_name')],
        'vt_categories': sorted({v['vt_category'] for v in vt_rows if v.get('vt_category')}),
        'unit_type_keys': unit_keys,
        'unit_type_names': [section_names.get(k, k) for k in unit_keys],
        'last_activity': max(stamps) if stamps else None,
        'has_activity': bool(total_secs or gens or sels),
    }


# ============================================================
# 2. INTENT SCORE  (your 100-point rubric)
# ============================================================

def compute_intent_score(s):
    mins = s['time_spent_seconds'] / 60

    if mins >= 7:
        duration = 40
    elif mins >= 4:
        duration = 30
    elif mins >= 2:
        duration = 20
    elif mins >= 1:
        duration = 15      # NOTE: 1-2 min isn't in your rubric; 15 is my assumption
    elif mins > 0:
        duration = 10
    else:
        duration = 0

    n = len(s['styles'])
    design = 0 if n == 0 else 20 if n == 1 else 15 if n == 2 else 5

    has_le = 'lifeecho' in s['tool_keys']
    has_vt = 'virtual_tour' in s['tool_keys']
    depth = 20 if (has_le and has_vt) else 10 if (has_le or has_vt) else 0

    text = ' '.join(s['scenario_texts'] + s['place_names'] + s['vt_categories'])
    intent = 20 if _HIGH_INTENT.search(text) else 10 if _GENERIC.search(text) else 0

    score = duration + design + depth + intent
    temperature = 'HOT' if score >= 70 else 'WARM' if score >= 40 else 'COLD'
    reasoning = (f"Session time {duration}/40, design focus {design}/20, "
                 f"tool depth {depth}/20, intent specificity {intent}/20.")
    return {'score': score, 'temperature': temperature, 'reasoning': reasoning}


def persist_score(supabase, uid, result, user=None):
    """Write the score to users.* so the leads list / property cards can read it cheaply."""
    if user and user.get('lead_score') == result['score'] \
            and user.get('lead_temperature') == result['temperature']:
        return
    try:
        supabase.table('users').update({
            'lead_score': result['score'],
            'lead_temperature': result['temperature'],
            'lead_reasoning': result['reasoning'],
            'temperature_updated_at': datetime.now(timezone.utc).isoformat(),
        }).eq('id', uid).execute()
    except Exception as e:
        logger.warning(f"[INTENT SCORE] could not persist for {uid}: {e}")


def refresh_intent_score(supabase, user_id):
    try:
        rows = supabase.table('users').select('*').eq('id', user_id).execute().data
        if not rows:
            return
        user = rows[0]
        s = summarize(collect_lead_data(supabase, user), user)
        if s['has_activity']:
            persist_score(supabase, user_id, compute_intent_score(s), user)
    except Exception as e:
        logger.warning(f"[INTENT SCORE] refresh failed for {user_id}: {e}")


def refresh_intent_score_async(supabase, user_id):
    """Fire-and-forget. Call after logging activity / selections / generations."""
    if user_id:
        threading.Thread(target=refresh_intent_score, args=(supabase, user_id), daemon=True).start()


# ============================================================
# 3. AI CONTENT  (lead intelligence + living insights + messages)
# ============================================================

def _call_groq_json(prompt, max_tokens=2500):
    from groq import Groq
    client = Groq(api_key=os.getenv('GROQ_API_KEY'))
    comp = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=max_tokens,
        reasoning_effort="low",
    )
    raw = (comp.choices[0].message.content or '').strip()
    clean = re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.DOTALL).strip()
    m = re.search(r'\{.*\}', clean, re.DOTALL)
    return json.loads(m.group()) if m else None


def _normalize_content(c):
    """Validate/repair the model output. Returns None if unusable."""
    if not isinstance(c, dict):
        return None
    intel = [str(x).strip() for x in (c.get('lead_intelligence') or []) if str(x).strip()]
    msgs = c.get('messages') or {}
    if not intel or not isinstance(msgs, dict) or not msgs.get('sms'):
        return None

    insights = []
    for i in (c.get('living_insights') or []):
        if isinstance(i, dict) and i.get('text'):
            icon = i.get('icon') if i.get('icon') in ICONS else 'home'
            insights.append({'text': str(i['text']).strip(), 'icon': icon})
        elif isinstance(i, str) and i.strip():
            insights.append({'text': i.strip(), 'icon': 'home'})

    email = msgs.get('email')
    if isinstance(email, str):
        email = {'subject': 'Following up on your home search', 'body': email}
    if not isinstance(email, dict):
        email = {'subject': 'Following up on your home search', 'body': msgs.get('whatsapp', '')}

    return {
        'lead_intelligence': intel[:6],
        'living_insights': insights[:4],
        'messages': {
            'sms': str(msgs.get('sms', '')).strip(),
            'email': {'subject': str(email.get('subject', '')).strip(),
                      'body': str(email.get('body', '')).strip()},
            'whatsapp': str(msgs.get('whatsapp') or msgs.get('sms', '')).strip(),
        },
    }


def _fallback_content(user, s, property_name):
    """Used when Groq is down / unparseable, so the modal is never empty."""
    first = (user.get('full_name') or 'there').split(' ')[0]
    unit = s['unit_type_names'][0] if s['unit_type_names'] else 'home'
    prop = property_name or 'our development'

    intel = []
    if s['scenario_texts']:
        intel.append(f"Reference their interest in: {s['scenario_texts'][0]}.")
    if s['place_names']:
        intel.append(f"Promote nearby spots they explored, like {s['place_names'][0]}.")
    if s['styles']:
        intel.append(f"Mention their design preferences ({', '.join(sorted(s['styles']))}).")
    intel.append("Propose an in-person site visit to bring their designs to life.")

    insights = [{'text': t, 'icon': 'home'} for t in s['scenario_texts'][:3]]

    sms = (f"Hi {first}, thanks for exploring {prop}. We have {unit} options that match your "
           f"interests. Would you like to arrange a viewing this week?")
    return {
        'lead_intelligence': intel,
        'living_insights': insights,
        'messages': {
            'sms': sms,
            'email': {'subject': f"Your home search at {prop}", 'body': sms},
            'whatsapp': sms,
        },
    }


def _generate_content(user, s, property_name):
    first = (user.get('full_name') or 'there').split(' ')[0]
    ctx = {
        'first_name': first,
        'property': property_name or 'the development',
        'unit_types_viewed': s['unit_type_names'],
        'minutes_on_platform': s['time_spent_minutes'],
        'tools_used': s['tool_labels'],
        'design_styles': sorted(s['styles']),
        'room_types': sorted(s['room_types']),
        'custom_design_requests': s['custom_prompts'][:5],
        'life_scenarios': s['scenario_texts'][:8],
        'nearby_places': s['place_names'][:8],
        'nearby_categories': s['vt_categories'],
        'has_generated_room_designs': bool(s['n_designs']),
    }

    prompt = f"""You are a real estate sales assistant. Using ONLY the buyer data below, write sales content.

BUYER DATA:
{json.dumps(ctx, indent=2)}

Return ONE JSON object, no markdown, exactly this shape:
{{
  "lead_intelligence": ["6 strings"],
  "living_insights": [{{"text": "string", "icon": "shield|home|clock|building|volume"}}],
  "messages": {{
    "sms": "string",
    "email": {{"subject": "string", "body": "string"}},
    "whatsapp": "string"
  }}
}}

RULES
- lead_intelligence: exactly 6 items, each 6-14 words, each starting with an action verb
  (Focus, Highlight, Proactively, Reference, Promote, Propose...). Be specific: name the styles,
  places and scenarios from the data. Do not invent facts.
- living_insights: 2-4 items, each max 12 words, describing what this buyer CARES ABOUT,
  inferred from life_scenarios (e.g. "Parents cautious about monsoon safety and access roads.").
  Do not just repeat the scenario title. If life_scenarios is empty, return [].
- nearby_places are businesses NEAR the development (e.g. a hotel gym, a restaurant). NEVER describe
  them as amenities inside the property, and never claim facilities that are not in the data.
- messages: address the buyer by first_name and use the real property / unit type. NEVER use
  placeholders, braces or brackets. Warm, not pushy, no invented prices or discounts.
  sms: max 300 characters. whatsapp: 60-100 words. email body: 90-140 words, sign off as
  "Sales Team, <property>". If has_generated_room_designs is true, mention the designs they
  created in the whatsapp and email messages. End each message with one simple question
  (e.g. arranging a viewing this week).
"""
    try:
        return _normalize_content(_call_groq_json(prompt))
    except Exception as e:
        logger.error(f"[LEAD AI CONTENT] Groq failed: {e}")
        return None


def get_ai_content(supabase, user, s, property_name, force=False):
    """Cached on users.ai_content; regenerated only when there is newer activity."""
    cached = user.get('ai_content')
    if isinstance(cached, str):
        try:
            cached = json.loads(cached)
        except Exception:
            cached = None
    updated = _ts(user.get('ai_content_updated_at'))

    fresh = bool(cached) and updated is not None and \
        (s['last_activity'] is None or updated >= s['last_activity'])
    if fresh and not force:
        return cached

    content = _generate_content(user, s, property_name)
    if content:
        try:
            supabase.table('users').update({
                'ai_content': content,
                'ai_content_updated_at': datetime.now(timezone.utc).isoformat(),
            }).eq('id', user['id']).execute()
        except Exception as e:
            logger.warning(f"[LEAD AI CONTENT] cache write failed (run the SQL migration?): {e}")
        return content

    return cached or _fallback_content(user, s, property_name)


# ============================================================
# 4. FULL RESPONSE FOR GET /api/admin/leads/<user_id>
# ============================================================

def build_lead_detail(supabase, user, section_names, property_name='', force_ai=False, debug=False):
    data = collect_lead_data(supabase, user)
    s = summarize(data, user, section_names)

    # Keep the score your own scorer already saved (users.lead_score / lead_temperature).
    # Only leads that were never scored fall back to the Python rubric.
    if user.get('lead_score') is not None and user.get('lead_temperature'):
        score = {
            'score': user['lead_score'],
            'temperature': user['lead_temperature'],
            'reasoning': user.get('lead_reasoning') or '',
        }
    else:
        score = compute_intent_score(s)
        if s['has_activity']:
            persist_score(supabase, user['id'], score, user)

    ai = get_ai_content(supabase, user, s, property_name, force=force_ai)

    # ---- room designs (what the lead generated)
    room_designs, missing_url = [], 0
    for g in data['gens']:
        url = _image_url(g)
        if not url:
            missing_url += 1
            continue
        style = g.get('style') or ''
        prompt = g.get('custom_prompt')
        room_designs.append({
            'id': g.get('generation_id') or g.get('id'),
            'image_url': url,
            'room_type': g.get('room_type') or 'N/A',
            'style': style or 'N/A',
            'custom_prompt': prompt,
            'label': prompt if (style == 'custom' and prompt) else style.replace('_', ' ').title(),
            'created_at': g.get('created_at', ''),
            'downloaded': g.get('downloaded', False),
            'download_count': g.get('download_count', 0),
        })

    # ---- explore nearby (deduped places)
    seen, nearby = set(), []
    for v in s['vt_rows']:
        key = v.get('vt_place_id') or v.get('vt_place_name')
        if not key or key in seen:
            continue
        seen.add(key)
        nearby.append({
            'name': v.get('vt_place_name'),
            'category': v.get('vt_category'),
            'photo_url': v.get('vt_photo_url'),
            'distance': v.get('vt_distance'),
            'rating': v.get('vt_rating'),
        })

    lead = {
        'id': user['id'],
        'name': user.get('full_name', 'Unknown'),
        'phone': format_phone(user),
        'email': user.get('email', 'N/A'),
        'registration_date': user.get('created_at', ''),
        'property_section': user.get('property_section'),

        # ---- the 10 things on the modal ----
        'intent_score': score['score'],                                   # 1
        'unit_types': s['unit_type_names'],                               # 2
        'unit_type_keys': s['unit_type_keys'],
        'time_spent_seconds': s['time_spent_seconds'],                    # 3
        'time_spent_minutes': s['time_spent_minutes'],
        'tools_used_labels': s['tool_labels'],                            # 4
        'lead_intelligence': ai['lead_intelligence'],                     # 5
        'messages': ai['messages'],                                       # 6  {sms, email{subject,body}, whatsapp}
        # 7 = POST /api/ai/send-outreach/<id>
        'room_designs': room_designs,                                     # 8
        'living_insights': ai['living_insights'],                         # 9
        'explore_nearby': nearby,                                         # 10

        # ---- legacy keys (kept so nothing that already works breaks) ----
        'temperature': {
            'score': score['score'],
            'temperature': score['temperature'],
            'reasoning': score['reasoning'],
            'sales_strategy': user.get('lead_sales_strategy') or '',
        },
        'images': room_designs,
        'total_generations': (user.get('total_generations', 0) or 0)
                             + (user.get('pre_registration_generations', 0) or 0),
        'total_time_spent_seconds': s['time_spent_seconds'],
        'total_time_spent_minutes': round(s['time_spent_seconds'] / 60, 1),
        'tools_used': s['tools_used'],
        'virtual_tour': {
            'categories_explored': s['vt_categories'],
            'places_viewed': [{
                'category': v.get('vt_category'), 'place_name': v.get('vt_place_name'),
                'place_id': v.get('vt_place_id'), 'photo_url': v.get('vt_photo_url'),
                'distance': v.get('vt_distance'), 'rating': v.get('vt_rating'),
                'viewed_at': v.get('created_at'),
            } for v in s['vt_rows']],
        },
        'lifeecho': {
            'total_scenarios_viewed': len(s['le_rows']),
            'scenarios': [{
                'scenario_id': l.get('lifeecho_scenario_id'),
                'scenario_title': l.get('lifeecho_scenario_title'),
                'scenario_icon': l.get('lifeecho_scenario_icon', 'clock'),
                'is_custom': l.get('lifeecho_is_custom', False),
                'custom_text': l.get('lifeecho_custom_text'),
                'selected_at': l.get('created_at'),
            } for l in s['le_rows']],
        },
    }

    if debug:
        lead['_debug'] = {
            'generation_rows': len(data['gens']),
            'generation_rows_without_image_url': missing_url,
            'generation_columns': sorted(data['gens'][0].keys()) if data['gens'] else [],
            'activity_rows': len(data['activity']),
            'selection_rows': len(data['selections']),
            'interest_rows': len(data['interests']),
        }
    return lead