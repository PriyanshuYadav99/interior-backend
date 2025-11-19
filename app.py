"""
AI Interior Design Backend - Properly Organized
Version: 6.0.0
"""

# ============================================================
# IMPORTS
# ============================================================
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import traceback
import base64
import time
import hashlib
import logging
from functools import wraps
from openai import OpenAI
import secrets
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client as TwilioClient
from supabase import create_client, Client

# Local imports
from config import (
    INTERIOR_STYLES, 
    FIXED_ROOM_LAYOUTS,
    ROOM_DESCRIPTIONS, 
    ROOM_IMAGES,
    THEME_ELEMENTS
)
from prompts import (
    construct_prompt,
    construct_fixed_layout_prompt,
    validate_inputs, 
    deconstruct_theme_to_realistic_elements,
    get_short_prompt_for_cache
)


# ============================================================
# LOGGING SETUP
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# CONFIGURATION
# ============================================================

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
FAL_API_KEY = os.getenv("FAL_API_KEY")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

# Email
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)

# Twilio for Phone OTP
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None

# Frontend URL
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Cache Settings
CACHE_DURATION = 1800  # 30 minutes
image_cache = {}


# ============================================================
# FLASK APP INITIALIZATION
# ============================================================
app = Flask(__name__)

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://interior-frontend-five.vercel.app",
            "http://localhost:5173",
            "http://localhost:3000",
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def timeout_decorator(seconds=120):
    """Decorator to add timeout to routes"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                if elapsed > seconds:
                    logger.warning(f"Request took {elapsed:.2f}s (exceeded {seconds}s timeout)")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Request failed after {elapsed:.2f}s: {str(e)}")
                raise
        return wrapper
    return decorator


def get_cached_image(prompt):
    """Check if we have a cached image for this prompt"""
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    if cache_key in image_cache:
        cached_data, timestamp = image_cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            logger.info(f"✅ Cache HIT for prompt: {prompt[:50]}...")
            return cached_data
        else:
            del image_cache[cache_key]
            logger.info(f"🗑️ Cache EXPIRED for prompt: {prompt[:50]}...")
    logger.info(f"❌ Cache MISS for prompt: {prompt[:50]}...")
    return None


def save_to_cache(prompt, image_data):
    """Save generated image to cache"""
    cache_key = hashlib.md5(prompt.encode()).hexdigest()
    image_cache[cache_key] = (image_data, time.time())
    logger.info(f"💾 Cached image for prompt: {prompt[:50]}...")


def clean_expired_cache():
    """Remove expired entries from cache"""
    current_time = time.time()
    expired_keys = [
        key for key, (_, timestamp) in image_cache.items()
        if current_time - timestamp >= CACHE_DURATION
    ]
    for key in expired_keys:
        del image_cache[key]
    if expired_keys:
        logger.info(f"🧹 Cleaned {len(expired_keys)} expired cache entries")


def optimize_prompt_for_dalle3(prompt, room_type):
    """Pre-process prompt to maximize DALL-E 3's layout accuracy"""
    # Remove decorative elements DALL-E ignores
    replacements = {
        "⚠️⚠️⚠️": "CRITICAL:", "⚠️": "CRITICAL:", "🔒": "", "✅": "", 
        "❌": "", "🏗️": "", "🪑": "", "🎨": "", "📸": "", "🚫": "",
        "1️⃣": "1.", "2️⃣": "2.", "3️⃣": "3.", "4️⃣": "4.",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━": "",
        "  ": " "
    }
    for old, new in replacements.items():
        prompt = prompt.replace(old, new)
    
    # Strengthen key architectural phrases
    prompt = prompt.replace("ARCHITECTURAL RENDERING", 
                          "ARCHITECTURAL RENDERING - EXACT LAYOUT REQUIRED")
    
    # Add architectural keywords at start
    if not prompt.startswith("Professional architectural"):
        prompt = f"Professional architectural interior photograph. {prompt}"
    
    logger.info(f"✅ Prompt optimized for DALL-E 3")
    return prompt


def generate_otp():
    """Generate 6-digit OTP"""
    return str(secrets.randbelow(900000) + 100000)


# ============================================================
# EMAIL & SMS FUNCTIONS
# ============================================================

def send_verification_email(user_id, email, token):
    """Send verification email"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.warning("⚠️ Email not configured")
            return False
        
        verify_link = f"{FRONTEND_URL}/verify?token={token}"
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🎨 Verify Your Email - AI Interior Design'
        msg['From'] = EMAIL_FROM
        msg['To'] = email
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
              <h2 style="color: #9333ea;">🎨 Welcome to AI Interior Design!</h2>
              <p>Thank you for registering. Verify your email to continue creating unlimited designs.</p>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="{verify_link}" 
                   style="background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%); 
                          color: white; 
                          padding: 15px 30px; 
                          text-decoration: none; 
                          border-radius: 8px; 
                          display: inline-block;
                          font-weight: bold;">
                  Verify Email Address
                </a>
              </div>
              
              <p style="color: #666; font-size: 14px;">
                Or copy this link:<br>
                <a href="{verify_link}" style="color: #9333ea;">{verify_link}</a>
              </p>
              
              <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
                Link expires in 24 hours.<br>
                If you didn't create an account, ignore this email.
              </p>
            </div>
          </body>
        </html>
        """
        
        msg.attach(MIMEText(html, 'html'))
        
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.send_message(msg)
        
        logger.info(f"✅ Verification email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Email error: {e}")
        traceback.print_exc()
        return False


def send_phone_otp(phone_number, country_code, otp):
    """Send OTP via Twilio SMS"""
    try:
        if not twilio_client:
            logger.warning("⚠️ Twilio not configured")
            return False
        
        country_dial_codes = {
            'IN': '+91', 'US': '+1', 'GB': '+44', 'CA': '+1', 'AU': '+61'
        }
        
        full_phone = f"{country_dial_codes.get(country_code, '+1')}{phone_number}"
        
        message = twilio_client.messages.create(
            body=f"Your Design Generator verification code is: {otp}. Valid for 10 minutes.",
            from_=TWILIO_PHONE_NUMBER,
            to=full_phone
        )
        
        logger.info(f"✅ OTP sent to {full_phone}")
        return True
        
    except Exception as e:
        logger.error(f"❌ SMS error: {e}")
        return False


# ============================================================
# AI IMAGE GENERATION PROVIDERS
# ============================================================

def generate_with_openai(prompt):
    """OpenAI DALL-E 3 - Maximum Quality"""
    try:
        if not openai_client:
            logger.warning("⚠️ No OpenAI API key found")
            return {"success": False, "error": "No API key"}
        
        logger.info("📡 Calling OpenAI DALL-E 3 HD...")
        
        original_length = len(prompt)
        
        # Optimize prompt if too long
        if len(prompt) > 3800:
            logger.warning(f"⚠️ Prompt too long ({original_length} chars), optimizing...")
            
            layout_lock = ""
            if "ARCHITECTURAL RENDERING" in prompt:
                layout_lock = prompt.split("FIXED ARCHITECTURAL")[0][:400]
            
            fixed_structure = ""
            if "FIXED ARCHITECTURAL" in prompt:
                start = prompt.find("FIXED ARCHITECTURAL")
                if "THEME APPLICATION" in prompt:
                    end = prompt.find("THEME APPLICATION")
                    fixed_structure = prompt[start:end][:1800]
                else:
                    fixed_structure = prompt[start:][:1800]
            
            theme_section = ""
            if "THEME APPLICATION" in prompt:
                start = prompt.find("THEME APPLICATION")
                if "RENDERING REQUIREMENTS" in prompt or "PHOTOGRAPHY" in prompt:
                    end = prompt.find("RENDERING REQUIREMENTS") if "RENDERING REQUIREMENTS" in prompt else prompt.find("PHOTOGRAPHY")
                    theme_section = prompt[start:end][:800]
                else:
                    theme_section = prompt[start:][:800]
            
            quality_specs = """

PHOTOGRAPHY REQUIREMENTS:
- Professional 8K photorealistic interior photography
- Ultra-sharp focus, perfect HDR lighting
- Accurate materials and textures
- Magazine-quality architectural rendering
- NO people, NO pets in scene

CRITICAL: Render exact furniture positions and room layout as specified above."""
            
            prompt = layout_lock + fixed_structure + theme_section + quality_specs
            logger.info(f"✅ Prompt optimized: {original_length} → {len(prompt)} chars")
        
        size = "1792x1024"  # Maximum resolution
        
        response = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="hd",
            style="natural",
            n=1,
            response_format="b64_json"
        )
        
        image_base64 = response.data[0].b64_json
        revised_prompt = response.data[0].revised_prompt
        
        logger.info(f"✅ DALL-E 3 HD Success! Resolution: {size}")
        
        if revised_prompt:
            prompt_similarity = len(revised_prompt) / len(prompt) if len(prompt) > 0 else 0
            if prompt_similarity < 0.5:
                logger.warning("⚠️⚠️ DALL-E HEAVILY REWROTE PROMPT!")
        
        return {
            "success": True,
            "image_base64": image_base64,
            "model": "dall-e-3-hd",
            "revised_prompt": revised_prompt,
            "size": size,
            "original_prompt_length": original_length,
            "final_prompt_length": len(prompt)
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ OpenAI DALL-E 3 failed: {error_msg}")
        
        if "invalid_size" in error_msg.lower():
            logger.error("📐 INVALID SIZE - Falling back to 1024x1024")
            try:
                response = openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="hd",
                    style="natural",
                    n=1,
                    response_format="b64_json"
                )
                return {
                    "success": True,
                    "image_base64": response.data[0].b64_json,
                    "model": "dall-e-3-hd",
                    "revised_prompt": response.data[0].revised_prompt,
                    "size": "1024x1024"
                }
            except:
                pass
        
        return {"success": False, "error": error_msg}


def generate_with_pollinations(prompt):
    """Pollinations AI - FREE"""
    try:
        import urllib.parse
        
        if len(prompt) > 600:
            prompt = prompt[:600]
        
        encoded_prompt = urllib.parse.quote(prompt)
        
        urls_to_try = [
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={int(time.time())}",
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024",
        ]
        
        for i, url in enumerate(urls_to_try):
            for retry in range(2):
                try:
                    if retry > 0:
                        logger.info(f"🔄 Retry {retry+1}/2 for format {i+1}")
                        time.sleep(2)
                    else:
                        logger.info(f"📡 Pollinations attempt {i+1}/{len(urls_to_try)}")
                    
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'image/png,image/jpeg,image/*'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=90, allow_redirects=True)
                    
                    if response.status_code == 530 and retry < 1:
                        logger.warning(f"⚠️ Service temporarily unavailable (530), retrying...")
                        continue
                    
                    if response.status_code == 200 and len(response.content) > 5000:
                        content_type = response.headers.get('content-type', '')
                        if 'image' in content_type or response.content[:4] in [b'\x89PNG', b'\xff\xd8\xff']:
                            image_base64 = base64.b64encode(response.content).decode('utf-8')
                            logger.info(f"✅ Pollinations success with format {i+1}")
                            return {
                                "success": True, 
                                "image_base64": image_base64,
                                "model": "pollinations"
                            }
                    
                    logger.warning(f"⚠️ Attempt {i+1} failed: HTTP {response.status_code}")
                    break
                    
                except requests.exceptions.Timeout:
                    logger.warning(f"⚠️ Attempt {i+1} timed out")
                    if retry < 1:
                        continue
                    break
                except Exception as attempt_error:
                    logger.warning(f"⚠️ Attempt {i+1} error: {attempt_error}")
                    break
        
        return {"success": False, "error": "Pollinations temporarily unavailable"}
        
    except Exception as e:
        logger.error(f"❌ Pollinations error: {e}")
        return {"success": False, "error": str(e)}


def generate_with_huggingface(prompt):
    """HuggingFace FLUX"""
    try:
        if not HUGGINGFACE_API_KEY:
            return {"success": False, "error": "No API key"}
        
        logger.info("📡 Calling HuggingFace FLUX...")
        
        API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 4
            }
        }
        
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            logger.error(f"❌ HuggingFace failed: {response.status_code}")
            return {"success": False, "error": response.text}
        
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        logger.info("✅ HuggingFace success!")
        
        return {
            "success": True,
            "image_base64": image_base64,
            "model": "huggingface-flux-schnell"
        }
        
    except Exception as e:
        logger.error(f"❌ HuggingFace error: {e}")
        return {"success": False, "error": str(e)}


def generate_with_fal(prompt):
    """FAL.ai FLUX"""
    try:
        if not FAL_API_KEY:
            return {"success": False, "error": "No API key"}
        
        logger.info("📡 Calling FAL.ai...")
        
        url = "https://fal.run/fal-ai/flux/schnell"
        headers = {
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "image_size": {"width": 1024, "height": 1024},
            "num_inference_steps": 4
        }
        
        for attempt in range(2):
            try:
                if attempt > 0:
                    time.sleep(3)
                
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                if response.status_code == 200:
                    result = response.json()
                    image_url = result.get('images', [{}])[0].get('url')
                    
                    if not image_url:
                        return {"success": False, "error": "No image URL returned"}
                    
                    img_response = requests.get(image_url, timeout=30)
                    
                    if img_response.status_code != 200:
                        if attempt < 1:
                            continue
                        return {"success": False, "error": f"Image download failed"}
                    
                    image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                    logger.info("✅ FAL.ai success!")
                    
                    return {
                        "success": True,
                        "image_base64": image_base64,
                        "model": "fal-flux-schnell"
                    }
                
                elif response.status_code in [429, 500, 502, 503, 504]:
                    if attempt < 1:
                        continue
                
                return {"success": False, "error": f"HTTP {response.status_code}"}
                
            except Exception as attempt_error:
                if attempt < 1:
                    continue
                return {"success": False, "error": str(attempt_error)}
        
        return {"success": False, "error": "All attempts failed"}
        
    except Exception as e:
        logger.error(f"❌ FAL.ai error: {e}")
        return {"success": False, "error": str(e)}


# ============================================================
# BASIC ROUTES
# ============================================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'healthy',
        'message': 'Property AI Backend with Fixed Layout System',
        'version': '6.0.0',
        'cache_size': len(image_cache),
        'features': ['fixed-layouts', 'theme-system', 'dalle3-hd-generation']
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    clean_expired_cache()
    return jsonify({
        'status': 'healthy',
        'providers': ['openai-dalle3-hd', 'pollinations', 'huggingface', 'fal'],
        'fixed_layout_system': 'enabled',
        'openai_configured': bool(OPENAI_API_KEY),
        'cache_entries': len(image_cache),
        'supported_rooms': list(FIXED_ROOM_LAYOUTS.keys()),
        'endpoints': ['/api/generate-design', '/api/rooms', '/api/styles', '/api/cache/clear']
    }), 200


@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached images"""
    cache_count = len(image_cache)
    image_cache.clear()
    logger.info(f"🧹 Manually cleared {cache_count} cache entries")
    return jsonify({
        'success': True,
        'message': f'Cleared {cache_count} cached images'
    }), 200


@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """Get available rooms with fixed layouts"""
    rooms = [
        {'id': room_id, 'name': room_id.replace('_', ' ').title()}
        for room_id in FIXED_ROOM_LAYOUTS.keys()
    ]
    return jsonify(rooms), 200


@app.route('/api/styles', methods=['GET'])
def get_styles():
    """Get available interior styles"""
    styles = [
        {'id': key, 'name': key.replace('_', ' ').title()}
        for key in INTERIOR_STYLES.keys()
    ]
    return jsonify(styles), 200


# ============================================================
# IMAGE GENERATION ROUTE
# ============================================================

@app.route('/api/generate-design', methods=['POST', 'OPTIONS'])
@timeout_decorator(180)
def generate_design():
    """Generate interior design with fixed layout system"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        room_type = data.get('room_type')
        style = data.get('style')
        custom_prompt = data.get('custom_prompt', '').strip()
        custom_dimensions = data.get('dimensions', '').strip()
        provider = data.get('provider', 'openai')

        # Validate inputs
        is_valid, message = validate_inputs(room_type, style, custom_prompt)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Get dimensions from fixed layouts
        if room_type in FIXED_ROOM_LAYOUTS:
            layout_info = FIXED_ROOM_LAYOUTS[room_type]
            dimensions = f"{layout_info['room_size']}, {layout_info['camera_angle']}"
        else:
            dimensions = custom_dimensions if custom_dimensions else ""

        # Build prompt
        prompt_data = construct_prompt(room_type, style, custom_prompt)
        if not prompt_data.get('success', True):
            return jsonify({'error': prompt_data.get('error', 'Prompt construction failed')}), 400
        
        prompt = prompt_data['prompt']
        prompt = optimize_prompt_for_dalle3(prompt, room_type)

        logger.info(f"🎨 Generating: {room_type} ({style or 'custom'}) using {provider}")

        # Check cache
        cached_result = get_cached_image(prompt)
        if cached_result:
            return jsonify({
                'success': True,
                'cached': True,
                'images': [cached_result],
                'prompt_used': prompt[:200] + '...'
            }), 200

        # Generate with selected provider
        result = None
        if provider == 'openai' and OPENAI_API_KEY:
            result = generate_with_openai(prompt)
        elif provider == 'pollinations':
            result = generate_with_pollinations(prompt)
        elif provider == 'huggingface':
            result = generate_with_huggingface(prompt)
        elif provider == 'fal':
            result = generate_with_fal(prompt)
        
        # Fallback chain
        if not result or not result.get('success'):
            logger.warning(f"⚠️ {provider} failed, trying fallback chain...")
            
            if provider != 'openai' and OPENAI_API_KEY:
                result = generate_with_openai(prompt)
            
            if not result or not result.get('success'):
                if provider != 'pollinations':
                    result = generate_with_pollinations(prompt)
            
            if not result or not result.get('success'):
                if provider != 'huggingface' and HUGGINGFACE_API_KEY:
                    result = generate_with_huggingface(prompt)
            
            if not result or not result.get('success'):
                if provider != 'fal' and FAL_API_KEY:
                    result = generate_with_fal(prompt)

        if not result or not result.get('success'):
            return jsonify({
                'error': 'Generation failed',
                'details': result.get('error', 'All providers failed') if result else 'No result returned'
            }), 500

        response_data = {
            'id': 0,
            'image_base64': result['image_base64'],
            'room_type': room_type,
            'style': style or 'custom',
            'model_used': result.get('model', 'unknown'),
            'revised_prompt': result.get('revised_prompt'),
            'layout_system': 'fixed',
            'resolution': result.get('size', '1024x1024')
        }

        save_to_cache(prompt, response_data)

        return jsonify({
            'success': True,
            'cached': False,
            'images': [response_data],
            'prompt_used': prompt[:200] + '...',
            'method': 'fixed-layout-generation'
        }), 200

    except Exception as e:
        logger.error(f"⚠️ Server Error: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


# ============================================================
# USER SESSION MANAGEMENT
# ============================================================

@app.route('/api/create-session', methods=['POST', 'OPTIONS'])
def create_session():
    """Create or update user session"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        if not session_id or not supabase:
            return jsonify({'error': 'Invalid request'}), 400
        
        existing_session = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
        if not existing_session.data:
            session_data = {
                'session_id': session_id,
                'user_id': user_id,
                'generation_count': 0,
                'is_verified': False,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'status': 'active'
            }
            supabase.table('sessions').insert(session_data).execute()
            logger.info(f"✅ New session created: {session_id}")
        else:
            supabase.table('sessions').update({
                'last_activity': datetime.now().isoformat(),
                'status': 'active'
            }).eq('session_id', session_id).execute()
            logger.info(f"✅ Session updated: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id
        }), 200

    except Exception as e:
        logger.error(f"❌ Create session error: {e}")
        return jsonify({'error': 'Session creation failed'}), 500


@app.route('/api/track-generation', methods=['POST', 'OPTIONS'])
def track_generation():
    """Track image generation"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        session_id = data.get('session_id')
        user_id = data.get('user_id')
        image_url = data.get('image_url')
        prompt = data.get('prompt')
        room_type = data.get('room_type')
        style = data.get('style')
        
        if not session_id or not supabase:
            return jsonify({'error': 'Invalid request'}), 400
        
        session = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
        if not session.data:
            return jsonify({'error': 'Session not found'}), 404
        
        current_session = session.data[0]
        generation_number = current_session['generation_count'] + 1
        was_verified = current_session['is_verified']
        
        generation_data = {
            'session_id': session_id,
            'user_id': user_id,
            'image_url': image_url,
            'prompt': prompt,
            'room_type': room_type,
            'style': style,
            'generation_number': generation_number,
            'was_verified_at_generation': was_verified
        }
        supabase.table('image_generations').insert(generation_data).execute()
        
        supabase.table('sessions').update({
            'generation_count': generation_number,
            'last_activity': datetime.now().isoformat()
        }).eq('session_id', session_id).execute()
        
        logger.info(f"✅ Generation tracked: {session_id} - Count: {generation_number}")
        
        return jsonify({
            'success': True,
            'generation_number': generation_number,
            'can_generate_more': was_verified or generation_number < 2
        }), 200

    except Exception as e:
        logger.error(f"❌ Track generation error: {e}")
        return jsonify({'error': 'Tracking failed'}), 500


# ============================================================
# USER REGISTRATION & AUTHENTICATION
# ============================================================

@app.route('/api/register-user', methods=['POST', 'OPTIONS'])
def register_user():
    """Register new user with session tracking"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone_number = data.get('phone_number', '').strip()
        country_code = data.get('country_code', 'US').strip()
        session_id = data.get('session_id', '').strip()

        if not full_name or len(full_name) < 2:
            return jsonify({'error': 'Full name is required'}), 400
        
        if not email or '@' not in email:
            return jsonify({'error': 'Valid email is required'}), 400
        
        if not supabase:
            return jsonify({'error': 'Database not configured'}), 500
        
        existing_user = supabase.table('users').select('*').eq('email', email).execute()
        
        is_duplicate = False
        user_id = None
        
        if existing_user.data and len(existing_user.data) > 0:
            is_duplicate = True
            user = existing_user.data[0]
            user_id = user['id']
            
            attempt_data = {
                'session_id': session_id,
                'email': email,
                'phone_number': phone_number,
                'full_name': full_name,
                'country_code': country_code,
                'is_duplicate': True,
                'existing_user_id': user_id,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
            supabase.table('registration_attempts').insert(attempt_data).execute()
            
            if user['email_verified'] and user.get('phone_verified', False):
                return jsonify({
                    'error': 'This email is already registered and verified.',
                    'already_verified': True
                }), 400
            
            verification_token = user.get('verification_token')
            if not verification_token:
                verification_token = secrets.token_urlsafe(32)
                token_expires = datetime.now() + timedelta(hours=24)
                
                supabase.table('users').update({
                    'verification_token': verification_token,
                    'verification_token_expires': token_expires.isoformat()
                }).eq('id', user_id).execute()
            
            send_verification_email(user_id, email, verification_token)
            
        else:
            verification_token = secrets.token_urlsafe(32)
            token_expires = datetime.now() + timedelta(hours=24)
            
            user_data = {
                'full_name': full_name,
                'email': email,
                'phone_number': phone_number,
                'country_code': country_code,
                'email_verified': False,
                'phone_verified': False,
                'verification_token': verification_token,
                'verification_token_expires': token_expires.isoformat(),
                'generation_count': 0
            }
            
            result = supabase.table('users').insert(user_data).execute()
            
            if not result.data:
                return jsonify({'error': 'Failed to create user'}), 500
            
            user_id = result.data[0]['id']
            
            attempt_data = {
                'session_id': session_id,
                'email': email,
                'phone_number': phone_number,
                'full_name': full_name,
                'country_code': country_code,
                'user_id': user_id,
                'is_duplicate': False,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', '')
            }
            supabase.table('registration_attempts').insert(attempt_data).execute()
            
            if session_id:
                supabase.table('sessions').update({
                    'user_id': user_id
                }).eq('session_id', session_id).execute()
            
            send_verification_email(user_id, email, verification_token)
        
        logger.info(f"✅ Registration: {email} (Duplicate: {is_duplicate})")
        
        return jsonify({
            'success': True,
            'message': 'Verification email sent again. Please check your inbox.' if is_duplicate else 'Registration successful! Please check your email to verify.',
            'user_id': user_id,
            'is_duplicate': is_duplicate
        }), 201

    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500


@app.route('/api/verify-email', methods=['GET', 'OPTIONS'])
def verify_email():
    """Verify user email"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        token = request.args.get('token')
        
        if not token:
            return jsonify({'error': 'Token required'}), 400
        
        if not supabase:
            return jsonify({'error': 'Database not configured'}), 500
        
        user_result = supabase.table('users').select('*').eq('verification_token', token).execute()
        
        if not user_result.data:
            return jsonify({'error': 'Invalid token'}), 400
        
        user = user_result.data[0]
        
        if user['verification_token_expires']:
            expires_at = datetime.fromisoformat(user['verification_token_expires'].replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) > expires_at:
                return jsonify({'error': 'Token expired'}), 400
        
        supabase.table('users').update({
            'email_verified': True,
            'verification_token': None,
            'verification_token_expires': None
        }).eq('id', user['id']).execute()
        
        supabase.table('sessions').update({
            'is_verified': True
        }).eq('user_id', user['id']).execute()
        
        supabase.table('registration_attempts').update({
            'email_verified': True,
            'registration_completed': True
        }).eq('user_id', user['id']).execute()
        
        logger.info(f"✅ Email verified: {user['email']}")
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully! You now have unlimited access.',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name']
            }
        }), 200

    except Exception as e:
        logger.error(f"❌ Verification error: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Verification failed'}), 500


@app.route('/api/check-user', methods=['POST', 'OPTIONS'])
def check_user():
    """Check if user exists"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email or not supabase:
            return jsonify({'exists': False, 'verified': False}), 200
        
        user_result = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user_result.data:
            return jsonify({'exists': False, 'verified': False}), 200
        
        user = user_result.data[0]
        
        return jsonify({
            'exists': True,
            'verified': user['email_verified'],
            'user': {
                'id': user['id'],
                'full_name': user['full_name'],
                'email': user['email']
            }
        }), 200

    except Exception as e:
        logger.error(f"❌ Check user error: {e}")
        return jsonify({'exists': False, 'verified': False}), 200


@app.route('/api/resend-verification', methods=['POST', 'OPTIONS'])
def resend_verification():
    """Resend verification email"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        
        if not email or not supabase:
            return jsonify({'error': 'Invalid request'}), 400
        
        user_result = supabase.table('users').select('*').eq('email', email).execute()
        
        if not user_result.data:
            return jsonify({'error': 'User not found'}), 404
        
        user = user_result.data[0]
        
        if user['email_verified']:
            return jsonify({'error': 'Already verified'}), 400
        
        new_token = secrets.token_urlsafe(32)
        token_expires = datetime.now() + timedelta(hours=24)
        
        supabase.table('users').update({
            'verification_token': new_token,
            'verification_token_expires': token_expires.isoformat()
        }).eq('id', user['id']).execute()
        
        send_verification_email(user['id'], email, new_token)
        
        return jsonify({
            'success': True,
            'message': 'Verification email sent!'
        }), 200

    except Exception as e:
        logger.error(f"❌ Resend error: {e}")
        return jsonify({'error': 'Failed to resend'}), 500


# ============================================================
# PHONE OTP VERIFICATION
# ============================================================

@app.route('/api/send-phone-otp', methods=['POST', 'OPTIONS'])
def send_otp():
    """Send phone OTP"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        country_code = data.get('country_code', 'IN')
        user_id = data.get('user_id')
        
        if not phone_number or not user_id or not supabase:
            return jsonify({'error': 'Invalid request'}), 400
        
        otp = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=10)
        
        supabase.table('users').update({
            'phone_otp': otp,
            'phone_otp_expires_at': expires_at.isoformat()
        }).eq('id', user_id).execute()
        
        otp_log_data = {
            'user_id': user_id,
            'phone_number': phone_number,
            'otp': otp,
            'expires_at': expires_at.isoformat(),
            'ip_address': request.remote_addr,
            'status': 'sent'
        }
        supabase.table('phone_otp_logs').insert(otp_log_data).execute()
        
        sms_sent = send_phone_otp(phone_number, country_code, otp)
        
        if not sms_sent:
            logger.warning(f"⚠️ SMS failed but OTP saved: {otp}")
        
        logger.info(f"✅ OTP sent to user {user_id}: {otp}")
        
        return jsonify({
            'success': True,
            'message': 'OTP sent successfully',
            'expires_in': 600
        }), 200

    except Exception as e:
        logger.error(f"❌ Send OTP error: {e}")
        return jsonify({'error': 'Failed to send OTP'}), 500


@app.route('/api/verify-phone-otp', methods=['POST', 'OPTIONS'])
def verify_otp():
    """Verify phone OTP"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        phone_number = data.get('phone_number')
        otp = data.get('otp')
        user_id = data.get('user_id')
        
        if not phone_number or not otp or not user_id or not supabase:
            return jsonify({'error': 'Invalid request'}), 400
        
        user = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if not user.data:
            return jsonify({'error': 'User not found'}), 404
        
        user_data = user.data[0]
        stored_otp = user_data.get('phone_otp')
        expires_at_str = user_data.get('phone_otp_expires_at')
        
        if stored_otp != otp:
            return jsonify({'error': 'Invalid OTP'}), 400
        
        if expires_at_str:
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            if datetime.now(expires_at.tzinfo) > expires_at:
                supabase.table('phone_otp_logs').update({
                    'status': 'expired'
                }).eq('user_id', user_id).eq('otp', otp).execute()
                return jsonify({'error': 'OTP expired. Please request a new one.'}), 400
        
        supabase.table('users').update({
            'phone_verified': True,
            'phone_otp': None,
            'phone_otp_expires_at': None
        }).eq('id', user_id).execute()
        
        supabase.table('phone_otp_logs').update({
            'verified_at': datetime.now().isoformat(),
            'status': 'verified'
        }).eq('user_id', user_id).eq('otp', otp).execute()
        
        supabase.table('registration_attempts').update({
            'phone_verified': True
        }).eq('user_id', user_id).order('attempt_time', desc=True).limit(1).execute()
        
        logger.info(f"✅ Phone verified for user {user_id}")
        
        return jsonify({
            'success': True,
            'message': 'Phone verified successfully!'
        }), 200

    except Exception as e:
        logger.error(f"❌ Verify OTP error: {e}")
        return jsonify({'error': 'OTP verification failed'}), 500


# ============================================================
# ANALYTICS & STATISTICS
# ============================================================

@app.route('/api/user-stats/<user_id>', methods=['GET', 'OPTIONS'])
def get_user_stats(user_id):
    """Get user statistics"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        if not supabase:
            return jsonify({'error': 'Database not configured'}), 500
        
        user = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if not user.data:
            return jsonify({'error': 'User not found'}), 404
        
        sessions = supabase.table('sessions').select('id').eq('user_id', user_id).execute()
        generations = supabase.table('image_generations').select('id').eq('user_id', user_id).execute()
        attempts = supabase.table('registration_attempts').select('id').eq('user_id', user_id).execute()
        
        stats = {
            'user': user.data[0],
            'total_sessions': len(sessions.data) if sessions.data else 0,
            'total_generations': len(generations.data) if generations.data else 0,
            'registration_attempts': len(attempts.data) if attempts.data else 0
        }
        
        return jsonify({
            'success': True,
            'stats': stats
        }), 200

    except Exception as e:
        logger.error(f"❌ Stats error: {e}")
        return jsonify({'error': 'Failed to fetch stats'}), 500


@app.route('/api/session-history/<session_id>', methods=['GET', 'OPTIONS'])
def get_session_history(session_id):
    """Get session history"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        if not supabase:
            return jsonify({'error': 'Database not configured'}), 500
        
        session = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
        if not session.data:
            return jsonify({'error': 'Session not found'}), 404
        
        generations = supabase.table('image_generations').select('*').eq('session_id', session_id).order('generated_at', desc=True).execute()
        
        return jsonify({
            'success': True,
            'session': session.data[0],
            'generations': generations.data if generations.data else []
        }), 200

    except Exception as e:
        logger.error(f"❌ Session history error: {e}")
        return jsonify({'error': 'Failed to fetch history'}), 500


# ============================================================
# SERVER STARTUP
# ============================================================

if __name__ == '__main__':
    logger.info("\n" + "="*70)
    logger.info("✅ AI Interior Design Backend Ready!")
    logger.info("="*70)
    logger.info(f"🎨 Fixed Layout System: ✅ ENABLED")
    logger.info(f"📌 Supported Rooms: {', '.join(FIXED_ROOM_LAYOUTS.keys())}")
    logger.info(f"🎭 Available Themes: {len(THEME_ELEMENTS['color_palettes'])} auto-detected")
    logger.info("="*70)
    logger.info(f"📡 OpenAI DALL-E 3: {'✅ Configured (HD Quality 1792x1024)' if OPENAI_API_KEY else '❌ Not configured'}")
    logger.info(f"📡 Pollinations: ✅ Always available (FREE)")
    logger.info(f"📡 Hugging Face: {'✅ Configured' if HUGGINGFACE_API_KEY else '❌ Not configured'}")
    logger.info(f"📡 FAL.ai: {'✅ Configured' if FAL_API_KEY else '❌ Not configured'}")
    logger.info("="*70)
    logger.info(f"🔐 Supabase: {'✅ Connected' if supabase else '❌ Not configured'}")
    logger.info(f"📧 Email: {'✅ Ready' if EMAIL_USER and EMAIL_PASSWORD else '❌ Not configured'}")
    logger.info(f"📱 Twilio SMS: {'✅ Ready' if twilio_client else '❌ Not configured'}")
    logger.info(f"💾 Cache Duration: {CACHE_DURATION // 60} minutes")
    logger.info(f"📝 Logging to: app.log")
    logger.info("="*70)
    logger.info("🚀 Starting Flask server on http://localhost:5000")
    logger.info("="*70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)