"""
Scenario Simulator Module - Single File Version
Generates realistic real estate scenarios with AI-generated images and narratives
"""

from flask import Blueprint, request, jsonify
import os
import time
import logging
import requests
import base64
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

# ============================================================
# CREATE BLUEPRINT
# ============================================================

scenario_bp = Blueprint('scenario', __name__, url_prefix='/api/scenario')

# ============================================================
# ❌ REMOVED: Duplicate CORS handler (handled globally in app.py)
# ============================================================
# The @scenario_bp.after_request decorator has been removed
# because app.py already handles CORS globally

# ============================================================
# SERVICE FUNCTIONS
# ============================================================

def generate_scenario_image(scenario_text, story_title):
    """
    Return icon emoji as SVG image (can be displayed in <img> tag)
    Expected time: < 0.01 seconds (instant)
    """
    try:
        scenario_lower = scenario_text.lower()
        
        # Icon mapping based on keywords
        icon_map = {
            # Transportation
            'transport': '🚗',
            'car': '🚗',
            'bike': '🚴',
            'bicycle': '🚴',
            'airplane': '✈️',
            'flight': '✈️',
            'bus': '🚌',
            'train': '🚆',
            'metro': '🚇',
            
            # Food & Dining
            'restaurant': '🍽️',
            'food': '🍽️',
            'cafe': '☕',
            'coffee': '☕',
            'dining': '🍽️',
            'grocery': '🛒',
            'market': '🏪',
            
            # Fitness & Health
            'gym': '🏋️',
            'fitness': '💪',
            'workout': '🏋️',
            'yoga': '🧘',
            'hospital': '🏥',
            'health': '⚕️',
            'ill': '🏥',        # ← Added for "ill"
            'sick': '🏥',       # ← Added for "sick"
            'fever': '🏥',      # ← Added for "fever"
            'emergency': '🚑',  # ← Added for "emergency"
            
            # Education
            'school': '🏫',
            'education': '📚',
            'library': '📚',
            'university': '🎓',
            
            # Recreation
            'park': '🏞️',
            'playground': '🎠',
            'nature': '🌳',
            'lake': '🏞️',
            'beach': '🏖️',
            'cinema': '🎬',
            'theater': '🎭',
            
            # Shopping
            'shop': '🛍️',
            'mall': '🏬',
            'store': '🏪',
            
            # Residential
            'home': '🏠',
            'house': '🏡',
            'apartment': '🏢',
            'neighborhood': '🏘️',
            
            # Services
            'bank': '🏦',
            'police': '🚓',
            'fire': '🚒',
        }
        
        # Find matching icon
        selected_icon = '📍'  # Default icon
        for keyword, icon in icon_map.items():
            if keyword in scenario_lower:
                selected_icon = icon
                break
        
        # Convert emoji to SVG that can be used in <img> tag
        svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="200" height="200">
            <text x="50" y="50" font-size="60" text-anchor="middle" dominant-baseline="middle" font-family="Arial, sans-serif">
                {selected_icon}
            </text>
        </svg>'''
        
        # Convert SVG to base64
        svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        
        return {
            'success': True,
            'image_base64': svg_base64,  # ← Now returns base64 SVG
            'icon': selected_icon,
            'is_svg': True,
            'generation_time': '0.00s'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'icon': '📍'
        }


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
        
        # INTELLIGENT PROMPT - Detects scenario type automatically
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
- [Option 3: e.g., Cab/Uber - 2-min wait time, ₹80-120]
- [Option 4: e.g., Metro (only if in metro city) - Nearest station 800m]

[Closing paragraph: 2-3 complete sentences explaining why this location makes it easy]

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
- Taxi/Cab - Book via app, 3-4 minute arrival time, ₹120-180
- Ambulance - Community emergency hotline, 5-minute response time
- Neighbor's Vehicle - WhatsApp group emergency protocol active

The hospital is only 2.3 kilometers away via a 60-foot-wide arterial road with zero traffic at night. The 24/7 manned security ensures the gate opens immediately without fumbling for access cards. While families in congested areas waste 20+ minutes navigating narrow gullies, you're already in the ER getting treatment.

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
- Auto-rickshaw - Available at gate, ₹60-80 per trip

The school is just 3.5 kilometers away via a signal-free stretch of the outer ring road. No narrow lanes, no U-turns, no traffic chaos. While other parents leave home at 8 AM to fight congestion, you're finishing breakfast in peace.

TAGLINE: Convenience isn't a perk. It's a parenting essential.

---
## FOR NARRATIVE FORMAT (Lifestyle/Emotional scenarios):
---

TITLE: [Emotional/evocative title, 5-8 words]

SCENARIO:
[Paragraph 1: Set the scene with sensory details - 2-3 complete sentences]

[Paragraph 2: Show the contrast or problem - 2-3 complete sentences]

[Paragraph 3: How the property solves it - 3-4 complete sentences with specific features]

[Paragraph 4: Emotional impact - 2 complete sentences]

TAGLINE: [Memorable emotional statement]

**EXAMPLE:**
TITLE: Serenity Found

SCENARIO:
Imagine waking up to the sweet songs of birds and the gentle rustle of leaves. Your home is surrounded by lush green parks, a sight to behold from every window. The fresh air and soothing views create a sense of tranquility, setting the tone for a peaceful day.

As you step out, the crunch of gravel beneath your feet and the vibrant colors of blooming flowers greet you. The parks offer a serene escape from the city's hustle, where children play freely and families gather for evening walks.

Inside your home, the triple-glazed windows and 80-meter green buffer zone ensure that city noise never intrudes. Your children can study without distractions, and you can work from home without closing windows. This isn't just clever architecture—it's designed wellness for your entire family.

The true luxury isn't the imported fittings or marble lobbies. It's the ability to hear yourself think, to sleep deeply, and to wake up refreshed every single morning.

TAGLINE: Find your inner peace in perfect harmony with nature.

---

**CRITICAL RULES:**
- TOTAL LENGTH: 180-220 words (not counting title/tagline)
- **TIMELINE TIME ANCHORING**: If user mentions a specific time (e.g., "3 AM", "9 AM"), START the timeline at that EXACT time or slightly before (e.g., if user says "3 AM emergency", start timeline at 3:00 AM, NOT 12:00 AM)
- Timeline format: Each time step on NEW LINE with clear formatting
- Timeline intervals: Use realistic 2-5 minute gaps between steps
- Transport options: Each option on NEW LINE with dash (-)
- NEVER end mid-sentence - always complete every paragraph
- For narrative: Write in complete, flowing paragraphs
- Make every sentence complete and grammatically correct
- End with proper punctuation (. ! ?)
- If running out of space, end the previous sentence properly - DO NOT truncate

**OUTPUT FORMAT:**
TITLE: [Title here]

SCENARIO:
[Content with proper line breaks and formatting]

TAGLINE: [Tagline here]"""

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": """You are an expert real estate scenario writer. You create two types of content:

1. TIMELINE scenarios: Use clear line breaks for each time step. Format like:
   8:45 AM — Action here
   8:50 AM — Next action
   
   CRITICAL: If the user mentions a specific time (like "3 AM" or "9 AM"), your timeline MUST start at or near that time. DO NOT start from midnight (12:00 AM) or any other arbitrary time. Examples:
   - User says "3 AM emergency" → Start timeline at 3:00 AM
   - User says "9 AM school" → Start timeline around 8:35-8:45 AM
   - User says "midnight fever" → Start timeline at 12:00 AM
   
2. NARRATIVE scenarios: Write in complete, flowing paragraphs. NEVER end mid-sentence.

CRITICAL: Always finish every sentence completely. If you're running out of tokens, end the previous sentence with proper punctuation. Never truncate words or leave sentences incomplete."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
            max_tokens=600,
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

# At the bottom of your scenario_simulator.py, replace the routes section with this:

# ============================================================
# ROUTES - NO OPTIONS HANDLING (app.py handles it globally)
# ============================================================

@scenario_bp.route('/health', methods=['GET', 'POST'])
def health():
    """Health check for scenario simulator"""
    return jsonify({
        'status': 'healthy',
        'module': 'scenario_simulator',
        'version': '1.0.0',
        'groq_configured': bool(groq_client),
        'replicate_configured': bool(REPLICATE_API_TOKEN)
    }), 200


@scenario_bp.route('/generate', methods=['POST'])
def generate_scenario():
    """Generate a scenario with story and image"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        scenario_text = data.get('scenario_text', '').strip()
        client_name = data.get('client_name', 'skyline')
        
        if not scenario_text:
            return jsonify({'error': 'scenario_text is required'}), 400
        
        if len(scenario_text) < 10:
            return jsonify({'error': 'Scenario description too short (min 10 characters)'}), 400
        
        logger.info(f"[SCENARIO] Generating for: {scenario_text[:100]}...")
        
        # Step 1: Generate story using Groq
        logger.info("[SCENARIO] Step 1/2: Generating story with Groq...")
        story_result = generate_scenario_story(scenario_text)
        
        if not story_result.get('success'):
            return jsonify({
                'error': 'Failed to generate story',
                'details': story_result.get('error')
            }), 500
        
        # Step 2: Generate image using Replicate
        logger.info("[SCENARIO] Step 2/2: Generating image with Replicate...")
        image_result = generate_scenario_image(
            scenario_text=scenario_text,
            story_title=story_result['title']
        )
        
        if not image_result.get('success'):
            return jsonify({
                'error': 'Failed to generate image',
                'details': image_result.get('error')
            }), 500
        
        # Success response
        logger.info(f"[SCENARIO] ✅ Successfully generated scenario: {story_result['title']}")
        
        return jsonify({
            'success': True,
            'title': story_result['title'],
            'story': story_result['story'],
            'tagline': story_result['tagline'],
            'image_base64': image_result.get('image_base64'),
            'generation_time': {
                'story': story_result.get('generation_time'),
                'image': image_result.get('generation_time')
            }
        }), 200

    except Exception as e:
        logger.error(f"[SCENARIO ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


import random


    
    
SCENARIO_POOL = [
    # === FAMILY WITH CHILDREN (10 scenarios) ===
    {
        'id': 1,
        'title': 'School Run Without the Morning Rush',
        'description': '''Your daughter's school bell rings at 8:30 AM sharp, and attendance matters.

**Timeline:**
7:45 AM — Finish breakfast and pack school bag
7:55 AM — Walk down to parking, load backpack
8:00 AM — Start driving via the main road
8:12 AM — Drop at school gate, 18 minutes early

**Transport Options Available:**
- School Bus - Picks up from society gate at 7:40 AM
- Own Vehicle - Covered parking, 12-minute direct route
- Carpool - Rotate with 4 families, organized via app
- Auto-rickshaw - Always available at gate, ₹70-90

The school is just 3.8 kilometers away on a signal-free corridor. No narrow lanes, no U-turns, no honking chaos. While parents in congested areas leave at 7:15 AM to battle traffic, you're enjoying a relaxed breakfast together.

**Tagline:** Mornings should start with smiles, not stress.''',
        'image_url': 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 2,
        'title': 'Peaceful Nights for Growing Dreams',
        'description': '''Picture this: Your newborn finally drifts off after the evening feed. The silence is sacred, and you need it to last. Outside your window, there's no traffic roar, no late-night honking, no construction drilling that jolts tiny eyes awake at midnight.

The triple-glazed windows and 100-meter buffer from the main road create a cocoon of calm. Your neighbors are young families too, so there are no late-night parties or loud gatherings. The society's strict 10 PM noise policy isn't just a rule—it's a culture everyone respects.

Inside, the nursery overlooks a landscaped garden with soft solar lighting. The air is cleaner here, filtered by mature trees that line the compound. Your baby sleeps through the night, and so do you.

**Tagline:** Where little ones sleep soundly, and parents finally rest.''',
        'image_url': 'https://images.unsplash.com/photo-1476703993599-0035a21b17a9?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 3,
        'title': 'Room to Run, Space to Grow',
        'description': '''Three children mean three different schedules, three homework stations, and constant motion. Your current 2BHK feels like a puzzle with missing pieces. Toys spill into the living room, online classes overlap, and finding quiet study time is a daily negotiation.

This 4BHK changes everything. Each child gets their own dedicated room with study desks and storage. The fourth room transforms into a play zone where Lego kingdoms and art projects can stay undisturbed. The 2,400 sq ft layout includes a separate family lounge, so movie nights don't interfere with bedtime routines.

Outside, the society's children's play area features swings, slides, and a sand pit just 50 meters from your tower. The basketball court and cycling track keep older kids engaged. Saturday mornings become parent coffee meetups while kids play safely within view.

**Tagline:** Spacious living where every child finds their corner.''',
        'image_url': 'https://images.unsplash.com/photo-1511895426328-dc8714191300?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 4,
        'title': 'Daycare Drop-off in 8 Minutes Flat',
        'description': '''You're a single parent juggling work calls and daycare schedules. Every minute counts when you need to drop off your toddler and make it to the office on time.

**Timeline:**
8:15 AM — Finish getting ready, pack lunch bag
8:20 AM — Walk to parking, buckle up safely
8:23 AM — Drive via the residential road
8:28 AM — Drop at daycare entrance, wave goodbye

**Transport Options Available:**
- Own Vehicle - Basement parking, 8-minute direct drive
- Society Shuttle - Morning daycare run at 8:10 AM
- Walking - 12-minute pedestrian path through safe lanes
- Bicycle - Dedicated cycle track, 10 minutes

The daycare is 2.1 kilometers away through well-maintained residential roads with speed breakers. No highway crossings, no risky turns. The affordable rent means you're not stretching budgets, and the proximity saves both time and fuel costs every single day.

**Tagline:** Parenting solo is hard enough. Convenience helps.''',
        'image_url': 'https://images.unsplash.com/photo-1503454537195-1dcabb73ffb9?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 5,
        'title': 'Walking to School, Building Independence',
        'description': '''Your 9-year-old wants to walk to school with friends. It's a big step toward independence, but every parent's mind races with safety concerns: busy roads, blind turns, stray dogs, and the unpredictable traffic that makes pedestrian crossings feel like obstacle courses.

This neighborhood was designed with walking in mind. The primary school is exactly 650 meters away via a dedicated pedestrian pathway lined with streetlights. There are no vehicle crossings, no open drains, and a security patrol that monitors the route during school hours. Zebra crossings have speed bumps and clear signage.

Other families do this daily. You'll see groups of children walking together, building friendships and confidence with every step. The route passes through well-maintained parks, and the society's CCTV coverage extends to the pathway entrance. You can track their progress on the community safety app.

**Tagline:** Safe streets where children walk free and parents breathe easy.''',
        'image_url': 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 6,
        'title': 'Summer Splashes Every Weekend',
        'description': '''Summer weekends used to mean packing bags, driving across town, and spending hours at crowded public pools where finding a spot felt like a competition. Your kids love swimming, but the logistics wore everyone out.

Now the pool is just an elevator ride away. The society's dedicated children's pool has a shallow wading area for toddlers and a training section for older kids. It's chlorinated daily, cleaned every morning, and has certified lifeguards on duty during all operating hours. Weekend swimming classes are organized by resident coaches.

Saturday mornings become ritual: breakfast, swimsuits, and down to the pool by 10 AM. Your children learn strokes, build water confidence, and make friends with neighbors their age. Parents lounge under shaded cabanas with coffee, and nobody drives anywhere. The evening adult swim session means fitness time for you too.

**Tagline:** Dive into joy without leaving home.''',
        'image_url': 'https://images.unsplash.com/photo-1530103043960-ef38714abb15?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 7,
        'title': 'Focus Zones for Future Scholars',
        'description': '''Two teenagers preparing for board exams in a cramped apartment is a masterclass in chaos management. One needs absolute silence for math problems while the other listens to history lectures aloud. Dining tables become makeshift desks, and every room echoes with competing study routines.

This 3BHK reimagines learning spaces. The master bedroom becomes the parents' zone. Each teenager gets their own room with a built-in study desk, floating shelves for books, and soundproof doors that close properly. The third room converts into a dedicated study library with a large desk, natural lighting, and a whiteboard wall.

The apartment's design includes acoustic insulation between bedrooms. No more arguments about noise levels or whose turn it is to use the quiet space. The high-speed internet has dual routers ensuring bandwidth for simultaneous online classes. Large windows bring in natural light that reduces eye strain during long study hours.

**Tagline:** Smart spaces where brilliant minds can truly focus.''',
        'image_url': 'https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 8,
        'title': 'No Stairs, No Worries',
        'description': '''Your toddler is at that fearless age where everything is a climbing challenge. Stairs become adventures, and elevators are risky with little fingers exploring buttons. High-floor living means constant vigilance, carrying strollers up and down, and anxiety every time the elevator is crowded during peak hours.

A ground floor apartment changes the equation entirely. Direct access to the garden means your child can toddle outside safely without navigating stairs or waiting for lifts. The attached patio becomes an extension of your living room where they can play while you cook, always visible through the kitchen window.

Loading groceries becomes effortless. The parking spot is right outside your door. Elderly grandparents can visit without mobility concerns. During power cuts or elevator maintenance, you're unaffected. The emergency exit is literally your front door. And when your little one trips or needs a bathroom break during outdoor play, home is always 30 seconds away.

**Tagline:** Ground floor living where safety meets sanity.''',
        'image_url': 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 9,
        'title': 'International Education at Your Doorstep',
        'description': '''Both of you leave for work by 8:30 AM. Your daughter's school starts at 8:45 AM. The international curriculum school you researched is excellent, but it's across town—meaning either a 90-minute school bus ride or one of you constantly adjusting work schedules for drop-offs.

This location solves the impossible puzzle. The Cambridge-affiliated international school is 2.7 kilometers away via a four-lane road with minimal traffic during morning hours. The 15-minute drive means your daughter gets extra sleep, you're never late for client calls, and family breakfast together becomes the norm, not a luxury.

The school bus service from this society runs a dedicated route with just three stops. Your child boards at 8:20 AM and reaches school by 8:40 AM. When one of you has early meetings, the other handles drop-off without derailing anyone's day. School event participation becomes feasible because you're not losing two hours to travel.

**Tagline:** World-class education without the daily marathon.''',
        'image_url': 'https://images.unsplash.com/photo-1509062522246-3755977927d7?w=400&h=300&fit=crop',
        'category': 'family'
    },
    {
        'id': 10,
        'title': 'Childhood Reimagined in Green Spaces',
        'description': '''Screen time battles. Indoor restlessness. Asking "Can we go to the park?" and hearing yourself say "Later, beta" because the nearest decent park is a 20-minute drive through congested traffic. Your children's childhood is slipping into pixels and closed rooms.

This community was designed around 12,000 square feet of central green space. The children's park has age-appropriate play equipment certified for safety, soft rubber flooring, and shaded seating for parents. Swings, slides, monkey bars, and a miniature rock climbing wall give kids varied physical activity.

Every evening becomes outdoor time. Children from the complex gather here, building friendships through spontaneous cricket matches and treasure hunts. Parents form support networks over evening chai. The park is gated within the society, so kids can play freely while you're always within shouting distance. Weekend mornings mean frisbee throws and picnic mats under trees.

**Tagline:** Where children grow wild, free, and happy.''',
        'image_url': 'https://images.unsplash.com/photo-1516627145497-ae6968895b74?w=400&h=300&fit=crop',
        'category': 'family'
    },
    
    # === ELDERLY & MULTI-GENERATIONAL (6 scenarios) ===
    {
        'id': 11,
        'title': 'Dignity Meets Design in Every Detail',
        'description': '''Your parents are moving in, and suddenly every staircase feels like an obstacle course. High-rise apartments mean elevator dependency. One power cut, one maintenance day, and mobility becomes a crisis. Your father's knee surgery last year makes stairs impossible, and your mother worries about being trapped on the 12th floor during emergencies.

A ground floor villa eliminates every barrier. Direct entry from the parking means no steps between car and living room. Wide doorways accommodate walkers or wheelchairs if ever needed. The bathroom has grab bars pre-installed and anti-slip tiles. The bedroom has natural ventilation, so they're never dependent on air conditioning during power outages.

The attached garden becomes morning ritual space. Your father does his physiotherapy exercises on the lawn. Your mother's evening walks happen safely within the compound. Guests can visit without your parents worrying about escort duties in elevators. Emergency exits are instant. Medical equipment deliveries happen at the door.

**Tagline:** Independence preserved with thoughtful design.''',
        'image_url': 'https://images.unsplash.com/photo-1581579438747-1dc8d17bbce4?w=400&h=300&fit=crop',
        'category': 'elderly'
    },
    {
        'id': 12,
        'title': 'Retirement Haven in Quiet Corners',
        'description': '''After 35 years of morning alarms and office deadlines, retirement should feel like exhaling. But your current apartment overlooks a busy intersection. Traffic noise starts at 6 AM. The balcony collects dust and exhaust fumes. The garden you always dreamed of maintaining remains a Pinterest dream.

This 2BHK on the second floor overlooks a landscaped garden spanning 8,000 square feet. Floor-to-ceiling windows frame mature trees and flowering shrubs. The balcony is deep enough for a rocking chair, a small table, and potted plants that actually thrive. Mornings begin with bird songs, not honking.

The society's senior citizens club meets twice weekly for yoga, book discussions, and light exercise sessions. The garden has meandering walking paths with benches every 50 meters. You can garden in the designated allotment beds growing tomatoes and herbs. Evenings mean chai on the balcony watching sunsets paint the sky.

**Tagline:** Where golden years truly shimmer with peace.''',
        'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400&h=300&fit=crop',
        'category': 'elderly'
    },
    {
        'id': 13,
        'title': 'Healthcare When Minutes Matter Most',
        'description': '''Your mother had a cardiac event last year. The cardiologist said response time is everything. But the nearest multispecialty hospital is 45 minutes away through unpredictable traffic. Every chest pain becomes a decision tree of worry: Is this serious? Should we wait? Can we make it in time?

This apartment is 1.8 kilometers from City Central Hospital with a 24/7 emergency department, cardiac care unit, and specialist doctors on call. The route is a straight road with zero traffic lights and minimal congestion even during peak hours.

**Timeline:**
2:15 AM — Chest discomfort wakes your mother up
2:17 AM — You help her sit up, grab medications
2:20 AM — Exit building, security opens gate immediately  
2:24 AM — Arrive at emergency entrance, doctors assess

The hospital has her complete medical history on file. Your family has met the cardiologist during routine checkups. Ambulance services know this route. While other families gamble with golden hour windows, you have certainty built into your address.

**Tagline:** Peace of mind measured in minutes, not miles.''',
        'image_url': 'https://images.unsplash.com/photo-1538108149393-fbbd81895907?w=400&h=300&fit=crop',
        'category': 'elderly'
    },
    {
        'id': 14,
        'title': 'Freedom Engineered Into Every Floor',
        'description': '''Your father uses a walker after his hip replacement. Buildings without elevators are impossible. But even buildings with lifts become problematic when elevators are under repair, or when they're too narrow, or when lift lobbies have steps. Mobility shouldn't mean isolation, yet that's what most buildings offer.

This apartment complex was built with universal design principles. The elevator is spacious enough for wheelchairs, with buttons at reachable heights and audio announcements at every floor. The lobby has a ramp entrance with handrails on both sides. Corridors are wide enough for two wheelchairs to pass comfortably.

Inside the apartment, doorways are 38 inches wide—the standard for wheelchair access. The bathroom has a walk-in shower with a foldable seat, grab bars near the toilet, and slip-resistant tiles throughout. The kitchen counters have variable heights. Light switches are positioned lower than standard. Even the parking spot is wider, close to the elevator, and marked clearly.

**Tagline:** Where mobility challenges meet invisible solutions.''',
        'image_url': 'https://images.unsplash.com/photo-1541883125728-68f4e11a3e8d?w=400&h=300&fit=crop',
        'category': 'elderly'
    },
    {
        'id': 15,
        'title': 'Golden Years Among Friends Who Understand',
        'description': '''Retirement communities abroad have senior clubs, book groups, and organized activities. Indian apartments? You're lucky if you find one neighbor your age. Your parents moved into their current flat five years ago and still barely know anyone. Loneliness isn't just emotional—it's a health risk for seniors.

This society's senior citizen club isn't a token amenity—it's a thriving community of 40+ members aged 60 and above. Tuesday mornings are yoga and meditation sessions led by a certified instructor. Thursday evenings feature book club discussions and documentary screenings. The club has organized day trips to nearby temples and heritage sites.

The dedicated club room has comfortable seating, a library with large-print books, and indoor games like chess and carrom. Members share WhatsApp groups for health tips and emergency contacts. During festivals, the club organizes low-impact celebrations. Coffee mornings become friendship circles. Your parents won't just live here—they'll belong here.

**Tagline:** Age gracefully surrounded by peers who get it.''',
        'image_url': 'https://images.unsplash.com/photo-1573497161161-c3e73707e25c?w=400&h=300&fit=crop',
        'category': 'elderly'
    },
    {
        'id': 16,
        'title': 'Three Generations Under One Expansive Roof',
        'description': '''Your traditional joint family setup is non-negotiable. Grandparents, you and your spouse, your children, and even your unmarried younger brother—seven people with different schedules, needs, and personal space requirements. Current 3BHKs feel like they're bursting at the seams.

This 5BHK villa spans 3,200 square feet across two levels. Grandparents occupy the ground floor master suite with attached bathroom and private sit-out area. The first floor has three bedrooms for your family and your brother. The fifth room is a multi-purpose space: prayer room in the morning, study area during afternoon, entertainment zone in evening.

Separate living and dining areas mean multiple activities can happen simultaneously without conflict. Your children do homework in the family lounge while grandparents watch TV in their private living space. The kitchen is large enough for your mother and wife to cook together comfortably. Outdoor space includes a front yard for tulsi plant and family gatherings.

**Tagline:** Togetherness without tripping over each other.''',
        'image_url': 'https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=400&h=300&fit=crop',
        'category': 'elderly'
    },
    
    # === PROFESSIONAL & WORK (8 scenarios) ===
    {
        'id': 17,
        'title': 'Metro Minutes from Work and Life',
        'description': '''Your first corporate job pays decently, but Delhi NCR traffic eats three hours daily. Cab costs drain your salary. Living far from the metro means adding auto-rickshaw uncertainty to your commute equation. You've been late to work twice this month because of traffic unpredictability.

This studio apartment is 280 meters from the metro station—a 4-minute walk even during monsoon. Exit your building, turn right, cross the pedestrian bridge, and you're on the platform. Your office is six metro stops away, 32 minutes door-to-door including the walk. Predictable, affordable, air-conditioned.

**Timeline:**
8:40 AM — Grab breakfast and laptop bag
8:45 AM — Exit building, walk to metro entry
8:49 AM — Board metro train heading to office
9:21 AM — Reach office station, walk to building

The studio's 450 square feet is efficiently designed with a murphy bed, compact kitchen, and workspace near the window. No landlord drama, no brokerage renewal hassles. Your monthly savings increase. Evening gym time becomes possible. Work-life balance starts with location logic.

**Tagline:** Commute less, live more, grow faster.''',
        'image_url': 'https://images.unsplash.com/photo-1545324418-cc1a3fa10c00?w=400&h=300&fit=crop',
        'category': 'professional'
    },
    {
        'id': 18,
        'title': 'Your Office Is Now Your Sanctuary',
        'description': '''Remote work sounded like freedom until your bedroom became your office. Client calls happen with your bed visible in the background. The dining table is perpetually covered with laptops and chargers. Your back hurts from working hunched on the sofa. Professional and personal spaces have blurred into exhausting overlap.

This 2BHK redefines work-from-home. The second bedroom converts into a proper home office with a dedicated entrance. Built-in desk runs along the window providing natural light and garden views. Floating shelves organize files. The door closes, creating physical and mental separation between work and home.

The internet infrastructure is future-ready with dual fiber connections and power backup that extends to the home office. Acoustic insulation in walls means your spouse's calls don't interfere with yours. The window opens to tree-lined silence, not traffic chaos. Video call backgrounds look professional without artificial backdrops. After work, you close the office door and leave.

**Tagline:** Work from home without living at work.''',
        'image_url': 'https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=400&h=300&fit=crop',
        'category': 'professional'
    },
    {
        'id': 19,
        'title': 'Tech Career Without Traffic Tax',
        'description': '''Your IT job is in the Outer Ring Road corridor. The salary is excellent. The catch? You live 18 kilometers away, which translates to 90 minutes in morning traffic on good days, two hours when it rains. You wake at 6:30 AM to reach by 9:30 AM. You're exhausted before work even begins.

This apartment is 7.3 kilometers from your office campus via the elevated expressway. Morning commute is 22 minutes. Evening return takes 28 minutes even during peak hours. You reclaim two hours daily—that's 40 hours monthly or 480 hours yearly. That's 20 entire days of your life returned.

**Transport Options Available:**
- Own Vehicle - Dedicated covered parking, smooth expressway route
- Office Cab - Pickup point 100 meters from your gate
- Metro - Upcoming station (Phase 3) will be walkable
- Carpool - Four colleagues live in this society

You wake at 8:00 AM now. Morning workout becomes feasible. Evening energy remains for learning new tech stacks. Your productivity increases because you're not arriving drained. The apartment's higher rent pays for itself in saved fuel, reduced vehicle wear, and preserved sanity.

**Tagline:** Closer to work, closer to life's actual work.''',
        'image_url': 'https://images.unsplash.com/photo-1497215728101-856f4ea42174?w=400&h=300&fit=crop',
        'category': 'professional'
    },
    {
        'id': 20,
        'title': 'Business Hub Built Into Your Address',
        'description': '''Your consulting business operates from home, but zoning laws prohibit commercial activity in residential complexes. Client meetings in your living room feel unprofessional. Renting separate office space doubles your overhead. Coworking memberships eat profits. You need flexibility without legal tangles.

This mixed-use space is officially zoned for both residential and commercial activity. The ground floor includes a separate entrance designed for client access without going through residential areas. The 900 square foot space divides naturally: front area configured as professional office with reception desk and meeting zone, back area as comfortable living quarters.

Signage is permitted. Business registration uses this address without landlord objections. GST-registered office location matches your residence. Clients arrive, park in designated visitor spots, and enter a proper office environment. After work hours, you simply close the partition door and the space transforms back to home. Electricty meters are split for accounting clarity.

**Tagline:** Build your empire from a foundation of flexibility.''',
        'image_url': 'https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=400&h=300&fit=crop',
        'category': 'professional'
    },
    {
        'id': 21,
        'title': 'Silence as a Creative Currency',
        'description': '''You're a writer, designer, or content creator. Your currency is focus, and focus demands silence. But your current apartment overlooks a construction site. Drilling starts at 8 AM. Honking persists until midnight. You've tried noise-canceling headphones, but creative work needs natural awareness, not artificial isolation.

This apartment sits in a residential cul-de-sac 150 meters from the main road. The approach road has speed breakers every 50 meters, naturally calming traffic. No commercial establishments mean no delivery trucks, no constant footfall, no blaring music. The building houses mostly young professionals and retired couples who value quiet.

The third-floor corner unit has windows on three sides opening to tree canopy, not buildings. You hear rustling leaves, occasional bird calls, and distant life—not jarring noise. The acoustic design includes concrete walls between units and insulated false ceilings. Your creative hours are yours again, undisturbed and generative.

**Tagline:** Where silence isn't luxury, it's infrastructure.''',
        'image_url': 'https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=400&h=300&fit=crop',
        'category': 'professional'
    },
    {
        'id': 22,
        'title': 'Status Delivered Through Strategic Location',
        'description': '''You've reached senior management. Clients visit occasionally. Your address reflects professional standing. Living in a mediocre locality sends wrong signals. Your current apartment is spacious, but the neighborhood lacks prestige. Relocating isn't about vanity—it's about perception that impacts business relationships.

This luxury 3BHK sits in the city's prime business district. The building's glass facade is an architectural landmark. Your floor has only two apartments ensuring exclusivity. Imported marble lobbies, concierge services, and valet parking signal success. The address on your business card opens conversations at networking events.

Floor-to-ceiling windows frame city skyline views. Modular Italian kitchen with wine cooler. Home automation controls lighting, temperature, and security via smartphone. The society hosts CEO families, diplomats, and senior corporate leaders. Your professional network expands through elevator conversations. Client meetings in the society's business lounge look impressive without booking external venues.

**Tagline:** An address that speaks before you do.''',
        'image_url': 'https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=400&h=300&fit=crop',
        'category': 'professional'
    },
    {
        'id': 23,
        'title': 'Sleep Soundly While the City Wakes',
        'description': '''You work night shifts at the hospital—7 PM to 7 AM. You return home exhausted when the world is starting its day. But sleep? Impossible. Construction drilling starts at 8 AM. School buses honk. Delivery trucks beep while reversing. Daytime sleep isn't just difficult—it's a medical necessity you're being denied.

This apartment in a residential tower has strategic design for your reality. The bedroom faces the inner courtyard, not the road. Triple-glazed windows with blackout curtains block 90% of external noise and 100% of light. The building has strict daytime noise regulations that residents actually follow because many are doctors, pilots, and IT professionals with similar schedules.

The neighborhood is naturally quiet—no nearby schools generating morning rush, no commercial markets creating vendor chaos. The society's maintenance work is scheduled between 3-5 PM only. Your phone stays on DND. The bedroom's ventilation is mechanical, so windows stay closed. You finally get the 7-8 hours your body desperately needs.

**Tagline:** Night warriors deserve daytime peace.''',
        'image_url': 'https://images.unsplash.com/photo-1505751172876-fa1923c5c528?w=400&h=300&fit=crop',
        'category': 'professional'
    },
    {
        'id': 24,
        'title': 'Central Point for Divided Directions',
        'description': '''You work in Cyber City. Your spouse works in Connaught Place. Opposite directions, 40 kilometers apart. Every housing decision becomes a negotiation of whose commute matters more. Current setup means one of you travels 90 minutes while the other manages 30. Resentment builds in traffic jams.

This apartment in Dwarka Sector 21 is geometrically equitable. You take the metro—three stops to Cyber City, 35 minutes total. Your spouse drives via the Ring Road—22 kilometers to CP, 40 minutes in morning traffic. Both commutes are manageable, neither feels sacrificed for the other's convenience.

**Transport Options Available:**
- Metro - Dwarka Sector 21 station is 400m walk
- Own Vehicle - Covered parking, easy Ring Road access
- Office Cabs - Multiple IT companies provide pick-up
- Carpooling - Active groups for both directions

Evenings mean you both return around 7:30 PM. Energy remains for cooking together, gym time, or simply talking without exhaustion. Weekends aren't spent recovering from commute fatigue. The apartment becomes a home, not just a resting point between battles with distance.

**Tagline:** Marriage is partnership, location should be too.''',
        'image_url': 'https://images.unsplash.com/photo-1560264280-88b68371db39?w=400&h=300&fit=crop',
        'category': 'professional'
    },
    
    # === LIFESTYLE & WELLNESS (7 scenarios) ===
{
    'id': 25,
    'title': 'Fitness Built Into Your Daily Address',
    'description': '''You've paid for gym memberships that go unused because driving 4 kilometers after work drains motivation. Morning runs require walking to find safe routes through traffic. Fitness goals repeatedly fail not from lack of discipline but from friction between intention and infrastructure.

This society was designed around active lifestyles. The gym on the ground floor has cardio machines, free weights, and functional training equipment. It opens at 5:30 AM for early birds. Evening batch runs from 6-9 PM. No commute, no excuses—just elevator down and you're working out.

The 800-meter jogging track circles the complex with rubber pavement that's joint-friendly. Distance markers every 100 meters help track progress. Outdoor gym equipment provides bodyweight training options. The yoga deck hosts sunrise sessions on weekends. Badminton and tennis courts book via app.

Your fitness routine becomes default, not heroic effort. Morning jog before coffee. Evening weights after work. Weekend tennis matches with neighbors. Health isn't a goal anymore—it's just how you live here.

**Tagline:** Where wellness is woven into daily life.''',
    'image_url': 'https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=400&h=300&fit=crop',
    'category': 'lifestyle'
},
{
    'id': 26,
    'title': 'Breathing Space in Concrete Jungles',
    'description': '''You moved to the city for career opportunities, but every year you feel more disconnected from nature. Your current apartment overlooks other buildings. The nearest park is 3 kilometers away. Weekends mean escaping the city just to see trees. You're tired of choosing between professional growth and environmental sanity.

This apartment complex sits on 5 acres where 60% is designated green space. Over 200 mature trees were preserved during construction—you're not moving into a new development waiting for saplings to grow. Floor-to-ceiling windows in your apartment frame canopy views. Bird calls replace alarm clocks.

The landscaping includes native species that attract butterflies and birds. Walking paths meander through gardens with seating alcoves under trees. A small water feature creates soothing sounds. The children's play area blends into natural terrain rather than sitting on concrete. Evenings mean balcony time watching sunsets filter through leaves.

The building design maximizes cross-ventilation, reducing AC dependency. Rainwater harvesting and organic waste composting happen behind the scenes. You're not compromising urban convenience—you're accessing it through a green filter.

**Tagline:** City living that remembers you're still human.''',
    'image_url': 'https://images.unsplash.com/photo-1441974231531-c6227db76b6e?w=400&h=300&fit=crop',
    'category': 'lifestyle'
},
{
    'id': 27,
    'title': 'Wagging Tails Welcome Here',
    'description': '''Your Labrador is family, but finding housing that agrees is exhausting. Landlords say no pets. Societies have breed restrictions. The nearest park for walks is across a busy highway. Your dog's quality of life suffers, and so does yours from the constant guilt and logistical stress.

This pet-friendly community doesn't just tolerate animals—it celebrates them. The society has a dedicated dog park with agility equipment, waste stations, and separate zones for small and large breeds. The park is 150 meters from your building. Morning and evening dog-walker groups form naturally among residents.

Building rules explicitly permit pets with simple registration. Elevators have designated pet-friendly timings. The ground floor has a pet washing station. Veterinary clinics and pet stores are within 2 kilometers. The nearby public park has a 1.5-kilometer walking trail perfect for longer walks without crossing roads.

Your dog makes friends. You make friends through your dog. Weekend meetups happen organically. Your pet isn't a complication anymore—they're your entry ticket into a community that gets it.

**Tagline:** Where four-legged family members belong too.''',
    'image_url': 'https://images.unsplash.com/photo-1450778869180-41d0601e046e?w=400&h=300&fit=crop',
    'category': 'lifestyle'
},
{
    'id': 28,
    'title': 'Sanctuary for the Soul Seeker',
    'description': '''Your meditation practice requires silence, but your current apartment sits above a restaurant. Kitchen exhaust fans run until midnight. Weekend mornings bring delivery trucks. You've tried early morning sessions, but construction noise starts at 7 AM. Inner peace feels like a luxury you can't afford at this address.

This apartment is positioned in the society's quietest corner, away from the main gate and parking areas. The building houses mindfulness-oriented residents—yoga teachers, therapists, and wellness professionals who chose this location for the same reasons you seek it. Shared values create shared respect for silence.

The bedroom faces east, welcoming sunrise for morning sadhana. The balcony is deep enough for a meditation cushion and small altar. Acoustic insulation in walls and double-glazed windows buffer external sounds. The society's yoga pavilion hosts group meditation sessions twice weekly and is available for personal practice during off-hours.

Nearby is a 2-kilometer tree-lined walking path around a lake. The neighborhood has two wellness centers offering sound healing and pranayama classes. Your practice deepens not through willpower but through environmental support. Peace isn't something you create despite your surroundings—it's what your surroundings naturally offer.

**Tagline:** Where stillness isn't stolen, it's given.''',
    'image_url': 'https://images.unsplash.com/photo-1544367567-0f2fcb009e0b?w=400&h=300&fit=crop',
    'category': 'lifestyle'
},
{
    'id': 29,
    'title': 'Community That Feels Like Family',
    'description': '''You thrive on social connection, but your current apartment feels isolated. Neighbors are strangers. Weekend evenings mean scrolling phones alone. You've tried joining clubs across town, but distance kills consistency. You're lonely in a city of millions, and it's affecting your mental health.

This society's clubhouse isn't just infrastructure—it's the beating heart of community life. Weekly events calendars include book clubs, board game nights, cooking competitions, and festival celebrations. The residents' WhatsApp group actively coordinates potlucks, movie screenings, and group outings to concerts and exhibitions.

The clubhouse has a multipurpose hall that hosts Saturday night Bollywood dance classes, Sunday morning acoustic music sessions, and midweek trivia nights. There's a café corner that becomes informal gathering space. The pool deck hosts summer evening socials. Birthday party bookings happen year-round.

You'll know your neighbors' names within weeks, not years. Friday evenings mean clubhouse dinner with eight friends you've made organically. Your social calendar fills with building events, not forced networking. Connection happens naturally because the architecture and culture enable it.

**Tagline:** Where neighbors become the family you choose.''',
    'image_url': 'https://images.unsplash.com/photo-1511632765486-a01980e01a18?w=400&h=300&fit=crop',
    'category': 'lifestyle'
},
{
    'id': 30,
    'title': 'Literary Life at Your Doorstep',
    'description': '''You're a voracious reader, but your current apartment is kilometers from any decent library. Online books miss the tactile joy of physical pages. Buying books is expensive and storage-intensive. Reading groups you'd love to join meet too far away for weeknight commitment.

The public library is 850 meters from your building—a 12-minute walk through a tree-lined residential street. The library has over 50,000 titles, coworking spaces for writers, and hosts author talks twice monthly. Your library card also gives access to online databases and audiobooks. Weekend afternoons mean browsing stacks and discovering unexpected gems.

Your apartment's second bedroom converts into a personal library with floor-to-ceiling shelving. Large windows provide natural reading light. The reading nook has a comfortable chair and adjustable lamp. The neighborhood is quiet enough that you can read with windows open, accompanied by bird songs and rustling leaves.

The library's book club meets Thursday evenings. You've joined two reading groups—one for contemporary fiction, another for non-fiction. Coffee shops within walking distance become post-library discussion venues. Your intellectual life flourishes not through online algorithms but through human curation and conversation.

**Tagline:** Where pages turn and minds expand naturally.''',
    'image_url': 'https://images.unsplash.com/photo-1507842217343-583bb7270b66?w=400&h=300&fit=crop',
    'category': 'lifestyle'
},
{
    'id': 31,
    'title': 'Culinary Adventures on Every Corner',
    'description': '''You love exploring cuisines, trying new restaurants, and discovering hidden café gems. But your current location offers two options: home delivery with soggy food or driving 8 kilometers to restaurant districts. Weekend dinner plans become logistical projects involving parking and traffic calculations.

This apartment sits in a vibrant neighborhood with 30+ restaurants within 1-kilometer radius. South Indian breakfast joints, North Indian dhabas, Chinese eateries, Italian bistros, Mexican cafés, and experimental fusion restaurants line the streets. New places open quarterly. Food delivery takes 15 minutes, but walking is more enjoyable.

Friday evenings mean spontaneous dinner dates—just walk out and choose based on mood. Weekend brunches become neighborhood explorations. That new café everyone's talking about? It's 400 meters away. The bakery with legendary croissants? Morning walk distance. The rooftop bar with city views? You can walk back safely at night.

Your kitchen stays stocked for serious cooking when inspiration strikes, but dining out isn't a production—it's just stepping outside. Food blogger meetups happen locally. Cooking classes run at the community center. Your relationship with food shifts from convenience-driven to curiosity-driven.

**Tagline:** Where every meal is an adventure, not an expedition.''',
    'image_url': 'https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop',
    'category': 'lifestyle'
},

# === RELIGIOUS & CULTURAL (3 scenarios) ===
{
    'id': 32,
    'title': 'Daily Devotion Without Disruption',
    'description': '''Your morning and evening prayers at the temple are non-negotiable spiritual anchors. But the temple is 6 kilometers away through congested traffic. Morning darshan means waking at 5 AM to travel and return before work. Evening prayers conflict with dinner and family time. Your devotion creates daily logistical stress.

The ancient Shiva temple is 700 meters from your building—an 8-minute walk via a pedestrian-friendly route with streetlights. Morning aarti at 6 AM is accessible with a 5:45 AM departure. Evening prayer at 7 PM means leaving home at 6:52 PM and returning by 7:30 PM for family dinner.

**Timeline:**
5:45 AM — Leave apartment in traditional attire
5:53 AM — Arrive at temple for morning aarti
6:15 AM — Complete prayers and prasad
6:25 AM — Return home, ready for office by 8 AM

The temple community recognizes regular devotees. Festival celebrations become neighborhood events. The walking route passes through quiet residential areas where morning walkers nod respectfully. Your spiritual practice deepens because accessibility removes friction. Prayer becomes meditation, not obligation shadowed by clock-watching.

**Tagline:** Faith flourishes when devotion meets convenience.''',
    'image_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop',
    'category': 'religion'
},
{
    'id': 33,
    'title': 'Prayer Call Within Walking Distance',
    'description': '''Five daily prayers define your spiritual rhythm, but the nearest mosque is 4 kilometers away. Fajr prayer at dawn requires driving through dark streets. Jummah prayers on Fridays mean leaving work early and battling traffic. Your teenage son wants to attend mosque regularly but can't drive yet.

The neighborhood mosque is 600 meters away via a safe, well-lit pathway. Fajr prayer is a 7-minute walk, returning home in time for family breakfast. Maghrib and Isha prayers fit naturally into evening routines. Your son walks independently to Zuhr and Asr prayers after school, building responsibility and religious connection.

**Transport Options Available:**
- Walking - Dedicated pedestrian path, 7-9 minutes
- Bicycle - Covered parking available at mosque
- Auto-rickshaw - Available but unnecessary for this distance
- Society shuttle - Runs for elderly residents on Fridays

Friday Jummah becomes community gathering without work disruption. The mosque runs Quran classes for children after school. During Ramadan, Taraweeh prayers are accessible without family separation. Islamic bookshops and halal restaurants nearby strengthen cultural connection. Your faith practice becomes integrated into daily life, not scheduled around transportation logistics.

**Tagline:** Where the call to prayer is answered with footsteps, not car keys.''',
    'image_url': 'https://images.unsplash.com/photo-1564769625905-50e93615e769?w=400&h=300&fit=crop',
    'category': 'religion'
},
{
    'id': 34,
    'title': 'Sunday Service Without the Rush',
    'description': '''Sunday morning service at 9 AM is family tradition, but the church is across town. You leave at 8 AM to find parking, arrive rushed, and miss the opening hymns. Post-service fellowship is brief because you're worried about lunch timing and traffic back home.

St. Mary's Church is 1.2 kilometers away—a 15-minute walk or 5-minute drive with guaranteed parking in the church compound. Sunday mornings transform from stressful sprints to peaceful rituals. You wake at 7:30 AM, enjoy family breakfast, dress leisurely, and still arrive 10 minutes early.

**Timeline:**
8:15 AM — Finish breakfast and get dressed
8:35 AM — Walk together as family to church
8:50 AM — Arrive, greet community, find seats
10:30 AM — Service ends, fellowship in courtyard
11:15 AM — Walk home, lunch prep without rush

The church community becomes your extended family. Your children attend Sunday school while you're in service. Midweek Bible study groups are accessible for evening attendance. Christmas and Easter celebrations don't require advance travel planning. The priest recognizes your family. Church volunteer opportunities fit into weekly schedules.

**Tagline:** Worship in peace, fellowship without watching the clock.''',
    'image_url': 'https://images.unsplash.com/photo-1438232992991-995b7058bbb3?w=400&h=300&fit=crop',
    'category': 'religion'
},

# === SAFETY & SECURITY (3 scenarios) ===
{
    'id': 35,
    'title': 'Safe Haven for Independent Living',
    'description': '''You're a young professional woman living alone. Every apartment viewing includes mental checklists: Can I walk from parking to my floor alone at night? Are there security cameras? Will the guard actually respond if something happens? Your independence shouldn't require constant hypervigilance.

This gated community has 24/7 manned security with three guards on each shift. Facial recognition entry for residents and mandatory registration for all visitors with photo ID verification. CCTV cameras cover every entry point, parking area, elevator lobby, and corridor with 30-day footage retention.

The apartment complex has 40% female residents living independently—it's not an exception, it's the norm. A women's safety WhatsApp group shares real-time updates. Escort services available from gate to apartment after 10 PM. Well-lit pathways eliminate dark corners. Panic buttons installed in elevators. The society conducts quarterly self-defense workshops.

You return from late work shifts without anxiety. Grocery shopping at 8 PM feels normal. Morning runs at 6 AM happen safely within the complex. Your parents visit without worry. Independence isn't compromised by gender—it's supported by infrastructure designed with awareness.

**Tagline:** Where safety is infrastructure, not afterthought.''',
    'image_url': 'https://images.unsplash.com/photo-1527482797697-8795b05a13fe?w=400&h=300&fit=crop',
    'category': 'safety'
},
{
    'id': 36,
    'title': 'Watchful Eyes for Peace of Mind',
    'description': '''Your children play in the park while you're visible from the balcony, but gaps in fencing make you nervous. Delivery personnel enter freely without verification. Neighborhood kids you don't recognize play alongside yours. Parenting in open layouts means constant low-level anxiety about who's watching when you're not.

This gated community operates like a secure campus. Single entry-exit point with boom barrier and security cabin. Every vehicle gets an RFID sticker for residents and temporary passes for guests. Delivery personnel hand packages to security who coordinate with residents via intercom. Amazon and food delivery stay at the gate.

Over 120 CCTV cameras networked across the complex with monitoring station in security office. Parks and play areas have dedicated camera coverage. Parents access live feeds via society app. All visitors registered with phone number, photo, and visiting flat number. Domestic help requires police verification and society-issued ID cards.

Your children play freely while you cook dinner, monitoring via app when needed. The park stays resident-only, so unfamiliar faces are rare. Emergency protocols drilled quarterly. Fire exits clearly marked with quarterly inspections. The security isn't paranoia—it's systematic design that lets families breathe easier.

**Tagline:** Gated means guarded, guarded means peaceful.''',
    'image_url': 'https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=400&h=300&fit=crop',
    'category': 'safety'
},
{
    'id': 37,
    'title': 'Emergency Exits That Actually Work',
    'description': '''The building fire last year across town killed three people because stairwell doors were locked and fire exits opened to walls. You've started noticing these details everywhere: fire extinguishers never inspected, emergency lighting that doesn't work, exit signs faded and ignored. Most buildings treat safety compliance as paperwork, not protection.

This apartment complex has NOC certificates from fire department displayed publicly. Two staircases per tower with pressurized stairwells that stay smoke-free during fires. Emergency lighting powered by backup generators. Fire extinguishers inspected monthly with visible tags. Sprinkler systems tested quarterly.

Every apartment has smoke detectors wired to central alarm system. Fire doors are never locked and open outward. Building management conducts fire drills twice yearly with mandatory participation. Printed emergency evacuation maps in every apartment showing two exit routes. Society maintains 50,000-liter water reserve specifically for fire fighting.

The builder provided completion certificate only after full safety compliance. Insurance companies charge lower premiums here because risk assessment confirms standards. You've walked the fire exits yourself during a drill—they're wide, well-lit, and actually lead outside, not to locked gates or storage rooms.

**Tagline:** Safety standards that protect, not just check boxes.''',
    'image_url': 'https://images.unsplash.com/photo-1472214103451-9374bd1c798e?w=400&h=300&fit=crop',
    'category': 'safety'
},

# === TRANSPORT & CONNECTIVITY (3 scenarios) ===
{
    'id': 38,
    'title': 'Jet-Setter Living Minutes from Takeoff',
    'description': '''You fly twice monthly for work. Every trip begins with anxiety: Did I leave enough time for traffic? Will I make my 6 AM flight? Early morning departures mean 3 AM wake-ups because airport is 90 minutes away through unpredictable traffic. You've missed flights. You've paid surge pricing for last-minute cabs. Business travel exhaustion begins before boarding.

This apartment is 8.5 kilometers from the airport terminal via the elevated expressway.

**Timeline:**
4:45 AM — Wake up, shower, grab pre-packed luggage
5:15 AM — Drive out of covered parking
5:32 AM — Arrive at departure terminal, park in hourly lot
5:40 AM — Check-in counter, 80 minutes before 7 AM flight

Late evening return flights mean reaching home by 11 PM, not midnight. Cab drivers never cancel these bookings because distance is predictable. Your car stays in secure parking during trips. International flights with 3-hour advance requirements feel manageable. The mental load of travel reduces when logistics become simple mathematics.

Airport noise? The flight path is perpendicular to this area, so no overhead air traffic. You get proximity benefits without the sonic costs.

**Tagline:** Where business travel starts from peace, not panic.''',
    'image_url': 'https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=400&h=300&fit=crop',
    'category': 'transport'
},
{
    'id': 39,
    'title': 'Car-Free Living That Actually Works',
    'description': '''You've never owned a car by choice—environmental reasons, cost savings, and urban lifestyle preferences. But your current apartment makes this choice punishing. The bus stop is 1.2 kilometers away via roads without footpaths. Auto-rickshaws refuse short trips. Grocery shopping becomes elaborate planning. Rainy seasons mean isolation.

The main bus stop is 180 meters from your building gate—a 2-minute walk with covered pathway. Six bus routes pass through, connecting to three different metro stations, the main market, and hospital area. Buses run every 12 minutes during peak hours, every 20 minutes off-peak.

**Transport Options Available:**
- Bus Service - 180m walk, connects 6 routes, ₹10-30
- Auto Stand - Always available at society gate, app booking
- Metro Feeder - Society shuttle runs to station, free for residents
- Cycle Sharing - 4 rental stations within 500m radius
- App Cabs - 3-minute average waiting time

The neighborhood has wide footpaths with street lighting. Markets, pharmacy, and restaurants within 700 meters walking distance. Your monthly transport costs are ₹2,500 versus ₹15,000 for car ownership. The choice that felt restrictive elsewhere becomes liberating here through design that respects non-car mobility.

**Tagline:** Car-free by choice, not by compromise.''',
    'image_url': 'https://images.unsplash.com/photo-1544620347-c4fd4a3d5957?w=400&h=300&fit=crop',
    'category': 'transport'
},
{
    'id': 40,
    'title': 'Metro Corridor Living at Its Finest',
    'description': '''You take the metro to work, but your current apartment is 2.5 kilometers from the station. Morning auto rides are unreliable. Shared autos pack six people in space for four. Walking takes 30 minutes. Your metro commute is efficient, but reaching the metro isn't. The first-last mile problem drains energy before your workday begins.

The metro station is 320 meters from your tower—a 4-minute walk via covered pathway with zebra crossings. Exit gate 3 deposits you on the pedestrian bridge that connects directly to your society entrance. Morning rush means 8:42 AM departure puts you at office by 9:15 AM. Evening return is equally predictable.

**Timeline:**
8:35 AM — Leave apartment with coffee tumbler
8:42 AM — Tap metro card at entry gate
9:14 AM — Exit at office station
9:22 AM — Reach office desk, 8 minutes early

The apartment's resale value appreciates faster because metro proximity is permanent infrastructure, not dependent on traffic patterns. Your vehicle costs are minimal. Rainy seasons don't disrupt commutes. Late work nights don't require cab budgets. The metro becomes extension of your building—reliable, safe, and stress-free.

**Tagline:** When the metro is this close, the city becomes smaller.''',
    'image_url': 'https://images.unsplash.com/photo-1469854523086-cc02fe5d8800?w=400&h=300&fit=crop',
    'category': 'transport'
}
]
# Track current batch index (shared across all users)
current_batch_index = 0
BATCH_SIZE = 5

@scenario_bp.route('/pre-generated', methods=['GET'])
def get_pre_generated_scenarios():
    """Get 5 random pre-generated example scenarios"""
    try:
        # Return 5 random scenarios instead of all 40
        if len(SCENARIO_POOL) < 5:
            return jsonify({
                'error': 'Not enough scenarios in pool',
                'available': len(SCENARIO_POOL)
            }), 400
        
        random_scenarios = random.sample(SCENARIO_POOL, 5)
        
        logger.info(f"[PRE-GENERATED] ✅ Returned 5 random scenarios")
        
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
    Get next 5 scenarios sequentially from the pool
    Loops back to start after all 40 scenarios shown (8 batches total)
    
    Usage: GET /api/scenario/random
    """
    global current_batch_index  # ← ADDED: Allow modifying global counter
    
    try:
        # Validate pool size
        if len(SCENARIO_POOL) < 5:
            return jsonify({
                'error': 'Not enough scenarios in pool',
                'available': len(SCENARIO_POOL)
            }), 400
        
        # ← CHANGED: Sequential logic instead of random
        # Calculate start and end indices for current batch
        start_idx = current_batch_index * BATCH_SIZE
        end_idx = start_idx + BATCH_SIZE
        
        # Get the sequential batch (scenarios 0-4, then 5-9, etc.)
        batch_scenarios = SCENARIO_POOL[start_idx:end_idx]
        
        # Track which batch we're serving (1-8 for display)
        current_serving = current_batch_index + 1
        
        # Increment batch index and loop back to 0 after batch 8
        current_batch_index = (current_batch_index + 1) % 8  # 40 ÷ 5 = 8 batches
        
        logger.info(f"[SEQUENTIAL] ✅ Returned batch {current_serving}/8 (scenarios {start_idx+1}-{end_idx})")
        
        # ← CHANGED: Updated return with batch metadata
        return jsonify({
            'success': True,
            'scenarios': batch_scenarios,
            'batch_number': current_serving,
            'total_batches': 8,
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