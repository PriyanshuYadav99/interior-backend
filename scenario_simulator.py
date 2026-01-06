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
# SERVICE FUNCTIONS
# ============================================================

def generate_scenario_image(scenario_text, story_title):
    """
    Generate realistic scenario image using Replicate (FLUX Schnell)
    Expected time: 5-8 seconds
    """
    try:
        if not REPLICATE_API_TOKEN:
            return {
                'success': False,
                'error': 'REPLICATE_API_TOKEN not configured'
            }
        
        start_time = time.time()
        
        # SMART PROMPT - Extract key elements and visualize the actual scenario
        prompt = f"""
Professional photorealistic photograph directly showing this scenario: {scenario_text}

CRITICAL: The image MUST show the main subject/location mentioned in the scenario.
- If scenario mentions "park" or "playground" → show OUTDOOR park with kids playing
- If scenario mentions "restaurants" or "cafes" → show EXTERIOR street with cafes/restaurants
- If scenario mentions "quiet neighborhood" → show EXTERIOR peaceful residential street
- If scenario mentions "schools" → show EXTERIOR school building with kids
- If scenario mentions "lake" or "nature" → show OUTDOOR natural setting

IMAGE REQUIREMENTS:
Style: Professional lifestyle photography, documentary style
Camera: Sony A7R IV, 35mm-50mm lens, f/2.8-4, natural daylight
Setting: OUTDOOR scene matching the scenario description
People: Real families/individuals in natural, candid moments
Composition: Wide environmental shot showing the actual place/benefit
Lighting: Natural golden hour or bright daylight, soft shadows
Colors: Natural, warm, inviting tones

Quality: 8K, sharp focus, professional color grading, authentic textures

Mood: Warm, aspirational, safe, family-friendly, welcoming

AVOID: Interior shots (unless scenario specifically mentions interior), cartoon style, illustrations, artificial lighting, stock photo poses, CGI look

Focus on showing the ACTUAL BENEFIT or PLACE mentioned in the scenario with real people enjoying it naturally.
"""
        
        logger.info("[REPLICATE] Creating prediction for scenario image...")
        
        # Use FLUX Schnell with updated parameters for photorealism
        prediction_response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {REPLICATE_API_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "version": "black-forest-labs/flux-schnell",
                "input": {
                    "prompt": prompt,
                    "num_outputs": 1,
                    "aspect_ratio": "4:3",
                    "output_format": "png",
                    "output_quality": 95,  # Increased from 90
                    "num_inference_steps": 4,
                    "disable_safety_checker": False,
                    # Add negative prompt to avoid cartoon styles
                    "negative_prompt": "cartoon, illustration, anime, drawing, painting, sketch, CGI, 3D render, artificial, fake, toy-like, pixar style, disney style, animated"
                }
            },
            timeout=30
        )
        
        if prediction_response.status_code != 201:
            return {
                'success': False,
                'error': f'Replicate API error: {prediction_response.status_code}'
            }
        
        prediction_id = prediction_response.json().get("id")
        logger.info(f"[REPLICATE] Polling for result (ID: {prediction_id[:12]}...)...")
        
        # Poll for result
        max_attempts = 100
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(0.5)
            
            status_response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"},
                timeout=10
            )
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            if attempt % 10 == 0 and attempt > 0:
                logger.info(f"[REPLICATE] Status: {status} (~{attempt * 0.5:.1f}s)")
            
            if status == "succeeded":
                output = status_data.get("output")
                if not output:
                    return {'success': False, 'error': 'No output'}
                
                image_url = output[0] if isinstance(output, list) else output
                
                # Download image
                img_response = requests.get(image_url, timeout=30)
                image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                
                generation_time = time.time() - start_time
                
                logger.info(f"[REPLICATE] ✅ Image generated in {generation_time:.2f}s")
                
                return {
                    'success': True,
                    'image_base64': image_base64,
                    'generation_time': f"{generation_time:.2f}s"
                }
            
            elif status == "failed":
                return {
                    'success': False,
                    'error': status_data.get('error', 'Unknown error')
                }
            
            attempt += 1
        
        return {'success': False, 'error': 'Timeout after 50 seconds'}
        
    except Exception as e:
        logger.error(f"[REPLICATE ERROR] {str(e)}")
        return {
            'success': False,
            'error': str(e)
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

**Transport Options Available:**
- Own Vehicle - Direct basement access, no parking delay
- School Bus - Picks up from community main gate at 8:30 AM
- Carpool - Neighbor coordination via WhatsApp group
- Metro - Nearest station 1.2km, direct line to school area

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
            max_tokens=600,  # Increased to prevent mid-sentence cuts
            stop=None  # Let model complete naturally
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        # Enhanced parsing that preserves formatting
        lines = response_text.split('\n')
        title = ""
        story_content = []  # Changed from story_paragraphs to preserve structure
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
                # Preserve all content including empty lines for formatting
                story_content.append(line)
        
        # Clean up story content - remove leading/trailing empty lines only
        while story_content and not story_content[0].strip():
            story_content.pop(0)
        while story_content and not story_content[-1].strip():
            story_content.pop()
        
        # Check if last line ends mid-sentence (no proper punctuation)
        if story_content:
            last_line = story_content[-1].strip()
            if last_line and last_line[-1] not in '.!?':
                # Try to find the last complete sentence
                full_text = '\n'.join(story_content)
                
                # Find last occurrence of sentence-ending punctuation
                last_period = max(full_text.rfind('.'), full_text.rfind('!'), full_text.rfind('?'))
                
                if last_period > 0:
                    # Truncate to last complete sentence
                    full_text = full_text[:last_period + 1]
                    story_content = full_text.split('\n')
                    logger.warning("[GROQ] Truncated incomplete sentence")
        
        # Convert story_content to paragraphs for compatibility with frontend
        # Split by double newlines to identify paragraph breaks
        full_story = '\n'.join(story_content)
        
        # Identify paragraphs (separated by blank lines or bold markers like **)
        story_paragraphs = []
        current_para = []
        
        for line in story_content:
            stripped = line.strip()
            if not stripped:  # Empty line = paragraph break
                if current_para:
                    story_paragraphs.append('\n'.join(current_para))
                    current_para = []
            else:
                current_para.append(line)
        
        # Add last paragraph
        if current_para:
            story_paragraphs.append('\n'.join(current_para))
        
        generation_time = time.time() - start_time
        
        logger.info(f"[GROQ] ✅ Scenario generated in {generation_time:.2f}s")
        logger.info(f"[GROQ] Generated {len(story_paragraphs)} paragraphs")
        
        return {
            'success': True,
            'title': title,
            'story': story_paragraphs,  # Returns list of paragraphs with preserved formatting
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
# ROUTES
# ============================================================

@scenario_bp.route('/health', methods=['GET'])
def health():
    """Health check for scenario simulator"""
    return jsonify({
        'status': 'healthy',
        'module': 'scenario_simulator',
        'version': '1.0.0',
        'groq_configured': bool(groq_client),
        'replicate_configured': bool(REPLICATE_API_TOKEN)
    }), 200


@scenario_bp.route('/generate', methods=['POST', 'OPTIONS'])
def generate_scenario():
    """
    Generate a scenario with story and image
    
    Request body:
    {
        "scenario_text": "I have school-going kids, need safe roads, quiet environment",
        "client_name": "skyline" (optional)
    }
    
    Response:
    {
        "success": true,
        "title": "The 60-Decibel Drop",
        "story": [...],
        "tagline": "...",
        "image_base64": "..."
    }
    """
    if request.method == 'OPTIONS':
        return '', 204

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
        
        # Step 1: Generate story using Groq (fast - 1-2 seconds)
        logger.info("[SCENARIO] Step 1/2: Generating story with Groq...")
        story_result = generate_scenario_story(scenario_text)
        
        if not story_result.get('success'):
            return jsonify({
                'error': 'Failed to generate story',
                'details': story_result.get('error')
            }), 500
        
        # Step 2: Generate image using Replicate (5-8 seconds)
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
            'image_base64': image_result['image_base64'],
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


@scenario_bp.route('/pre-generated', methods=['GET'])
def get_pre_generated_scenarios():
    """
    Get pre-generated example scenarios
    Returns 5 example scenarios with placeholder data
    """
    try:
        scenarios = [
            {
                'id': 1,
                'title': 'School-going children, daily travel during peak hours.',
                'description': 'Family with kids needing safe school commute',
                'image_url': 'https://images.unsplash.com/photo-1580582932707-520aed937b7b?w=400&h=300&fit=crop'
            },
            {
                'id': 2,
                'title': 'Family with kids, sensitive to noise and calm surroundings.',
                'description': 'Peaceful environment for growing family',
                'image_url': 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=400&h=300&fit=crop'
            },
            {
                'id': 3,
                'title': 'Parents cautious about monsoon safety and access roads.',
                'description': 'Weather-resistant infrastructure priority',
                'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=400&h=300&fit=crop'
            },
            {
                'id': 4,
                'title': 'Family leisure focused on nearby lake and temple.',
                'description': 'Proximity to recreational and spiritual spaces',
                'image_url': 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400&h=300&fit=crop'
            },
            {
                'id': 5,
                'title': 'Long-term family living amid future area development.',
                'description': 'Investment in growing neighborhood',
                'image_url': 'https://images.unsplash.com/photo-1560518883-ce09059eeffa?w=400&h=300&fit=crop'
            }
        ]
        
        return jsonify({
            'success': True,
            'scenarios': scenarios
        }), 200

    except Exception as e:
        logger.error(f"[SCENARIO ERROR] {str(e)}")
        return jsonify({
            'error': 'Failed to get scenarios',
            'details': str(e)
        }), 500