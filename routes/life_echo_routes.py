# """
# Scenario Simulator Module - Single File Version
# Generates realistic real estate scenarios with AI-generated images and narratives
# """

# from flask import Blueprint, request, jsonify
# import os
# import time
# import logging
# import requests
# import base64
# from groq import Groq
# import json
# import re
# import threading
# from pathlib import Path
# logger = logging.getLogger(__name__)

# # ============================================================
# # CONFIGURATION
# # ============================================================

# # Initialize Groq client
# GROQ_API_KEY = os.getenv('GROQ_API_KEY')
# groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# # Replicate API
# REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

# # ============================================================
# # CREATE BLUEPRINT
# # ============================================================

# scenario_bp = Blueprint('scenario', __name__, url_prefix='/api/scenario')

# # ============================================================
# # ❌ REMOVED: Duplicate CORS handler (handled globally in app.py)
# # ============================================================
# # The @scenario_bp.after_request decorator has been removed
# # because app.py already handles CORS globally

# # ============================================================
# # SERVICE FUNCTIONS
# # ============================================================




# def generate_scenario_story(scenario_text):
#     """
#     Generate context-aware scenario narratives using Groq
#     - Timeline format for time-based/emergency scenarios
#     - Narrative format for lifestyle/emotional scenarios
#     Expected time: 1-2 seconds
#     """
#     try:
#         if not groq_client:
#             return {
#                 'success': False,
#                 'error': 'GROQ_API_KEY not configured'
#             }
        
#         start_time = time.time()
        
#         prompt = f"""Analyze this real estate scenario: "{scenario_text}"

# **STEP 1: IDENTIFY THE SCENARIO TYPE**
# - Does it mention a specific TIME (3 AM, 9 AM, etc.)? → Use TIMELINE format
# - Is it an EMERGENCY (fever, hospital, urgent)? → Use TIMELINE format
# - Is it ROUTINE with time sensitivity (school, work, airport)? → Use TIMELINE format
# - Is it LIFESTYLE/EMOTIONAL (safety, noise, leisure, peace)? → Use NARRATIVE format

# **STEP 2: GENERATE THE RESPONSE**

# ---
# ## FOR TIMELINE FORMAT (Emergency/Time-based scenarios):
# ---

# TITLE: [Action-focused title, 5-8 words]

# SCENARIO:
# [Opening line: Set the situation - 1 complete sentence]

# **Timeline:**
# [TIME] — [Action step 1]
# [TIME] — [Action step 2]
# [TIME] — [Action step 3]
# [TIME] — [Outcome/arrival]

# **Transport Options Available:**
# - [Option 1: e.g., Own Vehicle - Direct basement access, no parking delay]
# - [Option 2: e.g., School Bus - Picks up from community gate]
# - [Option 3: e.g., Taxi/Cab - 2-min wait time, AED 15-25]
# - [Option 4: e.g., RTA Bus/Metro - Nearest station 800m]

# [Closing paragraph: MAX 3 sentences explaining why this location makes it easy]

# TAGLINE: [Practical benefit statement]

# **EXAMPLE 1 (Emergency at specific time):**
# TITLE: Crisis to Care in 9 Minutes

# SCENARIO:
# It's 3 AM, and your son's fever has spiked to 104°F. You need to reach the hospital immediately.

# **Timeline:**
# 3:00 AM — Discover high fever, make the decision to go to ER
# 3:02 AM — Wake up, grab emergency documents and medications
# 3:05 AM — Exit apartment building, security gate opens instantly
# 3:09 AM — Arrive at City Pediatric Hospital emergency entrance

# **Transport Options Available:**
# - Own Vehicle - Direct basement parking access, start immediately
# - Taxi/Cab - Book via app, 3-4 minute arrival time, AED 25-40
# - Ambulance - Community emergency hotline, 5-minute response time
# - Neighbor's Vehicle - WhatsApp group emergency protocol active

# The hospital is only 2.3 kilometers away via a wide arterial road with zero traffic at night. The 24/7 manned security ensures the gate opens immediately without fumbling for access cards. While families in congested areas waste 20+ minutes, you're already in the ER getting treatment.

# TAGLINE: In medical emergencies, proximity saves lives.

# **EXAMPLE 2 (Routine with goal time):**
# TITLE: School Run in Under 30 Minutes

# SCENARIO:
# Your son's school starts at 9 AM sharp, and he cannot be late.

# **Timeline:**
# 8:35 AM — Finish breakfast and pack school bag
# 8:40 AM — Leave apartment, walk to parking area
# 8:45 AM — Start driving via the service road
# 8:55 AM — Arrive at school gate, 5 minutes early

# **Transport Options Available:**
# - School Bus - Picks up from community gate at 8:15 AM daily
# - Own Vehicle - Basement parking, 10-minute direct drive
# - Carpool - Rotate with 3 neighbor families via WhatsApp
# - Taxi/Cab - Available at gate, AED 20-35 per trip

# The school is just 3.5 kilometers away via a signal-free stretch of road. No narrow lanes, no U-turns, no traffic chaos. While other parents leave home at 8 AM to fight congestion, you're finishing breakfast in peace.

# TAGLINE: Convenience isn't a perk. It's a parenting essential.

# ---
# ## FOR NARRATIVE FORMAT (Lifestyle/Emotional scenarios):
# ---

# TITLE: [Emotional/evocative title, 5-8 words]

# SCENARIO:
# [Paragraph 1: Set the scene with sensory details - MAX 3 sentences only]

# [Paragraph 2: Show the contrast or problem - MAX 3 sentences only]

# [Paragraph 3: How the property solves it - MAX 3 sentences with specific features]

# [Paragraph 4: Emotional impact - MAX 2 sentences only]

# TAGLINE: [Memorable emotional statement]

# **EXAMPLE:**
# TITLE: Serenity Found

# SCENARIO:
# Imagine waking up to the sweet songs of birds and the gentle rustle of leaves. Your home is surrounded by lush green parks visible from every window. The fresh air and soothing views create a sense of tranquility from the very first morning.

# As you step out, vibrant flowers and open walkways greet you. The parks offer a serene escape where children play freely and families gather for evening walks. It's a stark contrast to the noise and congestion most city dwellers accept as normal.

# Inside, triple-glazed windows and an 80-meter green buffer zone ensure city noise never intrudes. Your children can study without distractions, and you can work from home with windows open. This isn't clever architecture — it's designed wellness for your entire family.

# The true luxury isn't marble lobbies or imported fittings. It's the ability to hear yourself think, sleep deeply, and wake up refreshed every single morning.

# TAGLINE: Find your inner peace in perfect harmony with nature.

# ---

# **CRITICAL RULES:**
# - TOTAL LENGTH: 180-220 words (not counting title/tagline)
# - TIMELINE FORMAT: Always include ALL 4 sections — Opening line, Timeline (4 steps), Transport Options (4 options), Closing paragraph. NEVER skip any section.
# - NARRATIVE FORMAT: Always include ALL 4 paragraphs. NEVER skip any paragraph.
# - Each paragraph: MAXIMUM 3 sentences, keep it concise
# - Currency: STRICTLY use INR (Indian Rupees, ₹) ONLY. NEVER use AED, $, €, or any other currency. Every single price must be in ₹. Example: ₹25-40, ₹200-350
# - **TIMELINE TIME ANCHORING**: If user mentions a specific time (e.g., "3 AM", "9 AM"), START the timeline at that EXACT time or slightly before
# - Timeline format: Each time step on NEW LINE with clear formatting
# - Timeline intervals: Use realistic 2-5 minute gaps between steps
# - Transport options: Each option on NEW LINE with dash (-)
# - NEVER end mid-sentence - always complete every paragraph
# - For narrative: Write in complete, flowing paragraphs
# - Make every sentence complete and grammatically correct
# - End with proper punctuation (. ! ?)

# **OUTPUT FORMAT:**
# TITLE: [Title here]

# SCENARIO:
# [Content with proper line breaks and formatting]

# TAGLINE: [Tagline here]"""

#         chat_completion = groq_client.chat.completions.create(
#             messages=[
#                 {
#                     "role": "system",
#                     "content": """You are an expert real estate scenario writer based in Dubai, UAE. You create two types of content:

# 1. TIMELINE scenarios: Use clear line breaks for each time step. Format like:
#    8:45 AM — Action here
#    8:50 AM — Next action
   
#    CRITICAL: If the user mentions a specific time (like "3 AM" or "9 AM"), your timeline MUST start at or near that time. DO NOT start from midnight (12:00 AM) or any other arbitrary time. Examples:
#    - User says "3 AM emergency" → Start timeline at 3:00 AM
#    - User says "9 AM school" → Start timeline around 8:35-8:45 AM
#    - User says "midnight fever" → Start timeline at 12:00 AM

# 2. NARRATIVE scenarios: Write in complete, flowing paragraphs with MAXIMUM 3 sentences per paragraph. NEVER end mid-sentence.

# CRITICAL CURRENCY RULE: You are writing for India. EVERY price MUST be in INR (Indian Rupees, symbol ₹). NEVER use AED, $, £, € or any other currency under any circumstance. If you use any currency other than ₹/INR, the response is considered a failure.

# CRITICAL COMPLETENESS RULE: For TIMELINE format, you MUST always include ALL of these sections in order:
# 1. Opening sentence
# 2. Timeline with exactly 4 steps
# 3. Transport Options with exactly 4 options
# 4. Closing paragraph (3 sentences)
# 5. Tagline
# NEVER skip or shorten any section. A missing section is a failed response.

# For NARRATIVE format, you MUST always include ALL 4 paragraphs. NEVER skip any paragraph.

# Keep each paragraph to a maximum of 3 sentences.
# Always finish every sentence completely. Never truncate words or leave sentences incomplete."""
#                 },
#                 {
#                     "role": "user",
#                     "content": prompt
#                 }
#             ],
#             model="openai/gpt-oss-120b",
#     temperature=0.7,
#     max_tokens=2000,          # increased from 900
#     reasoning_effort="low",   # ask it to spend fewer tokens "thinking"
#     stop=None
# )
        
#         response_text = chat_completion.choices[0].message.content.strip()
        
#         # Enhanced parsing that preserves formatting
#         lines = response_text.split('\n')
#         title = ""
#         story_content = []
#         tagline = ""
        
#         current_section = None
#         collecting_story = False
        
#         for line in lines:
#             stripped = line.strip()
            
#             if stripped.startswith("TITLE:"):
#                 title = stripped.replace("TITLE:", "").strip()
#                 current_section = "title"
                
#             elif stripped.startswith("SCENARIO:"):
#                 current_section = "story"
#                 collecting_story = True
                
#             elif stripped.startswith("TAGLINE:"):
#                 tagline = stripped.replace("TAGLINE:", "").strip()
#                 current_section = "tagline"
#                 collecting_story = False
                
#             elif collecting_story and current_section == "story":
#                 story_content.append(line)
        
#         # Clean up story content - remove leading/trailing empty lines only
#         while story_content and not story_content[0].strip():
#             story_content.pop(0)
#         while story_content and not story_content[-1].strip():
#             story_content.pop()
        
#         # Check if last line ends mid-sentence
#         if story_content:
#             last_line = story_content[-1].strip()
#             if last_line and last_line[-1] not in '.!?':
#                 full_text = '\n'.join(story_content)
#                 last_period = max(full_text.rfind('.'), full_text.rfind('!'), full_text.rfind('?'))
                
#                 if last_period > 0:
#                     full_text = full_text[:last_period + 1]
#                     story_content = full_text.split('\n')
#                     logger.warning("[GROQ] Truncated incomplete sentence")
        
#         # Convert story_content to paragraphs
#         story_paragraphs = []
#         current_para = []
        
#         for line in story_content:
#             stripped = line.strip()
#             if not stripped:
#                 if current_para:
#                     story_paragraphs.append('\n'.join(current_para))
#                     current_para = []
#             else:
#                 current_para.append(line)
        
#         if current_para:
#             story_paragraphs.append('\n'.join(current_para))
        
#         generation_time = time.time() - start_time
        
#         logger.info(f"[GROQ] ✅ Scenario generated in {generation_time:.2f}s")
#         logger.info(f"[GROQ] Generated {len(story_paragraphs)} paragraphs")
        
#         return {
#             'success': True,
#             'title': title,
#             'story': story_paragraphs,
#             'tagline': tagline,
#             'generation_time': f"{generation_time:.2f}s"
#         }
        
#     except Exception as e:
#         logger.error(f"[GROQ ERROR] {str(e)}")
#         return {
#             'success': False,
#             'error': str(e)
#         }


# # ============================================================
# # IMAGE SERVICE (Pexels + cache)
# # ============================================================
# PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')
# IMAGE_CACHE_FILE = Path(os.getenv('IMAGE_CACHE_FILE', 'scenario_image_cache.json'))
# _cache_lock = threading.Lock()

# def _load_image_cache():
#     try:
#         if IMAGE_CACHE_FILE.exists():
#             return json.loads(IMAGE_CACHE_FILE.read_text(encoding='utf-8'))
#     except Exception as e:
#         logger.warning(f"[IMAGES] Could not load cache: {e}")
#     return {}

# _image_cache = _load_image_cache()

# def _save_image_cache():
#     try:
#         IMAGE_CACHE_FILE.write_text(json.dumps(_image_cache), encoding='utf-8')
#     except Exception as e:
#         logger.warning(f"[IMAGES] Could not save cache: {e}")

# # (regex of trigger words, cache key, search query that gives realistic photos)
# # ORDER MATTERS: more specific rules first.
# KEYWORD_RULES = [
#     (r'\b(gym|fitness|workout|yoga|exercise)\b', 'gym', 'modern gym interior fitness equipment'),
#     (r'\b(hospital|emergency|clinic|fever|ambulance|medical|doctor)\b', 'hospital', 'hospital building exterior modern'),
#     (r'\b(restaurant|dining|cafe|coffee|food|brunch|dinner)\b', 'dining', 'restaurant interior dining cozy'),
#     (r'\b(hockey|rink|skating|trail|trails|hiking|cycling)\b', 'outdoor-rec', 'community park walking trail'),
#     (r'\b(park|parks|garden|green|playground|nature)\b', 'park', 'city park green trees residential'),
#     (r'\b(school|schools|catchment|elementary|secondary|education|library|libraries)\b', 'school', 'school building exterior students'),
#     (r'\b(transit|metro|train|lrt|subway|station|commute|bus)\b', 'transit', 'modern train station platform commuters'),
#     (r'\b(mall|shopping|grocery|groceries|supermarket|walkable)\b', 'shopping', 'shopping street supermarket exterior'),
#     (r'\b(basement|flood|flooding|drainage|sump)\b', 'basement', 'finished basement suite interior'),
#     (r'\b(garage|snow|winter|driveway)\b', 'winter-home', 'suburban house snow driveway garage'),
#     (r'\b(fiber|internet|wifi|remote work|cottage)\b', 'remote-work', 'home office remote work lake view'),
#     (r'\b(wildfire|fire)\b', 'wildfire', 'house forest landscaping stone gravel'),
#     (r'\b(energy|heat pump|insulation|solar)\b', 'energy', 'modern energy efficient house exterior'),
#     (r'\b(quiet|noise|peace|cul-de-sac|serenity)\b', 'quiet', 'quiet residential street cul-de-sac trees'),
#     (r'\b(security|safety|safe)\b', 'security', 'gated residential community entrance'),
#     (r'\b(temple|church|mosque|prayer|worship)\b', 'worship', 'place of worship exterior architecture'),
#     (r'\b(pool|swimming|clubhouse|amenit)\w*', 'amenities', 'apartment building swimming pool amenities'),
# ]
# DEFAULT_KEY = 'residential'
# DEFAULT_QUERY = 'modern residential apartment building exterior'

# def resolve_keyword(title, text):
#     """Title first (most specific), then the longer text. Returns (cache_key, search_query)."""
#     for haystack in (title.lower(), text.lower()):
#         for pattern, key, query in KEYWORD_RULES:
#             if re.search(pattern, haystack):
#                 return key, query
#     return DEFAULT_KEY, DEFAULT_QUERY

# def fetch_pexels_images(query, count=3):
#     if not PEXELS_API_KEY:
#         raise RuntimeError('PEXELS_API_KEY not configured')
#     resp = requests.get(
#         'https://api.pexels.com/v1/search',
#         headers={'Authorization': PEXELS_API_KEY},
#         params={'query': query, 'per_page': count, 'orientation': 'landscape'},
#         timeout=8,
#     )
#     resp.raise_for_status()
#     return [
#         {
#             'url': p['src']['large'],
#             'thumb': p['src']['medium'],
#             'alt': p.get('alt') or query,
#             'photographer': p.get('photographer', ''),
#             'photographer_url': p.get('photographer_url', ''),
#             'source_url': p.get('url', ''),
#         }
#         for p in resp.json().get('photos', [])
#     ]

# def get_images_for_scenario(title, text, count=3):
#     key, query = resolve_keyword(title, text)
#     with _cache_lock:
#         cached = _image_cache.get(key)
#     if cached:
#         return key, cached, True

#     images = fetch_pexels_images(query, count)
#     if images:  # never cache empty results
#         with _cache_lock:
#             _image_cache[key] = images
#             _save_image_cache()
#     return key, images, False


# @scenario_bp.route('/images', methods=['GET'])
# def scenario_images():
#     """GET /api/scenario/images?title=...&text=..."""
#     try:
#         title = request.args.get('title', '').strip()
#         text = request.args.get('text', '').strip()
#         if not title and not text:
#             return jsonify({'error': 'title or text is required'}), 400

#         key, images, from_cache = get_images_for_scenario(title, text)
#         logger.info(f"[IMAGES] keyword='{key}' cached={from_cache} count={len(images)}")
#         return jsonify({'success': True, 'keyword': key, 'cached': from_cache, 'images': images}), 200
#     except Exception as e:
#         logger.error(f"[IMAGES ERROR] {e}")
#         # Return 200 with empty list so the UI simply hides the photo panel
#         return jsonify({'success': False, 'images': [], 'error': str(e)}), 200

    
# # At the bottom of your scenario_simulator.py, replace the routes section with this:

# # ============================================================
# # ROUTES - NO OPTIONS HANDLING (app.py handles it globally)
# # ============================================================

# @scenario_bp.route('/health', methods=['GET', 'POST'])
# def health():
#     """Health check for scenario simulator"""
#     return jsonify({
#         'status': 'healthy',
#         'module': 'scenario_simulator',
#         'version': '1.0.0',
#         'groq_configured': bool(groq_client),
#         'replicate_configured': bool(REPLICATE_API_TOKEN)
#     }), 200


# @scenario_bp.route('/generate', methods=['POST'])
# def generate_scenario():
#     """Generate a scenario with story only (no image)"""
#     try:
#         data = request.get_json()
        
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400
        
#         scenario_text = data.get('scenario_text', '').strip()
        
#         if not scenario_text:
#             return jsonify({'error': 'scenario_text is required'}), 400
        
#         if len(scenario_text) < 10:
#             return jsonify({'error': 'Scenario description too short (min 10 characters)'}), 400
        
#         logger.info(f"[SCENARIO] Generating for: {scenario_text[:100]}...")
        
#         # Generate story using Groq
#         story_result = generate_scenario_story(scenario_text)
        
#         if not story_result.get('success'):
#             return jsonify({
#                 'error': 'Failed to generate story',
#                 'details': story_result.get('error')
#             }), 500
        
#         # Success response WITHOUT image
#         logger.info(f"[SCENARIO] ✅ Successfully generated scenario: {story_result['title']}")
        
#         return jsonify({
#             'success': True,
#             'title': story_result['title'],
#             'story': story_result['story'],
#             'tagline': story_result['tagline'],
#             'category': data.get('category', 'general'),
#             'generation_time': story_result.get('generation_time')
#         }), 200

#     except Exception as e:
#         logger.error(f"[SCENARIO ERROR] {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             'error': 'Internal server error',
#             'details': str(e)
#         }), 500


# import random


# SCENARIO_POOL = [
#     # === HOME & PROPERTY (5 scenarios) ===
#     {
#         'id': 1,
#         'title': 'Basement Flooding Risk During Spring Snowmelt and Thaw',
#         'description': '''Spring arrives and snowmelt begins — but not every basement handles it equally. In many Ontario and Alberta neighbourhoods, low-lying lots and aging drainage infrastructure turn March and April into an annual anxiety test for homeowners.

# **What to look for:**
# - Lot grading that slopes away from the foundation (not toward it)
# - Sump pump installation with a battery backup
# - No history of water intrusion (ask for receipts, not promises)
# - Municipal storm sewer capacity in the area
# - Weeping tile condition (inspectors can camera-scope it)

# Properties on elevated lots or newer developments with updated drainage bylaws carry significantly lower risk. A home on a ridge line drains naturally; one in a hollow collects. Checking the city's flood risk maps before making an offer takes 10 minutes and could save you tens of thousands.

# **Tagline:** Where dry basements mean worry-free winters.''',
#         'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
#         'category': 'home'
#     },
#     {
#         'id': 2,
#         'title': 'Proximity to Community Hockey Rinks and Public Trails',
#         'description': '''For Canadian families, weekend life orbits around the rink and the trail. Whether it's 6 AM hockey practice, a Saturday afternoon skate, or a groomed cross-country ski loop through conservation land, proximity to these amenities isn't a bonus — it's a lifestyle decision.

# **What's nearby:**
# - Municipal arena with public skating, hockey leagues, and learn-to-skate programs (1.2 km)
# - 18 km of groomed multi-use trail connecting to the Trans Canada Trail network
# - Two outdoor rinks maintained by the city from November through February
# - Off-leash dog trail through the adjacent ravine
# - Cycling path linking the neighbourhood to the downtown waterfront

# Parents in this area skip the 40-minute arena drives that define suburban hockey life elsewhere. Kids cycle to the outdoor rink after school in winter. Summer trails become running routes, mountain bike paths, and family weekend walks. The outdoors is genuinely within reach.

# **Tagline:** Step outside and into the Canadian outdoors.''',
#         'image_url': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop',
#         'category': 'lifestyle'
#     },
#     {
#         'id': 3,
#         'title': 'Reliance on GO Transit/LRT with Heated Platform Access',
#         'description': '''Commuting without a car in Canada demands infrastructure that takes winter seriously. Standing on an exposed platform at -15°C waiting for a delayed train isn't a minor inconvenience — it's a factor in whether transit is actually usable long-term.

# **Transit profile for this location:**
# 7:12 AM — Walk 6 minutes to Clarkson GO Station
# 7:18 AM — Board GO Train (heated waiting area, enclosed platform)
# 8:10 AM — Arrive Union Station, downtown Toronto
# 8:18 AM — Arrive at Bay Street office via PATH network (no outdoor walking)

# The Eglinton Crosstown LRT stop is 400 metres from the front door. Enclosed stations with real-time arrivals, heated waiting zones, and Level Access boarding make the system usable for elderly riders, parents with strollers, and anyone who values their Thursday morning in January. Monthly GO pass costs approximately $190 — significantly below downtown parking.

# **Tagline:** Commuting in comfort, even at -20°C.''',
#         'image_url': 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400&h=300&fit=crop',
#         'category': 'transit'
#     },
#     {
#         'id': 4,
#         'title': 'Quiet Cul-de-Sac Away from Flight Paths and Highways',
#         'description': '''You found the house. Perfect layout, great yard, reasonable price. Then you notice the Pearson flight path cutting directly overhead. Or the 401 noise wall visible from the back deck. What looks like a deal often carries a hidden cost measured in sleep quality and outdoor livability.

# This cul-de-sac sits in a noise-mapped quiet zone. The nearest highway is 3.2 km away with a natural sound buffer of mature maple and pine. Pearson's primary approach corridors don't cross this area. The street has six homes and no through traffic — the only vehicles you'll hear are your neighbours.

# Evening decibel levels hover around 38-42 dB (comparable to a quiet library). Residents keep windows open through June and September. Children play on the street without parents watching from behind a fence. The backyard is genuinely usable for morning coffee and evening meals, not just lawn maintenance.

# **Tagline:** Peace and quiet is a feature, not a luxury.''',
#         'image_url': 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&h=300&fit=crop',
#         'category': 'lifestyle'
#     },
#     {
#         'id': 5,
#         'title': 'High-Speed Fiber Internet for Remote "Cottage Country" Work',
#         'description': '''The promise of remote work collapses without reliable internet. Thousands of Canadians discovered this when they moved to Muskoka, Prince Edward County, or the Kawarthas only to find that their Zoom calls froze and their upload speeds peaked at 3 Mbps.

# This property is serviced by Bell Fibe gigabit infrastructure — not LTE backup, not DSL, not a rural fixed wireless solution that degrades in rain. Symmetrical 940 Mbps up and down, with a router that covers the main floor, the loft office, and the backyard deck.

# **Confirmed speeds (from existing owner logs):**
# - Download: 924 Mbps
# - Upload: 918 Mbps
# - Latency: 8 ms to Toronto servers
# - Reliability: 99.4% uptime over 18 months

# Video calls with 12 participants, large file uploads to cloud storage, and simultaneous 4K streaming coexist without conflict. You work with the lake out the window. The city is 90 minutes away for the days you need to be there.

# **Tagline:** Lakeside mornings, big-city productivity.''',
#         'image_url': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400&h=300&fit=crop',
#         'category': 'home'
#     },
#     {
#         'id': 6,
#         'title': 'Homes with Legal Basement Suites for Mortgage Assistance',
#         'description': '''At current interest rates, a second income stream isn't a nice-to-have — for many buyers, it's what makes the mortgage math work. A legal basement suite (registered with the city, separately metered, up to fire code) generates between $1,400 and $2,200/month in rental income in most major Canadian markets.

# This 4-bedroom detached home includes a fully legal 1-bedroom basement suite with:
# - Separate entrance from the side of the home
# - Independent electrical panel and water meter
# - Egress windows to current Ontario building code
# - Full kitchen, bathroom, and in-unit laundry
# - City permit on file (no retroactive legalization required)

# Current tenant pays $1,750/month on a month-to-month lease. At a 6.2% mortgage rate on a $900,000 purchase with 20% down, the rental income offsets approximately $290,000 of effective mortgage principal. That's the difference between stretching and breathing.

# **Tagline:** Your tenant helps pay for your home.''',
#         'image_url': 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=400&h=300&fit=crop',
#         'category': 'home'
#     },
#     {
#         'id': 7,
#         'title': 'Winter-Ready Attached Garage and Snow-Clearing Route Access',
#         'description': '''By the third week of January, the romance of a Canadian winter has fully evaporated. What remains is the daily reality: brushing off the car, shovelling the driveway, and waiting for the salt truck before you can safely reverse out. An attached garage doesn't just protect your vehicle — it changes your morning entirely.

# **Winter logistics from this property:**
# - Double attached garage with automatic door opener, heated to 5°C minimum
# - Driveway is 28 feet — qualifies for city's priority snow-clearing route
# - Covered walkway from garage directly into mudroom (no outdoor exposure)
# - Interlocking driveway with heated edge strips to reduce ice formation
# - Street is plowed within 4 hours of any snowfall over 5 cm

# You leave for work in a warm car, without scraping, without worrying whether you can exit the driveway. Grandparents visit without slipping. The side door means groceries go from trunk to kitchen in eight steps. Small design decisions that compound into a genuinely easier winter.

# **Tagline:** Scraping ice is optional when you plan ahead.''',
#         'image_url': 'https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=400&h=300&fit=crop',
#         'category': 'home'
#     },
#     {
#         'id': 8,
#         'title': 'Energy-Efficient Builds with Heat Pumps for -30°C Winters',
#         'description': '''A natural gas furnace in a poorly insulated 1990s build can cost $4,800/year to heat in Northern Ontario winters. A cold-climate heat pump in a well-insulated new build can do the same job for $1,100 — and cool your home in summer without a separate system.

# This 2023 Tarion-warranted build achieves a Net Zero Ready certification from Natural Resources Canada. Key specs:

# **Thermal envelope:**
# - R-30 walls, R-60 attic, R-20 under slab
# - Triple-pane argon-filled windows (U-0.17)
# - Air tightness: 0.6 ACH @ 50 Pa (exceeds Step 5 BC Energy Code)

# **Mechanical system:**
# - Mitsubishi Zuba-Central cold-climate heat pump rated to -30°C
# - HRV (Heat Recovery Ventilator) for fresh air without heat loss
# - Smart thermostat with utility rate optimization

# **Projected annual energy cost:** $1,240 (gas equivalent would be $4,100+)

# The Canada Greener Homes Grant covers $5,000 of the heat pump installation cost.

# **Tagline:** Warm home, lower bills, cleaner future.''',
#         'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
#         'category': 'home'
#     },
#     {
#         'id': 9,
#         'title': 'Walking Distance to LCBO, Loblaws, and Local Libraries',
#         'description': '''Car dependency is expensive, time-consuming, and — for elderly residents, teenagers, and anyone between vehicles — a real barrier to daily life. A walkable neighbourhood isn't just convenient; for many buyers, it's a long-term quality-of-life decision.

# **Walk Score: 87 (Very Walkable)**

# Within 800 metres of this address:
# - Loblaws (full grocery, pharmacy, Joe Fresh) — 6-minute walk
# - LCBO — 7-minute walk
# - Oakville Public Library branch — 9-minute walk
# - TD Bank, RBC, and Scotiabank branches
# - Independent coffee shop, dry cleaner, and dentist
# - Transit stop with 10-minute frequency during peak hours

# You don't own a car and you don't need one for everyday errands. Teenagers can move independently. When one car is in the shop, the household doesn't grind to a halt. Retirement becomes easier to imagine when the infrastructure supports it.

# **Tagline:** Everything you need, steps from your door.''',
#         'image_url': 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=400&h=300&fit=crop',
#         'category': 'lifestyle'
#     },
#     {
#         'id': 10,
#         'title': 'Wildfire-Resilient Landscaping in High-Risk Wooded Areas',
#         'description': '''BC's wildfire interface zone now includes communities that weren't on anyone's risk map a decade ago. Kelowna, Kamloops, and hundreds of smaller communities have learned that proximity to beautiful forested land comes with a responsibility — and sometimes a bill — that buyers rarely factor into their purchase decision.

# This property has been professionally assessed and retrofitted to FireSmart Canada standards:

# **Structure:**
# - Metal roof and ember-resistant vents (no mesh gaps over 1.6 mm)
# - Non-combustible cladding on lower 1.5 metres of exterior walls
# - Multi-pane windows with tempered glass

# **Landscaping (Zone 1 — within 1.5 metres of structure):**
# - No combustible materials (wood mulch, cedar hedges removed)
# - Gravel surround and stone patio

# **Zone 2 (1.5–10 metres):**
# - Low-growing, high-moisture native plants replacing dry grass
# - Tree canopy thinned to 3-metre separation between crowns

# Insurance premium reduced 18% following FireSmart certification.

# **Tagline:** Beautiful property, built to endure.''',
#         'image_url': 'https://images.unsplash.com/photo-1601979031925-424e53b6caaa?w=400&h=300&fit=crop',
#         'category': 'safety'
#     },

#     # === SCHOOL CATCHMENT (5 scenarios) ===
#     {
#         'id': 11,
#         'title': 'Within Strict Boundaries for Top-Ranked Secondary Schools',
#         'description': '''Secondary school catchment boundaries in Ontario, BC, and Alberta are drawn street by street — and the difference between one side of a road and the other can mean the difference between a top-decile school and a mid-tier one. Buyers who don't verify the boundary before signing a deal sometimes discover this after closing.

# This address falls within the confirmed catchment for Westmount Secondary, ranked in the top 4% of Ontario public schools by the Fraser Institute (2024 edition). Enrolment is guaranteed by address; no lottery, no application process.

# **School profile:**
# - Fraser Institute score: 9.2/10
# - University acceptance rate: 91% (class of 2023)
# - IB Programme offered (one of 14 schools in the region)
# - STEM specialization stream
# - Average class size: 22 students

# The boundary has been stable for 11 years with no redistricting proposals on record. Neighbouring streets west of Trafalgar Road fall into a different catchment with a Fraser score of 5.7.

# **Tagline:** The right address opens the right doors.''',
#         'image_url': 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=400&h=300&fit=crop',
#         'category': 'school'
#     },
#     {
#         'id': 12,
#         'title': 'Short Walking Distance to French Immersion Elementary Schools',
#         'description': '''French Immersion waitlists in most major Canadian cities are long — sometimes years long. But proximity to the school doesn't guarantee enrollment in a competitive program. What it does mean is that once your child is enrolled, the daily logistics become dramatically simpler.

# The designated French Immersion feeder school for this address is École Riverside, 550 metres away via a signalized pedestrian crossing. No highway crossings, no stroller-unfriendly curbs, and a school crossing guard stationed at the intersection from 8:00–8:45 AM and 3:00–3:45 PM.

# **Program details:**
# - Early French Immersion: entry at JK (full French instruction)
# - Late French Immersion: entry at Grade 4
# - Graduates continue to Collège Frontenac (3.1 km, transit served)
# - After-school French tutoring program run by parent council

# Parents on this street routinely walk children to school together. The route passes through a small park with a splash pad — a genuine improvement over a 20-minute drive to a different catchment school.

# **Tagline:** Bilingual futures begin on the walk to school.''',
#         'image_url': 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400&h=300&fit=crop',
#         'category': 'school'
#     },
#     {
#         'id': 13,
#         'title': 'Property Falls Under a Specific Catholic (Separate) School Board',
#         'description': '''In Ontario, a property's municipal address determines not just which public school board serves it, but whether it falls under the publicly funded Catholic (Separate) school board catchment. This matters deeply to families seeking faith-based education without private school tuition — and it's entirely determined by where you live.

# This property is confirmed within the Halton Catholic District School Board catchment, with the following feeder schools:

# **Elementary:** St. Patrick Catholic Elementary School (680 m, walking distance)
# - Full sacramental preparation program
# - Faith-integrated curriculum across all subjects
# - Hot lunch program

# **Secondary:** Bishop Reding Catholic Secondary School (2.4 km, bus served)
# - Fraser Institute score: 8.1/10
# - Chaplaincy, retreat, and service-learning programs
# - 94% graduation rate

# Catholic school enrollment is not guaranteed by address alone — at least one parent must be a Catholic separate school supporter on the property tax roll. The listing agent can confirm the tax support designation and assist with the transfer process if needed.

# **Tagline:** Faith-based education, right in your catchment.''',
#         'image_url': 'https://images.unsplash.com/photo-1509062522246-3755977927d7?w=400&h=300&fit=crop',
#         'category': 'school'
#     },
#     {
#         'id': 14,
#         'title': 'High Fraser Institute Ranking for Local Elementary Education',
#         'description': '''The Fraser Institute's annual school rankings draw controversy, but they remain the most widely referenced independent dataset Canadian buyers use when evaluating school catchments. A consistently high-ranking elementary school — one that has held its score across multiple years — signals a stable academic environment that many families treat as a non-negotiable.

# Riverside Meadows Elementary (the feeder school for this address) has scored between 8.4 and 9.1 out of 10 over the past six years, placing it consistently in the top 8% of British Columbia public elementary schools.

# **What drives the ranking:**
# - Foundation Skills Assessment (FSA) results in reading, writing, and numeracy
# - Scores reported over a 5-year rolling average (not a single-year blip)
# - School improvement trend included in published methodology

# **What the ranking doesn't capture:** arts programs, French Immersion availability, extracurricular range, and teacher tenure — worth visiting the school to assess directly.

# The ranking has been stable enough that families on adjacent streets have explicitly purchased on this side of the block to secure catchment.

# **Tagline:** Data-backed schools, peace-of-mind parenting.''',
#         'image_url': 'https://images.unsplash.com/photo-1471286174890-9c112ac6476d?w=400&h=300&fit=crop',
#         'category': 'school'
#     },
#     {
#         'id': 15,
#         'title': 'Avoiding "Holding Schools" in New Suburban Developments',
#         'description': '''When a new subdivision opens before its permanent school is built, the school board assigns students to a "holding school" — often a portable-heavy facility several kilometres away, sometimes in a different neighbourhood entirely. It's a temporary arrangement that can last 3 to 7 years, and it's something most buyers in new developments discover only after move-in.

# This resale property is in an established neighbourhood served by a permanent, purpose-built school that opened in 2009. There are no outstanding boundary consultations, no planned portable additions, and no history of overflow to holding schools in this subdivision.

# **Red flags buyers should ask about in new builds:**
# - "What school will my child attend at time of occupancy?" (not at project completion)
# - Is a new school funded in the capital budget, or only "proposed"?
# - How many portables does the current feeder school operate?
# - What is the school board's current enrolment vs. capacity for the catchment?

# Purchasing a resale home in a mature neighbourhood with a built school eliminates this uncertainty entirely.

# **Tagline:** A permanent school before you sign on the dotted line.''',
#         'image_url': 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=400&h=300&fit=crop',
#         'category': 'school'
#     },
# ]    
    
# # Track current batch index (shared across all users)
# current_batch_index = 0
# BATCH_SIZE = 6

# @scenario_bp.route('/pre-generated', methods=['GET'])
# def get_pre_generated_scenarios():
#     """Get 5 random pre-generated example scenarios"""
#     try:
#         # Return 5 random scenarios instead of all 40
#         if len(SCENARIO_POOL) < 5:
#             return jsonify({
#                 'error': 'Not enough scenarios in pool',
#                 'available': len(SCENARIO_POOL)
#             }), 400
        
#         random_scenarios = random.sample(SCENARIO_POOL, 5)
        
#         logger.info(f"[PRE-GENERATED] ✅ Returned 5 random scenarios")
        
#         return jsonify({
#             'success': True,
#             'scenarios': random_scenarios,
#             'total_available': len(SCENARIO_POOL)
#         }), 200

#     except Exception as e:
#         logger.error(f"[SCENARIO ERROR] {str(e)}")
#         return jsonify({
#             'error': 'Failed to get scenarios',
#             'details': str(e)
#         }), 500


# @scenario_bp.route('/random', methods=['GET'])
# def get_random_scenarios():
#     """
#     Get next 6 scenarios sequentially from the pool
#     Loops back to start after all 42 scenarios shown (7 batches total)
    
#     Usage: GET /api/scenario/random
#     """
#     global current_batch_index  # ← ADDED: Allow modifying global counter
    
#     try:
#         # Validate pool size
#         if len(SCENARIO_POOL) < 6:
#             return jsonify({
#                 'error': 'Not enough scenarios in pool',
#                 'available': len(SCENARIO_POOL)
#             }), 400
        
#         # ← CHANGED: Sequential logic instead of random
#         # Calculate start and end indices for current batch
#         start_idx = current_batch_index * BATCH_SIZE
#         end_idx = start_idx + BATCH_SIZE
        
#         # Get the sequential batch (scenarios 0-4, then 5-9, etc.)
#         batch_scenarios = SCENARIO_POOL[start_idx:end_idx]
        
#         # Track which batch we're serving (1-8 for display)
#         current_serving = current_batch_index + 1
        
#         # Increment batch index and loop back to 0 after batch 8
#         current_batch_index = (current_batch_index + 1) % 7  # 40 ÷ 5 = 8 batches
        
#         logger.info(f"[SEQUENTIAL] ✅ Returned batch {current_serving}/7 (scenarios {start_idx+1}-{end_idx})")
        
#         # ← CHANGED: Updated return with batch metadata
#         # Add icon field to each scenario if missing
#         for scenario in batch_scenarios:
#             if 'icon' not in scenario:
#                 # Map category to icon
#                 category_icons = {
#                     'family': 'clock',
#                     'elderly': 'shield',
#                     'professional': 'building',
#                     'lifestyle': 'home',
#                     'religion': 'home',
#                     'safety': 'shield',
#                     'transport': 'clock'
#                 }
#                 scenario['icon'] = category_icons.get(scenario.get('category', 'general'), 'building')

#         return jsonify({
#             'success': True,
#             'scenarios': batch_scenarios,
#             'batch_number': current_serving,
#             'total_batches': 7,
#             'total_pool_size': len(SCENARIO_POOL)
#         }), 200
        
#     except Exception as e:
#         logger.error(f"[SEQUENTIAL ERROR] {str(e)}")
#         import traceback
#         traceback.print_exc()
#         return jsonify({
#             'error': 'Failed to get sequential scenarios',
#             'details': str(e)
#         }), 500

"""
Scenario Simulator Module - Single File Version
Generates realistic real estate scenarios with AI-generated narratives
and cached, keyword-matched real photos (Pexels).
"""

from flask import Blueprint, request, jsonify
import os
import time
import logging
import requests
import base64
import json
import re
import math
import random
import threading
from pathlib import Path
from groq import Groq

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURATION
# ============================================================

# Initialize Groq client
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# Replicate API
REPLICATE_API_TOKEN = os.getenv('REPLICATE_API_TOKEN')

# Pexels API (free, real photographs) -> https://www.pexels.com/api/
PEXELS_API_KEY = os.getenv('PEXELS_API_KEY')

# ============================================================
# CREATE BLUEPRINT
# ============================================================

scenario_bp = Blueprint('scenario', __name__, url_prefix='/api/scenario')

# CORS is handled globally in app.py

# ============================================================
# SERVICE FUNCTIONS - STORY GENERATION
# ============================================================


def generate_scenario_story(scenario_text):
    """
    Generate context-aware scenario narratives using Groq
    - Timeline format for time-based/emergency scenarios
    - Narrative format for lifestyle/emotional scenarios
    Expected time: 1-2 seconds
    """
    try:
        if not groq_client:
            return {
                'success': False,
                'error': 'GROQ_API_KEY not configured'
            }

        start_time = time.time()

        prompt = f"""Analyze this real estate scenario: "{scenario_text}"

**STEP 1: IDENTIFY THE SCENARIO TYPE**
- Does it mention a specific TIME (3 AM, 9 AM, etc.)? → Use TIMELINE format
- Is it an EMERGENCY (fever, hospital, urgent)? → Use TIMELINE format
- Is it ROUTINE with time sensitivity (school, work, airport)? → Use TIMELINE format
- Is it LIFESTYLE/EMOTIONAL (safety, noise, leisure, peace)? → Use NARRATIVE format

**STEP 2: GENERATE THE RESPONSE**

---
## FOR TIMELINE FORMAT (Emergency/Time-based scenarios):
---

TITLE: [Action-focused title, 5-8 words]

SCENARIO:
[Opening line: Set the situation - 1 complete sentence]

**Timeline:**
[TIME] — [Action step 1]
[TIME] — [Action step 2]
[TIME] — [Action step 3]
[TIME] — [Outcome/arrival]

**Transport Options Available:**
- [Option 1: e.g., Own Vehicle - Direct basement access, no parking delay]
- [Option 2: e.g., School Bus - Picks up from community gate]
- [Option 3: e.g., Taxi/Cab - 2-min wait time, AED 15-25]
- [Option 4: e.g., RTA Bus/Metro - Nearest station 800m]

[Closing paragraph: MAX 3 sentences explaining why this location makes it easy]

TAGLINE: [Practical benefit statement]

**EXAMPLE 1 (Emergency at specific time):**
TITLE: Crisis to Care in 9 Minutes

SCENARIO:
It's 3 AM, and your son's fever has spiked to 104°F. You need to reach the hospital immediately.

**Timeline:**
3:00 AM — Discover high fever, make the decision to go to ER
3:02 AM — Wake up, grab emergency documents and medications
3:05 AM — Exit apartment building, security gate opens instantly
3:09 AM — Arrive at City Pediatric Hospital emergency entrance

**Transport Options Available:**
- Own Vehicle - Direct basement parking access, start immediately
- Taxi/Cab - Book via app, 3-4 minute arrival time, AED 25-40
- Ambulance - Community emergency hotline, 5-minute response time
- Neighbor's Vehicle - WhatsApp group emergency protocol active

The hospital is only 2.3 kilometers away via a wide arterial road with zero traffic at night. The 24/7 manned security ensures the gate opens immediately without fumbling for access cards. While families in congested areas waste 20+ minutes, you're already in the ER getting treatment.

TAGLINE: In medical emergencies, proximity saves lives.

**EXAMPLE 2 (Routine with goal time):**
TITLE: School Run in Under 30 Minutes

SCENARIO:
Your son's school starts at 9 AM sharp, and he cannot be late.

**Timeline:**
8:35 AM — Finish breakfast and pack school bag
8:40 AM — Leave apartment, walk to parking area
8:45 AM — Start driving via the service road
8:55 AM — Arrive at school gate, 5 minutes early

**Transport Options Available:**
- School Bus - Picks up from community gate at 8:15 AM daily
- Own Vehicle - Basement parking, 10-minute direct drive
- Carpool - Rotate with 3 neighbor families via WhatsApp
- Taxi/Cab - Available at gate, AED 20-35 per trip

The school is just 3.5 kilometers away via a signal-free stretch of road. No narrow lanes, no U-turns, no traffic chaos. While other parents leave home at 8 AM to fight congestion, you're finishing breakfast in peace.

TAGLINE: Convenience isn't a perk. It's a parenting essential.

---
## FOR NARRATIVE FORMAT (Lifestyle/Emotional scenarios):
---

TITLE: [Emotional/evocative title, 5-8 words]

SCENARIO:
[Paragraph 1: Set the scene with sensory details - MAX 3 sentences only]

[Paragraph 2: Show the contrast or problem - MAX 3 sentences only]

[Paragraph 3: How the property solves it - MAX 3 sentences with specific features]

[Paragraph 4: Emotional impact - MAX 2 sentences only]

TAGLINE: [Memorable emotional statement]

**EXAMPLE:**
TITLE: Serenity Found

SCENARIO:
Imagine waking up to the sweet songs of birds and the gentle rustle of leaves. Your home is surrounded by lush green parks visible from every window. The fresh air and soothing views create a sense of tranquility from the very first morning.

As you step out, vibrant flowers and open walkways greet you. The parks offer a serene escape where children play freely and families gather for evening walks. It's a stark contrast to the noise and congestion most city dwellers accept as normal.

Inside, triple-glazed windows and an 80-meter green buffer zone ensure city noise never intrudes. Your children can study without distractions, and you can work from home with windows open. This isn't clever architecture — it's designed wellness for your entire family.

The true luxury isn't marble lobbies or imported fittings. It's the ability to hear yourself think, sleep deeply, and wake up refreshed every single morning.

TAGLINE: Find your inner peace in perfect harmony with nature.

---

**CRITICAL RULES:**
- TOTAL LENGTH: 180-220 words (not counting title/tagline)
- TIMELINE FORMAT: Always include ALL 4 sections — Opening line, Timeline (4 steps), Transport Options (4 options), Closing paragraph. NEVER skip any section.
- NARRATIVE FORMAT: Always include ALL 4 paragraphs. NEVER skip any paragraph.
- Each paragraph: MAXIMUM 3 sentences, keep it concise
- Currency: STRICTLY use INR (Indian Rupees, ₹) ONLY. NEVER use AED, $, €, or any other currency. Every single price must be in ₹. Example: ₹25-40, ₹200-350
- **TIMELINE TIME ANCHORING**: If user mentions a specific time (e.g., "3 AM", "9 AM"), START the timeline at that EXACT time or slightly before
- Timeline format: Each time step on NEW LINE with clear formatting
- Timeline intervals: Use realistic 2-5 minute gaps between steps
- Transport options: Each option on NEW LINE with dash (-)
- NEVER end mid-sentence - always complete every paragraph
- For narrative: Write in complete, flowing paragraphs
- Make every sentence complete and grammatically correct
- End with proper punctuation (. ! ?)

**OUTPUT FORMAT:**
TITLE: [Title here]

SCENARIO:
[Content with proper line breaks and formatting]

TAGLINE: [Tagline here]"""

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert real estate scenario writer based in Dubai, UAE. You create two types of content:

1. TIMELINE scenarios: Use clear line breaks for each time step. Format like:
   8:45 AM — Action here
   8:50 AM — Next action
   
   CRITICAL: If the user mentions a specific time (like "3 AM" or "9 AM"), your timeline MUST start at or near that time. DO NOT start from midnight (12:00 AM) or any other arbitrary time. Examples:
   - User says "3 AM emergency" → Start timeline at 3:00 AM
   - User says "9 AM school" → Start timeline around 8:35-8:45 AM
   - User says "midnight fever" → Start timeline at 12:00 AM

2. NARRATIVE scenarios: Write in complete, flowing paragraphs with MAXIMUM 3 sentences per paragraph. NEVER end mid-sentence.

CRITICAL CURRENCY RULE: You are writing for India. EVERY price MUST be in INR (Indian Rupees, symbol ₹). NEVER use AED, $, £, € or any other currency under any circumstance. If you use any currency other than ₹/INR, the response is considered a failure.

CRITICAL COMPLETENESS RULE: For TIMELINE format, you MUST always include ALL of these sections in order:
1. Opening sentence
2. Timeline with exactly 4 steps
3. Transport Options with exactly 4 options
4. Closing paragraph (3 sentences)
5. Tagline
NEVER skip or shorten any section. A missing section is a failed response.

For NARRATIVE format, you MUST always include ALL 4 paragraphs. NEVER skip any paragraph.

Keep each paragraph to a maximum of 3 sentences.
Always finish every sentence completely. Never truncate words or leave sentences incomplete."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="openai/gpt-oss-120b",
            temperature=0.7,
            max_tokens=2000,
            reasoning_effort="low",
            stop=None
        )

        response_text = chat_completion.choices[0].message.content.strip()

        # Enhanced parsing that preserves formatting
        lines = response_text.split('\n')
        title = ""
        story_content = []
        tagline = ""

        current_section = None
        collecting_story = False

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("TITLE:"):
                title = stripped.replace("TITLE:", "").strip()
                current_section = "title"

            elif stripped.startswith("SCENARIO:"):
                current_section = "story"
                collecting_story = True

            elif stripped.startswith("TAGLINE:"):
                tagline = stripped.replace("TAGLINE:", "").strip()
                current_section = "tagline"
                collecting_story = False

            elif collecting_story and current_section == "story":
                story_content.append(line)

        # Clean up story content - remove leading/trailing empty lines only
        while story_content and not story_content[0].strip():
            story_content.pop(0)
        while story_content and not story_content[-1].strip():
            story_content.pop()

        # Check if last line ends mid-sentence
        if story_content:
            last_line = story_content[-1].strip()
            if last_line and last_line[-1] not in '.!?':
                full_text = '\n'.join(story_content)
                last_period = max(full_text.rfind('.'), full_text.rfind('!'), full_text.rfind('?'))

                if last_period > 0:
                    full_text = full_text[:last_period + 1]
                    story_content = full_text.split('\n')
                    logger.warning("[GROQ] Truncated incomplete sentence")

        # Convert story_content to paragraphs
        story_paragraphs = []
        current_para = []

        for line in story_content:
            stripped = line.strip()
            if not stripped:
                if current_para:
                    story_paragraphs.append('\n'.join(current_para))
                    current_para = []
            else:
                current_para.append(line)

        if current_para:
            story_paragraphs.append('\n'.join(current_para))

        generation_time = time.time() - start_time

        logger.info(f"[GROQ] ✅ Scenario generated in {generation_time:.2f}s")
        logger.info(f"[GROQ] Generated {len(story_paragraphs)} paragraphs")

        return {
            'success': True,
            'title': title,
            'story': story_paragraphs,
            'tagline': tagline,
            'generation_time': f"{generation_time:.2f}s"
        }

    except Exception as e:
        logger.error(f"[GROQ ERROR] {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================
# SERVICE FUNCTIONS - IMAGE SERVICE (Pexels + cache)
# ============================================================

IMAGE_CACHE_FILE = Path(os.getenv('IMAGE_CACHE_FILE', 'scenario_image_cache.json'))
_cache_lock = threading.Lock()


def _load_image_cache():
    try:
        if IMAGE_CACHE_FILE.exists():
            return json.loads(IMAGE_CACHE_FILE.read_text(encoding='utf-8'))
    except Exception as e:
        logger.warning(f"[IMAGES] Could not load cache: {e}")
    return {}


_image_cache = _load_image_cache()


def _save_image_cache():
    try:
        IMAGE_CACHE_FILE.write_text(json.dumps(_image_cache), encoding='utf-8')
    except Exception as e:
        logger.warning(f"[IMAGES] Could not save cache: {e}")


# (regex of trigger words, cache key, search query that gives realistic photos)
# ORDER MATTERS: more specific rules first.
KEYWORD_RULES = [
    (r'\b(gym|fitness|workout|yoga|exercise)\b', 'gym', 'modern gym interior fitness equipment'),
    (r'\b(hospital|emergency|clinic|fever|ambulance|medical|doctor)\b', 'hospital', 'hospital building exterior modern'),
    (r'\b(restaurant|dining|cafe|coffee|food|brunch|dinner)\b', 'dining', 'restaurant interior dining cozy'),
    (r'\b(hockey|rink|skating|trail|trails|hiking|cycling)\b', 'outdoor-rec', 'community park walking trail'),
    (r'\b(park|parks|garden|green|playground|nature)\b', 'park', 'city park green trees residential'),
    (r'\b(school|schools|catchment|elementary|secondary|education|library|libraries)\b', 'school', 'school building exterior students'),
    (r'\b(transit|metro|train|lrt|subway|station|commute|bus)\b', 'transit', 'modern train station platform commuters'),
    (r'\b(mall|shopping|grocery|groceries|supermarket|walkable)\b', 'shopping', 'shopping street supermarket exterior'),
    (r'\b(basement|flood|flooding|drainage|sump)\b', 'basement', 'finished basement suite interior'),
    (r'\b(garage|snow|winter|driveway)\b', 'winter-home', 'suburban house snow driveway garage'),
    (r'\b(fiber|internet|wifi|remote work|cottage)\b', 'remote-work', 'home office remote work lake view'),
    (r'\b(wildfire|fire)\b', 'wildfire', 'house forest landscaping stone gravel'),
    (r'\b(energy|heat pump|insulation|solar)\b', 'energy', 'modern energy efficient house exterior'),
    (r'\b(quiet|noise|peace|cul-de-sac|serenity)\b', 'quiet', 'quiet residential street cul-de-sac trees'),
    (r'\b(security|safety|safe)\b', 'security', 'gated residential community entrance'),
    (r'\b(temple|church|mosque|prayer|worship)\b', 'worship', 'place of worship exterior architecture'),
    (r'\b(pool|swimming|clubhouse|amenit)\w*', 'amenities', 'apartment building swimming pool amenities'),
]
DEFAULT_KEY = 'residential'
DEFAULT_QUERY = 'modern residential apartment building exterior'


def resolve_keyword(title, text):
    """Title first (most specific), then the longer text. Returns (cache_key, search_query)."""
    for haystack in ((title or '').lower(), (text or '').lower()):
        for pattern, key, query in KEYWORD_RULES:
            if re.search(pattern, haystack):
                return key, query
    return DEFAULT_KEY, DEFAULT_QUERY


def fetch_pexels_images(query, count=3):
    if not PEXELS_API_KEY:
        raise RuntimeError('PEXELS_API_KEY not configured')
    resp = requests.get(
        'https://api.pexels.com/v1/search',
        headers={'Authorization': PEXELS_API_KEY},
        params={'query': query, 'per_page': count, 'orientation': 'landscape'},
        timeout=8,
    )
    resp.raise_for_status()
    return [
        {
            'url': p['src']['large'],
            'thumb': p['src']['medium'],
            'alt': p.get('alt') or query,
            'photographer': p.get('photographer', ''),
            'photographer_url': p.get('photographer_url', ''),
            'source_url': p.get('url', ''),
        }
        for p in resp.json().get('photos', [])
    ]


def get_images_for_scenario(title, text, count=1):
    key, query = resolve_keyword(title, text)
    with _cache_lock:
        cached = _image_cache.get(key)
    if cached:
        return key, cached, True

    images = fetch_pexels_images(query, count)
    if images:  # never cache empty results
        with _cache_lock:
            _image_cache[key] = images
            _save_image_cache()
    return key, images, False


# ============================================================
# ROUTES - NO OPTIONS HANDLING (app.py handles it globally)
# ============================================================

@scenario_bp.route('/health', methods=['GET', 'POST'])
def health():
    """Health check for scenario simulator"""
    return jsonify({
        'status': 'healthy',
        'module': 'scenario_simulator',
        'version': '1.1.0',
        'groq_configured': bool(groq_client),
        'replicate_configured': bool(REPLICATE_API_TOKEN),
        'pexels_configured': bool(PEXELS_API_KEY),
        'cached_image_keywords': list(_image_cache.keys())
    }), 200


@scenario_bp.route('/generate', methods=['POST'])
def generate_scenario():
    """Generate a scenario with story only (no image)"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        scenario_text = data.get('scenario_text', '').strip()

        if not scenario_text:
            return jsonify({'error': 'scenario_text is required'}), 400

        if len(scenario_text) < 10:
            return jsonify({'error': 'Scenario description too short (min 10 characters)'}), 400

        logger.info(f"[SCENARIO] Generating for: {scenario_text[:100]}...")

        # Generate story using Groq
        story_result = generate_scenario_story(scenario_text)

        if not story_result.get('success'):
            return jsonify({
                'error': 'Failed to generate story',
                'details': story_result.get('error')
            }), 500

        logger.info(f"[SCENARIO] ✅ Successfully generated scenario: {story_result['title']}")

        return jsonify({
            'success': True,
            'title': story_result['title'],
            'story': story_result['story'],
            'tagline': story_result['tagline'],
            'category': data.get('category', 'general'),
            'generation_time': story_result.get('generation_time')
        }), 200

    except Exception as e:
        logger.error(f"[SCENARIO ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


@scenario_bp.route('/images', methods=['GET'])
def scenario_images():
    """GET /api/scenario/images?title=...&text=...  -> keyword-matched, cached photos"""
    try:
        title = request.args.get('title', '').strip()
        text = request.args.get('text', '').strip()
        if not title and not text:
            return jsonify({'error': 'title or text is required'}), 400

        key, images, from_cache = get_images_for_scenario(title, text)
        logger.info(f"[IMAGES] keyword='{key}' cached={from_cache} count={len(images)}")
        return jsonify({
            'success': True,
            'keyword': key,
            'cached': from_cache,
            'images': images
        }), 200
    except Exception as e:
        logger.error(f"[IMAGES ERROR] {e}")
        # Return 200 with empty list so the UI simply hides the photo panel
        return jsonify({'success': False, 'images': [], 'error': str(e)}), 200


# ============================================================
# PRE-GENERATED SCENARIO POOL
# ============================================================

SCENARIO_POOL = [
    # === HOME & PROPERTY ===
    {
        'id': 1,
        'title': 'Basement Flooding Risk During Spring Snowmelt and Thaw',
        'description': '''Spring arrives and snowmelt begins — but not every basement handles it equally. In many Ontario and Alberta neighbourhoods, low-lying lots and aging drainage infrastructure turn March and April into an annual anxiety test for homeowners.

**What to look for:**
- Lot grading that slopes away from the foundation (not toward it)
- Sump pump installation with a battery backup
- No history of water intrusion (ask for receipts, not promises)
- Municipal storm sewer capacity in the area
- Weeping tile condition (inspectors can camera-scope it)

Properties on elevated lots or newer developments with updated drainage bylaws carry significantly lower risk. A home on a ridge line drains naturally; one in a hollow collects. Checking the city's flood risk maps before making an offer takes 10 minutes and could save you tens of thousands.

**Tagline:** Where dry basements mean worry-free winters.''',
        'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
        'category': 'home'
    },
    {
        'id': 2,
        'title': 'Proximity to Community Hockey Rinks and Public Trails',
        'description': '''For Canadian families, weekend life orbits around the rink and the trail. Whether it's 6 AM hockey practice, a Saturday afternoon skate, or a groomed cross-country ski loop through conservation land, proximity to these amenities isn't a bonus — it's a lifestyle decision.

**What's nearby:**
- Municipal arena with public skating, hockey leagues, and learn-to-skate programs (1.2 km)
- 18 km of groomed multi-use trail connecting to the Trans Canada Trail network
- Two outdoor rinks maintained by the city from November through February
- Off-leash dog trail through the adjacent ravine
- Cycling path linking the neighbourhood to the downtown waterfront

Parents in this area skip the 40-minute arena drives that define suburban hockey life elsewhere. Kids cycle to the outdoor rink after school in winter. Summer trails become running routes, mountain bike paths, and family weekend walks. The outdoors is genuinely within reach.

**Tagline:** Step outside and into the Canadian outdoors.''',
        'image_url': 'https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=400&h=300&fit=crop',
        'category': 'lifestyle'
    },
    {
        'id': 3,
        'title': 'Reliance on GO Transit/LRT with Heated Platform Access',
        'description': '''Commuting without a car in Canada demands infrastructure that takes winter seriously. Standing on an exposed platform at -15°C waiting for a delayed train isn't a minor inconvenience — it's a factor in whether transit is actually usable long-term.

**Transit profile for this location:**
7:12 AM — Walk 6 minutes to Clarkson GO Station
7:18 AM — Board GO Train (heated waiting area, enclosed platform)
8:10 AM — Arrive Union Station, downtown Toronto
8:18 AM — Arrive at Bay Street office via PATH network (no outdoor walking)

The Eglinton Crosstown LRT stop is 400 metres from the front door. Enclosed stations with real-time arrivals, heated waiting zones, and Level Access boarding make the system usable for elderly riders, parents with strollers, and anyone who values their Thursday morning in January. Monthly GO pass costs approximately $190 — significantly below downtown parking.

**Tagline:** Commuting in comfort, even at -20°C.''',
        'image_url': 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400&h=300&fit=crop',
        'category': 'transit'
    },
    {
        'id': 4,
        'title': 'Quiet Cul-de-Sac Away from Flight Paths and Highways',
        'description': '''You found the house. Perfect layout, great yard, reasonable price. Then you notice the Pearson flight path cutting directly overhead. Or the 401 noise wall visible from the back deck. What looks like a deal often carries a hidden cost measured in sleep quality and outdoor livability.

This cul-de-sac sits in a noise-mapped quiet zone. The nearest highway is 3.2 km away with a natural sound buffer of mature maple and pine. Pearson's primary approach corridors don't cross this area. The street has six homes and no through traffic — the only vehicles you'll hear are your neighbours.

Evening decibel levels hover around 38-42 dB (comparable to a quiet library). Residents keep windows open through June and September. Children play on the street without parents watching from behind a fence. The backyard is genuinely usable for morning coffee and evening meals, not just lawn maintenance.

**Tagline:** Peace and quiet is a feature, not a luxury.''',
        'image_url': 'https://images.unsplash.com/photo-1449824913935-59a10b8d2000?w=400&h=300&fit=crop',
        'category': 'lifestyle'
    },
    {
        'id': 5,
        'title': 'High-Speed Fiber Internet for Remote "Cottage Country" Work',
        'description': '''The promise of remote work collapses without reliable internet. Thousands of Canadians discovered this when they moved to Muskoka, Prince Edward County, or the Kawarthas only to find that their Zoom calls froze and their upload speeds peaked at 3 Mbps.

This property is serviced by Bell Fibe gigabit infrastructure — not LTE backup, not DSL, not a rural fixed wireless solution that degrades in rain. Symmetrical 940 Mbps up and down, with a router that covers the main floor, the loft office, and the backyard deck.

**Confirmed speeds (from existing owner logs):**
- Download: 924 Mbps
- Upload: 918 Mbps
- Latency: 8 ms to Toronto servers
- Reliability: 99.4% uptime over 18 months

Video calls with 12 participants, large file uploads to cloud storage, and simultaneous 4K streaming coexist without conflict. You work with the lake out the window. The city is 90 minutes away for the days you need to be there.

**Tagline:** Lakeside mornings, big-city productivity.''',
        'image_url': 'https://images.unsplash.com/photo-1593642632823-8f785ba67e45?w=400&h=300&fit=crop',
        'category': 'home'
    },
    {
        'id': 6,
        'title': 'Homes with Legal Basement Suites for Mortgage Assistance',
        'description': '''At current interest rates, a second income stream isn't a nice-to-have — for many buyers, it's what makes the mortgage math work. A legal basement suite (registered with the city, separately metered, up to fire code) generates between $1,400 and $2,200/month in rental income in most major Canadian markets.

This 4-bedroom detached home includes a fully legal 1-bedroom basement suite with:
- Separate entrance from the side of the home
- Independent electrical panel and water meter
- Egress windows to current Ontario building code
- Full kitchen, bathroom, and in-unit laundry
- City permit on file (no retroactive legalization required)

Current tenant pays $1,750/month on a month-to-month lease. At a 6.2% mortgage rate on a $900,000 purchase with 20% down, the rental income offsets approximately $290,000 of effective mortgage principal. That's the difference between stretching and breathing.

**Tagline:** Your tenant helps pay for your home.''',
        'image_url': 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=400&h=300&fit=crop',
        'category': 'home'
    },
    {
        'id': 7,
        'title': 'Winter-Ready Attached Garage and Snow-Clearing Route Access',
        'description': '''By the third week of January, the romance of a Canadian winter has fully evaporated. What remains is the daily reality: brushing off the car, shovelling the driveway, and waiting for the salt truck before you can safely reverse out. An attached garage doesn't just protect your vehicle — it changes your morning entirely.

**Winter logistics from this property:**
- Double attached garage with automatic door opener, heated to 5°C minimum
- Driveway is 28 feet — qualifies for city's priority snow-clearing route
- Covered walkway from garage directly into mudroom (no outdoor exposure)
- Interlocking driveway with heated edge strips to reduce ice formation
- Street is plowed within 4 hours of any snowfall over 5 cm

You leave for work in a warm car, without scraping, without worrying whether you can exit the driveway. Grandparents visit without slipping. The side door means groceries go from trunk to kitchen in eight steps. Small design decisions that compound into a genuinely easier winter.

**Tagline:** Scraping ice is optional when you plan ahead.''',
        'image_url': 'https://images.unsplash.com/photo-1516912481808-3406841bd33c?w=400&h=300&fit=crop',
        'category': 'home'
    },
    {
        'id': 8,
        'title': 'Energy-Efficient Builds with Heat Pumps for -30°C Winters',
        'description': '''A natural gas furnace in a poorly insulated 1990s build can cost $4,800/year to heat in Northern Ontario winters. A cold-climate heat pump in a well-insulated new build can do the same job for $1,100 — and cool your home in summer without a separate system.

This 2023 Tarion-warranted build achieves a Net Zero Ready certification from Natural Resources Canada. Key specs:

**Thermal envelope:**
- R-30 walls, R-60 attic, R-20 under slab
- Triple-pane argon-filled windows (U-0.17)
- Air tightness: 0.6 ACH @ 50 Pa (exceeds Step 5 BC Energy Code)

**Mechanical system:**
- Mitsubishi Zuba-Central cold-climate heat pump rated to -30°C
- HRV (Heat Recovery Ventilator) for fresh air without heat loss
- Smart thermostat with utility rate optimization

**Projected annual energy cost:** $1,240 (gas equivalent would be $4,100+)

The Canada Greener Homes Grant covers $5,000 of the heat pump installation cost.

**Tagline:** Warm home, lower bills, cleaner future.''',
        'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
        'category': 'home'
    },
    {
        'id': 9,
        'title': 'Walking Distance to LCBO, Loblaws, and Local Libraries',
        'description': '''Car dependency is expensive, time-consuming, and — for elderly residents, teenagers, and anyone between vehicles — a real barrier to daily life. A walkable neighbourhood isn't just convenient; for many buyers, it's a long-term quality-of-life decision.

**Walk Score: 87 (Very Walkable)**

Within 800 metres of this address:
- Loblaws (full grocery, pharmacy, Joe Fresh) — 6-minute walk
- LCBO — 7-minute walk
- Oakville Public Library branch — 9-minute walk
- TD Bank, RBC, and Scotiabank branches
- Independent coffee shop, dry cleaner, and dentist
- Transit stop with 10-minute frequency during peak hours

You don't own a car and you don't need one for everyday errands. Teenagers can move independently. When one car is in the shop, the household doesn't grind to a halt. Retirement becomes easier to imagine when the infrastructure supports it.

**Tagline:** Everything you need, steps from your door.''',
        'image_url': 'https://images.unsplash.com/photo-1541339907198-e08756dedf3f?w=400&h=300&fit=crop',
        'category': 'lifestyle'
    },
    {
        'id': 10,
        'title': 'Wildfire-Resilient Landscaping in High-Risk Wooded Areas',
        'description': '''BC's wildfire interface zone now includes communities that weren't on anyone's risk map a decade ago. Kelowna, Kamloops, and hundreds of smaller communities have learned that proximity to beautiful forested land comes with a responsibility — and sometimes a bill — that buyers rarely factor into their purchase decision.

This property has been professionally assessed and retrofitted to FireSmart Canada standards:

**Structure:**
- Metal roof and ember-resistant vents (no mesh gaps over 1.6 mm)
- Non-combustible cladding on lower 1.5 metres of exterior walls
- Multi-pane windows with tempered glass

**Landscaping (Zone 1 — within 1.5 metres of structure):**
- No combustible materials (wood mulch, cedar hedges removed)
- Gravel surround and stone patio

**Zone 2 (1.5–10 metres):**
- Low-growing, high-moisture native plants replacing dry grass
- Tree canopy thinned to 3-metre separation between crowns

Insurance premium reduced 18% following FireSmart certification.

**Tagline:** Beautiful property, built to endure.''',
        'image_url': 'https://images.unsplash.com/photo-1601979031925-424e53b6caaa?w=400&h=300&fit=crop',
        'category': 'safety'
    },

    # === SCHOOL CATCHMENT ===
    {
        'id': 11,
        'title': 'Within Strict Boundaries for Top-Ranked Secondary Schools',
        'description': '''Secondary school catchment boundaries in Ontario, BC, and Alberta are drawn street by street — and the difference between one side of a road and the other can mean the difference between a top-decile school and a mid-tier one. Buyers who don't verify the boundary before signing a deal sometimes discover this after closing.

This address falls within the confirmed catchment for Westmount Secondary, ranked in the top 4% of Ontario public schools by the Fraser Institute (2024 edition). Enrolment is guaranteed by address; no lottery, no application process.

**School profile:**
- Fraser Institute score: 9.2/10
- University acceptance rate: 91% (class of 2023)
- IB Programme offered (one of 14 schools in the region)
- STEM specialization stream
- Average class size: 22 students

The boundary has been stable for 11 years with no redistricting proposals on record. Neighbouring streets west of Trafalgar Road fall into a different catchment with a Fraser score of 5.7.

**Tagline:** The right address opens the right doors.''',
        'image_url': 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=400&h=300&fit=crop',
        'category': 'school'
    },
    {
        'id': 12,
        'title': 'Short Walking Distance to French Immersion Elementary Schools',
        'description': '''French Immersion waitlists in most major Canadian cities are long — sometimes years long. But proximity to the school doesn't guarantee enrollment in a competitive program. What it does mean is that once your child is enrolled, the daily logistics become dramatically simpler.

The designated French Immersion feeder school for this address is École Riverside, 550 metres away via a signalized pedestrian crossing. No highway crossings, no stroller-unfriendly curbs, and a school crossing guard stationed at the intersection from 8:00–8:45 AM and 3:00–3:45 PM.

**Program details:**
- Early French Immersion: entry at JK (full French instruction)
- Late French Immersion: entry at Grade 4
- Graduates continue to Collège Frontenac (3.1 km, transit served)
- After-school French tutoring program run by parent council

Parents on this street routinely walk children to school together. The route passes through a small park with a splash pad — a genuine improvement over a 20-minute drive to a different catchment school.

**Tagline:** Bilingual futures begin on the walk to school.''',
        'image_url': 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400&h=300&fit=crop',
        'category': 'school'
    },
    {
        'id': 13,
        'title': 'Property Falls Under a Specific Catholic (Separate) School Board',
        'description': '''In Ontario, a property's municipal address determines not just which public school board serves it, but whether it falls under the publicly funded Catholic (Separate) school board catchment. This matters deeply to families seeking faith-based education without private school tuition — and it's entirely determined by where you live.

This property is confirmed within the Halton Catholic District School Board catchment, with the following feeder schools:

**Elementary:** St. Patrick Catholic Elementary School (680 m, walking distance)
- Full sacramental preparation program
- Faith-integrated curriculum across all subjects
- Hot lunch program

**Secondary:** Bishop Reding Catholic Secondary School (2.4 km, bus served)
- Fraser Institute score: 8.1/10
- Chaplaincy, retreat, and service-learning programs
- 94% graduation rate

Catholic school enrollment is not guaranteed by address alone — at least one parent must be a Catholic separate school supporter on the property tax roll. The listing agent can confirm the tax support designation and assist with the transfer process if needed.

**Tagline:** Faith-based education, right in your catchment.''',
        'image_url': 'https://images.unsplash.com/photo-1509062522246-3755977927d7?w=400&h=300&fit=crop',
        'category': 'school'
    },
    {
        'id': 14,
        'title': 'High Fraser Institute Ranking for Local Elementary Education',
        'description': '''The Fraser Institute's annual school rankings draw controversy, but they remain the most widely referenced independent dataset Canadian buyers use when evaluating school catchments. A consistently high-ranking elementary school — one that has held its score across multiple years — signals a stable academic environment that many families treat as a non-negotiable.

Riverside Meadows Elementary (the feeder school for this address) has scored between 8.4 and 9.1 out of 10 over the past six years, placing it consistently in the top 8% of British Columbia public elementary schools.

**What drives the ranking:**
- Foundation Skills Assessment (FSA) results in reading, writing, and numeracy
- Scores reported over a 5-year rolling average (not a single-year blip)
- School improvement trend included in published methodology

**What the ranking doesn't capture:** arts programs, French Immersion availability, extracurricular range, and teacher tenure — worth visiting the school to assess directly.

The ranking has been stable enough that families on adjacent streets have explicitly purchased on this side of the block to secure catchment.

**Tagline:** Data-backed schools, peace-of-mind parenting.''',
        'image_url': 'https://images.unsplash.com/photo-1471286174890-9c112ac6476d?w=400&h=300&fit=crop',
        'category': 'school'
    },
    {
        'id': 15,
        'title': 'Avoiding "Holding Schools" in New Suburban Developments',
        'description': '''When a new subdivision opens before its permanent school is built, the school board assigns students to a "holding school" — often a portable-heavy facility several kilometres away, sometimes in a different neighbourhood entirely. It's a temporary arrangement that can last 3 to 7 years, and it's something most buyers in new developments discover only after move-in.

This resale property is in an established neighbourhood served by a permanent, purpose-built school that opened in 2009. There are no outstanding boundary consultations, no planned portable additions, and no history of overflow to holding schools in this subdivision.

**Red flags buyers should ask about in new builds:**
- "What school will my child attend at time of occupancy?" (not at project completion)
- Is a new school funded in the capital budget, or only "proposed"?
- How many portables does the current feeder school operate?
- What is the school board's current enrolment vs. capacity for the catchment?

Purchasing a resale home in a mature neighbourhood with a built school eliminates this uncertainty entirely.

**Tagline:** A permanent school before you sign on the dotted line.''',
        'image_url': 'https://images.unsplash.com/photo-1497366216548-37526070297c?w=400&h=300&fit=crop',
        'category': 'school'
    },
]

# ============================================================
# BATCHING (derived from pool size, so it never goes out of sync)
# ============================================================

BATCH_SIZE = 6
TOTAL_BATCHES = max(1, math.ceil(len(SCENARIO_POOL) / BATCH_SIZE))

# Track current batch index (shared across all users)
current_batch_index = 0
_batch_lock = threading.Lock()

CATEGORY_ICONS = {
    'family': 'clock',
    'elderly': 'shield',
    'professional': 'building',
    'lifestyle': 'home',
    'religion': 'home',
    'safety': 'shield',
    'transport': 'clock',
    'transit': 'clock',
    'school': 'building',
    'home': 'home',
}


@scenario_bp.route('/pre-generated', methods=['GET'])
def get_pre_generated_scenarios():
    """Get 5 random pre-generated example scenarios"""
    try:
        if len(SCENARIO_POOL) < 5:
            return jsonify({
                'error': 'Not enough scenarios in pool',
                'available': len(SCENARIO_POOL)
            }), 400

        random_scenarios = random.sample(SCENARIO_POOL, 5)

        logger.info("[PRE-GENERATED] ✅ Returned 5 random scenarios")

        return jsonify({
            'success': True,
            'scenarios': random_scenarios,
            'total_available': len(SCENARIO_POOL)
        }), 200

    except Exception as e:
        logger.error(f"[SCENARIO ERROR] {str(e)}")
        return jsonify({
            'error': 'Failed to get scenarios',
            'details': str(e)
        }), 500


@scenario_bp.route('/random', methods=['GET'])
def get_random_scenarios():
    """
    Get the next batch of scenarios sequentially from the pool.
    Loops back to the start after the last batch.

    Usage: GET /api/scenario/random
    """
    global current_batch_index

    try:
        if not SCENARIO_POOL:
            return jsonify({'error': 'Scenario pool is empty'}), 400

        with _batch_lock:
            start_idx = current_batch_index * BATCH_SIZE
            end_idx = start_idx + BATCH_SIZE
            batch_scenarios = SCENARIO_POOL[start_idx:end_idx]

            current_serving = current_batch_index + 1
            current_batch_index = (current_batch_index + 1) % TOTAL_BATCHES

        logger.info(
            f"[SEQUENTIAL] ✅ Returned batch {current_serving}/{TOTAL_BATCHES} "
            f"(scenarios {start_idx + 1}-{min(end_idx, len(SCENARIO_POOL))})"
        )

        # Add icon field to each scenario if missing (work on copies)
        result = []
        for scenario in batch_scenarios:
            item = dict(scenario)
            if 'icon' not in item:
                item['icon'] = CATEGORY_ICONS.get(item.get('category', 'general'), 'building')
            result.append(item)

        return jsonify({
            'success': True,
            'scenarios': result,
            'batch_number': current_serving,
            'total_batches': TOTAL_BATCHES,
            'total_pool_size': len(SCENARIO_POOL)
        }), 200

    except Exception as e:
        logger.error(f"[SEQUENTIAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Failed to get sequential scenarios',
            'details': str(e)
        }), 500