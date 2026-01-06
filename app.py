# Standard library imports first
import os
import sys
import io
import base64
import time
import hashlib
import logging
import traceback
import tempfile
import secrets
import smtplib
import threading
from functools import wraps
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# Third-party imports
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from supabase import create_client, Client
from PIL import Image
import cloudinary
import cloudinary.uploader
import cloudinary.api
import requests
from scenario_simulator import scenario_bp

# Load environment variables
load_dotenv()

# ============================================================
# LOGGING SETUP - MUST BE FIRST!
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# IMPORT PROJECT MODULES - AFTER LOGGER
# ============================================================
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
    construct_custom_theme_prompt,
    validate_inputs, 
    deconstruct_theme_to_realistic_elements,
    get_short_prompt_for_cache
)

# ✅ ADD THESE 2 LINES SEPARATELY (AFTER the prompts import)
from whatsapp_service import send_notification_to_user
from scheduler import init_scheduler, start_scheduler, schedule_user_notification

# ============================================================
# API CONFIGURATION - AFTER LOGGER
# ============================================================





# ============================================================
# CONFIGURATION
# ============================================================

# API Keys
# Initialize Replicate client
# Set your API key as environment variable: export REPLICATE_API_TOKEN="your_token"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")



# Replicate API Token (for interior design model)
if REPLICATE_API_TOKEN:
    logger.info("[SETUP] Replicate API configured successfully")
else:
    logger.warning("[SETUP] REPLICATE_API_TOKEN not set - Image generation will not work")

# Supabase
# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
# ❌ MongoDB removed - using Supabase only
mongo_client = None
db = None
logger.info("[SETUP] 📦 Using Supabase as primary database (MongoDB removed)")
# Email
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)




# Frontend URL
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5177/")

# Cache Settings
CACHE_DURATION = 1800  # 30 minutes
image_cache = {}

# Cloudinary Setup
cloudinary.config(
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key = os.getenv("CLOUDINARY_API_KEY"),
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
)
# ============================================================
# FLASK APP INITIALIZATION
# ============================================================
app = Flask(__name__)

CORS(app, 
     origins="*",
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type"],
     supports_credentials=False,
     max_age=3600)


# Force headers on every response
@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
    response.headers["Access-Control-Max-Age"] = "3600"
    
    # Handle preflight OPTIONS requests
    if request.method == "OPTIONS":
        response.status_code = 200
    
    return response

# OpenAI client (not needed anymore since we use FLUX)
openai_client = None

# ============================================================
# REGISTER BLUEPRINTS - MUST BE HERE FOR PRODUCTION
# ============================================================
try:
    app.register_blueprint(scenario_bp)
    logger.info("[SETUP] ✅ Scenario Simulator blueprint registered at /api/scenario")
    
    # Verify routes are registered
    scenario_routes = [rule for rule in app.url_map.iter_rules() if 'scenario' in rule.rule]
    logger.info(f"[SETUP] Found {len(scenario_routes)} scenario routes:")
    for route in scenario_routes:
        logger.info(f"  ✓ {route.rule} [{', '.join(route.methods - {'HEAD', 'OPTIONS'})}]")
        
except Exception as e:
    logger.error(f"[SETUP] ❌ Failed to register scenario blueprint: {e}")
    import traceback
    traceback.print_exc()

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


def get_cached_image(prompt, client_name='default'):
    """Check if we have a cached image for this prompt + client combo"""
    cache_key = hashlib.md5(f"{client_name}:{prompt}".encode()).hexdigest()
    if cache_key in image_cache:
        cached_data, timestamp = image_cache[cache_key]
        if time.time() - timestamp < CACHE_DURATION:
            logger.info(f"[SUCCESS] Cache HIT for client={client_name}, prompt: {prompt[:50]}...")
            return cached_data
        else:
            del image_cache[cache_key]
            logger.info(f"[INFO] Cache EXPIRED for client={client_name}, prompt: {prompt[:50]}...")
    logger.info(f"[INFO] Cache MISS for client={client_name}, prompt: {prompt[:50]}...")
    return None


def save_to_cache(prompt, image_data, client_name='default'):
    """Save generated image to cache with client context"""
    cache_key = hashlib.md5(f"{client_name}:{prompt}".encode()).hexdigest()
    image_cache[cache_key] = (image_data, time.time())
    logger.info(f"[CACHE] Cached image for client={client_name}: {prompt[:50]}...")
def save_generation_to_db(client_name, room_type, style, custom_prompt, generated_image_url, user_id=None, session_id=None):
    """Save generation to Supabase only (MongoDB removed for performance)"""
    try:
        if not supabase or not generated_image_url:
            logger.warning("[DB] Supabase or image URL missing")
            return None
        
        # Generate unique ID
        generation_id = f"gen_{int(time.time())}_{secrets.token_hex(4)}"
        
        # ✅ STEP 1: Save generation to user_generations
        user_gen_data = {
            'generation_id': generation_id,
            'user_id': user_id,
            'session_id': session_id,
            'client_name': client_name,
            'room_type': room_type,
            'style': style,
            'custom_prompt': custom_prompt,
            'image_url': generated_image_url,
            'downloaded': False,
            'download_count': 0
        }
        
        result = supabase.table('user_generations').insert(user_gen_data).execute()
        
        if not result.data:
            logger.error(f"[DB] ❌ Failed to save generation")
            return None
        
        logger.info(f"[DB] ✅ Saved generation: {generation_id}")
        
        # ✅ STEP 2: Update client statistics
        try:
            # Check if client exists
            client_result = supabase.table('client_stats')\
                .select('total_generations')\
                .eq('client_name', client_name)\
                .execute()
            
            if client_result.data:
                # Client exists - increment
                current_count = client_result.data[0]['total_generations']
                supabase.table('client_stats')\
                    .update({
                        'total_generations': current_count + 1,
                        'updated_at': datetime.now().isoformat()
                    })\
                    .eq('client_name', client_name)\
                    .execute()
                logger.info(f"[DB] ✅ Incremented {client_name}: {current_count} → {current_count + 1}")
            else:
                # Client doesn't exist - create new
                supabase.table('client_stats').insert({
                    'client_name': client_name,
                    'total_generations': 1,
                    'total_downloads': 0
                }).execute()
                logger.info(f"[DB] ✅ Created stats for client: {client_name}")
                
        except Exception as stats_error:
            logger.warning(f"[DB] Could not update client stats: {stats_error}")
        
        return generation_id
        
    except Exception as e:
        logger.error(f"[DB ERROR] Failed to save: {e}")
        import traceback
        traceback.print_exc()
        return None
    
def upload_to_cloudinary(image_base64, client_name, room_type):
    """Upload generated image to Cloudinary"""
    try:
        upload_result = cloudinary.uploader.upload(
            f"data:image/png;base64,{image_base64}",
            folder=f"generated/{client_name}",
            public_id=f"{room_type}_{int(time.time())}",
            resource_type="image"
        )
        
        image_url = upload_result['secure_url']
        logger.info(f"[CLOUDINARY] Uploaded image: {image_url}")
        return image_url
        
    except Exception as e:
        logger.error(f"[CLOUDINARY ERROR] Upload failed: {e}")
        return None
    
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
        logger.info(f"[CLEANUP] Cleaned {len(expired_keys)} expired cache entries")


def optimize_prompt_for_gpt_image1(prompt, room_type):
    """Pre-process prompt for GPT Image 1"""
    replacements = {
        "⚠️": "", "✅": "", "❌": "", "🔒": "", "🏗️": "", 
        "🪑": "", "🎨": "", "📸": "", "🚫": "", "━": ""
    }
    for old, new in replacements.items():
        prompt = prompt.replace(old, new)
    
    prompt = " ".join(prompt.split())
    logger.info(f"[SUCCESS] Prompt optimized for GPT Image 1 (Length: {len(prompt)} chars)")
    return prompt


def load_reference_image(room_type, client_name='skyline'):
    """Load and convert reference image to PNG format for OpenAI - WITH CLIENT SUPPORT"""
    try:
        # Build client-specific path
        if client_name and client_name != 'default':
            # Client-specific images
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Map room_type to actual filename based on client
            if client_name == 'skyline':
                filename_map = {
                    'master_bedroom': 'skyline_bedroom.webp',
                    'living_room': 'skyline_living_room.webp',
                    'kitchen': 'skyline_kitchen.webp'
                }
            elif client_name == 'ellington':
                filename_map = {
                    'master_bedroom': 'ellington_bedroom.webp',
                    'living_room': 'ellington_living_room.webp',
                    'kitchen': 'ellington_kitchen.webp'
                }
            else:
                logger.error(f"Unknown client: {client_name}")
                return None
            
            filename = filename_map.get(room_type)
            if not filename:
                logger.error(f"No filename mapping for {room_type} in {client_name}")
                return None
            
            image_path = os.path.join(base_dir, 'images', client_name, filename)
            
            if not os.path.exists(image_path):
                logger.warning(f"Client image not found: {image_path}, falling back to default")
                # Fallback to default
                image_path = ROOM_IMAGES.get(room_type)
        else:
            # Default images (your current setup)
            if room_type not in ROOM_IMAGES:
                logger.error(f"No reference image found for {room_type}")
                return None
            image_path = ROOM_IMAGES[room_type]
        
        if not os.path.exists(image_path):
            logger.error(f"Reference image not found at path: {image_path}")
            return None
        
        logger.info(f"[INFO] Loading image from: {image_path} (Client: {client_name})")
        
        img = Image.open(image_path)
        
        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save as PNG to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        image_data = img_byte_arr.read()
        
        # Convert to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        logger.info(f"[SUCCESS] Loaded reference image for {room_type} - {client_name} ({len(image_data)} bytes)")
        return image_base64
        
    except Exception as e:
        logger.error(f"[ERROR] Error loading reference image: {e}")
        traceback.print_exc()
        return None





# ============================================================
# EMAIL & SMS FUNCTIONS
# ============================================================

def send_welcome_email(full_name, email):
    """Send simple welcome email after registration"""
    try:
        if not EMAIL_USER or not EMAIL_PASSWORD:
            logger.warning("[WARNING] Email not configured")
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = '🎨 Welcome to AI Interior Design Generator!'
        msg['From'] = EMAIL_FROM
        msg['To'] = email
        
        html = f"""
        <html>
          <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
              <h1 style="color: white; margin: 0; font-size: 28px;">🎨 Welcome {full_name}!</h1>
            </div>
            
            <div style="background: white; padding: 30px; border: 2px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
              <p style="font-size: 18px; color: #111827; margin-top: 0;">
                Thank you for registering! 🎉
              </p>
              
              <p style="font-size: 16px; color: #374151;">
                You now have <strong style="color: #9333ea;">unlimited access</strong> to generate stunning AI-powered interior designs!
              </p>
              
              <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #f59e0b;">
                <h3 style="margin-top: 0; color: #92400e; font-size: 18px;">✨ What You Can Do Now:</h3>
                <ul style="color: #78350f; margin: 10px 0; padding-left: 20px;">
                  <li style="margin: 8px 0;">Generate unlimited interior designs</li>
                  <li style="margin: 8px 0;">Choose from multiple styles (Modern, Scandinavian, Industrial & more)</li>
                  <li style="margin: 8px 0;">Create custom themes with your imagination</li>
                  <li style="margin: 8px 0;">Download all your designs in high quality</li>
                </ul>
              </div>
              
              <div style="text-align: center; margin: 30px 0;">
                <a href="{FRONTEND_URL}" style="display: inline-block; background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(147, 51, 234, 0.3);">
                  Start Creating Now →
                </a>
              </div>
              
              <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                <strong>Your Details:</strong><br>
                Name: {full_name}<br>
                Email: {email}
              </p>
              
              <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              
              <p style="color: #9ca3af; font-size: 13px; text-align: center; margin-bottom: 0;">
                Need help? Reply to this email and we'll assist you.<br>
                Happy designing! 🏠✨
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
        
        logger.info(f"[SUCCESS] Welcome email sent to {email}")
        return True
        
    except Exception as e:
        logger.error(f"[ERROR] Email error: {e}")
        traceback.print_exc()
        return False





# ============================================================
# AI IMAGE GENERATION - IMAGE-TO-IMAGE
# ============================================================
# ============================================================
# AI IMAGE GENERATION - IMAGE-TO-IMAGE
# ============================================================
# ============================================================
# GLOBAL CACHE FOR MODEL VERSION
# ============================================================
_cached_model_version = None
_version_cache_time = None
VERSION_CACHE_DURATION = 3600  # 1 hour

def get_cached_model_version():
    """Get model version with 1-hour caching - SAVES 1-2 SECONDS"""
    global _cached_model_version, _version_cache_time
    
    current_time = time.time()
    
    # Return cached version if valid
    if _cached_model_version and _version_cache_time:
        if current_time - _version_cache_time < VERSION_CACHE_DURATION:
            logger.info("[CACHE] Using cached model version ⚡")
            return _cached_model_version
    
    # Fetch new version
    logger.info("[API] Fetching model version...")
    try:
        model_response = requests.get(
            "https://api.replicate.com/v1/models/adirik/interior-design",
            headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"},
            timeout=10
        )
        
        if model_response.status_code != 200:
            # If cache exists, use stale cache
            if _cached_model_version:
                logger.warning("[CACHE] Using stale cache (fetch failed)")
                return _cached_model_version
            raise Exception(f"Model fetch failed: {model_response.status_code}")
        
        latest_version = model_response.json().get("latest_version", {}).get("id")
        if not latest_version:
            if _cached_model_version:
                return _cached_model_version
            raise Exception("No model version found")
        
        # Cache it
        _cached_model_version = latest_version
        _version_cache_time = current_time
        
        logger.info(f"[CACHE] Cached version: {latest_version[:16]}... ✅")
        return latest_version
        
    except Exception as e:
        if _cached_model_version:
            logger.warning(f"[CACHE] Using stale cache: {e}")
            return _cached_model_version
        raise


# ============================================================
# SINGLE UNIFIED GENERATION FUNCTION (REPLACES ALL 3)
# ============================================================
def generate_interior_design_unified(
    prompt, 
    reference_image_base64,
    room_type="living_room",
    is_custom_theme=False,
    width=1024,
    height=1024
):
    """
    UNIFIED: Single function for both flows
    
    FLOW 1: Style-based (is_custom_theme=False)
    - Parameters: guidance_scale=10, prompt_strength=0.82, steps=28
    
    FLOW 2: Custom theme (is_custom_theme=True)  
    - Parameters: guidance_scale=10, prompt_strength=0.92, steps=32
    
    Expected time: 7-8 seconds
    """
    try:
        if not REPLICATE_API_TOKEN:
            return {"success": False, "error": "REPLICATE_API_TOKEN not set"}
        
        flow_name = "CUSTOM THEME" if is_custom_theme else "STYLE-BASED"
        logger.info(f"[{flow_name}] Starting generation for {room_type}...")
        start_time = time.time()
        
        # Optimize prompt length
        if len(prompt) > 800:
            prompt = prompt[:800]
        
        # Enhanced prompt based on flow
        if is_custom_theme:
            # FLOW 2: Custom theme - more dramatic
            enhanced_prompt = (
                f"{prompt}, complete interior redesign, dramatic transformation, "
                f"professional architectural photography, luxury interior, "
                f"high-end design, modern aesthetic, natural lighting, 8k ultra detailed"
            )
        else:
            # FLOW 1: Style-based - balanced
            enhanced_prompt = (
                f"{prompt}, {room_type} interior design, "
                f"professional architectural photography, modern luxury space, "
                f"high-end real estate photo, natural lighting, 8k quality"
            )
        
        # Get cached model version (SAVES 1-2 SECONDS)
        latest_version = get_cached_model_version()
        
        logger.info(f"[{flow_name}] Creating prediction...")
        
        # Parameters optimized by flow
        if is_custom_theme:
            # FLOW 2: Custom - Higher transformation
            guidance_scale = 10
            prompt_strength = 0.92  # More dramatic change
            num_inference_steps = 32  # Slightly more for quality
        else:
            # FLOW 1: Style - Balanced
            guidance_scale = 10
            prompt_strength = 0.82  # Moderate change
            num_inference_steps = 28  # Faster
        
        # Create prediction
        prediction_response = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={
                "Authorization": f"Token {REPLICATE_API_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "version": latest_version,
                "input": {
                    "image": f"data:image/png;base64,{reference_image_base64}",
                    "prompt": enhanced_prompt,
                    "negative_prompt": (
                        "lowres, bad quality, watermark, text, logo, worst quality, "
                        "low quality, blurry, pixelated, deformed, ugly" +
                        (", boring, plain" if is_custom_theme else "")
                    ),
                    "guidance_scale": guidance_scale,
                    "prompt_strength": prompt_strength,
                    "num_inference_steps": num_inference_steps
                }
            },
            timeout=30
        )
        
        if prediction_response.status_code != 201:
            return {"success": False, "error": prediction_response.text}
        
        prediction_id = prediction_response.json().get("id")
        logger.info(f"[{flow_name}] Polling (ID: {prediction_id[:12]}...)...")
        
        # Fast polling - 0.5 second intervals
        max_attempts = 200
        attempt = 0
        
        while attempt < max_attempts:
            time.sleep(0.3)
            
            status_response = requests.get(
                f"https://api.replicate.com/v1/predictions/{prediction_id}",
                headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"},
                timeout=10
            )
            
            status_data = status_response.json()
            status = status_data.get("status")
            
            # Reduced logging - only every 10 attempts (~5 seconds)
            if attempt % 20 == 0 and attempt > 0:
                elapsed = attempt * 0.3
                logger.info(f"[{flow_name}] {status} (~{elapsed:.1f}s)")
            
            if status == "succeeded":
                output = status_data.get("output")
                if not output:
                    return {"success": False, "error": "No output"}
                
                image_url = output[0] if isinstance(output, list) else output
                img_response = requests.get(image_url, timeout=30)
                image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                
                generation_time = time.time() - start_time
                
                logger.info(f"{'='*60}")
                logger.info(f"[SUCCESS] ⚡ {flow_name}: {generation_time:.2f}s")
                logger.info(f"{'='*60}")
                
                return {
                    "success": True,
                    "image_base64": image_base64,
                    "model": "adirik/interior-design",
                    "size": "1024x1024",
                    "room_type": room_type,
                    "method": f"unified_{'custom' if is_custom_theme else 'style'}",
                    "generation_time": f"{generation_time:.2f}s",
                    "flow": "FLOW 2" if is_custom_theme else "FLOW 1",
                    "parameters": {
                        "guidance_scale": guidance_scale,
                        "prompt_strength": prompt_strength,
                        "steps": num_inference_steps
                    }
                }
            
            elif status == "failed":
                error = status_data.get("error", "Unknown error")
                logger.error(f"[ERROR] {flow_name} failed: {error}")
                return {"success": False, "error": error}
            
            attempt += 1
        
        return {"success": False, "error": "Timeout after 75 seconds"}
        
    except Exception as e:
        logger.error(f"[ERROR] {flow_name}: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# ============================================================
# WRAPPER FUNCTIONS (KEEP YOUR EXISTING API INTACT)
# ============================================================

def generate_with_gemini_flash_image(prompt, room_type, reference_image_base64):
    """
    WRAPPER: Maintains backward compatibility
    Calls unified function with is_custom_theme=False
    """
    return generate_interior_design_unified(
        prompt=prompt,
        reference_image_base64=reference_image_base64,
        room_type=room_type,
        is_custom_theme=False
    )


def generate_with_openai_style_based(prompt, room_type, reference_image_base64, width=1024, height=1024):
    """
    FLOW 1 WRAPPER: Style-based generation
    Calls unified function with is_custom_theme=False
    """
    return generate_interior_design_unified(
        prompt=prompt,
        reference_image_base64=reference_image_base64,
        room_type=room_type,
        is_custom_theme=False,
        width=width,
        height=height
    )


def generate_with_openai_custom_theme(prompt, reference_image_base64, width=1024, height=1024):
    """
    FLOW 2 WRAPPER: Custom theme generation
    Calls unified function with is_custom_theme=True
    """
    return generate_interior_design_unified(
        prompt=prompt,
        reference_image_base64=reference_image_base64,
        room_type="custom",
        is_custom_theme=True,
        width=width,
        height=height
    )


# ============================================================
# BASIC ROUTES
# ============================================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'healthy',
        'message': 'AI Interior Design Backend - Imagen 3 Powered',
        'version': '12.0.0',
        'models': ['imagen-3'],
        'features': ['ai-generation', 'email-verification', 'multi-client']
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    clean_expired_cache()
    return jsonify({
        'status': 'healthy',
        'replicate_configured': bool(REPLICATE_API_TOKEN),
        'email_configured': bool(EMAIL_USER and EMAIL_PASSWORD),
        'supabase_configured': bool(supabase),
        'cache_entries': len(image_cache),
        'available_models': ['adirik/interior-design'] if REPLICATE_API_TOKEN else []
    }), 200


@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """Get available rooms with reference images"""
    rooms = [
        {
            'id': room_id, 
            'name': room_id.replace('_', ' ').title(),
            'has_reference': room_id in ROOM_IMAGES
        }
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
# REGISTRATION & OTP ENDPOINTS (unchanged)
# ============================================================

@app.route('/api/simple-register', methods=['POST', 'OPTIONS'])
def simple_register():
    """Simple registration - NO OTP, NO duplicate checks - ALLOW EVERYTHING"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()
        phone_number = data.get('phone_number', '').strip()
        country_code = data.get('country_code', 'IN')
        session_id = data.get('session_id')
        generated_count = data.get('generated_count', 0)
        
        logger.info(f"[SIMPLE_REGISTER] New registration - Email: {email}, Phone: {phone_number}")
        
        # Validation - ALL fields required
        if not full_name or not email or not phone_number:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(phone_number) < 10:
            return jsonify({'error': 'Phone number must be at least 10 digits'}), 400
        
        if '@' not in email or '.' not in email:
            return jsonify({'error': 'Invalid email address'}), 400
        
        if not supabase:
            return jsonify({'error': 'Database not configured'}), 500
        
        # ✅ NO DUPLICATE CHECKS - Allow all registrations (even duplicates)
        logger.info(f"[SIMPLE_REGISTER] Creating new user (duplicates allowed): {email}, {phone_number}")
        
        # Create new user - NO checks, always insert
        user_data = {
            'full_name': full_name,
            'email': email,
            'phone_number': phone_number,
            'country_code': country_code,
            'pre_registration_generations': generated_count,
            'total_generations': 0,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')
        }
        
        new_user = supabase.table('users').insert(user_data).execute()
        
        if not new_user.data:
            return jsonify({'error': 'Failed to create user'}), 500
        
        user_id = new_user.data[0]['id']
        logger.info(f"[SIMPLE_REGISTER] New user created: {email} (ID: {user_id})")

        # ✅ ADD THESE 4 LINES - Schedule WhatsApp/SMS notification
        if supabase:
            schedule_user_notification(user_id, phone_number, country_code, delay_minutes=2, supabase=supabase)
            logger.info(f"[SIMPLE_REGISTER] ✅ WhatsApp notification scheduled for {email} in 30 minutes")

        # Update session
        if session_id:
            try:
                supabase.table('sessions').update({
                    'user_id': user_id,
                    'is_registered': True,
                    'generation_count': 0
                }).eq('session_id', session_id).execute()
            except Exception as e:
                logger.warning(f"[SIMPLE_REGISTER] Session update failed: {e}")
        
        # ✅ Send welcome email in background thread (non-blocking)
        def send_email_async():
            try:
                send_welcome_email(full_name, email)
                logger.info(f"[SIMPLE_REGISTER] Welcome email sent to {email}")
            except Exception as e:
                logger.warning(f"[SIMPLE_REGISTER] Failed to send welcome email: {e}")
        
        # Start email thread in background
        email_thread = threading.Thread(target=send_email_async, daemon=True)
        email_thread.start()
        logger.info(f"[SIMPLE_REGISTER] Email queued for background sending")
        
        logger.info(f"[SIMPLE_REGISTER] Registration complete for {email}")
        
        return jsonify({
            'success': True,
            'message': 'Registration successful! You now have unlimited access.',
            'user_id': user_id,
            'email': email,
            'phone_number': phone_number
        }), 200

    except Exception as e:
        logger.error(f"[SIMPLE_REGISTER] Error: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Registration failed', 'details': str(e)}), 500


@app.route('/api/check-user', methods=['POST', 'OPTIONS'])
def check_user_status():
    """Check if user is registered (simplified - no verification needed)"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        phone_number = data.get('phone_number', '').strip()
        
        if not phone_number:
            return jsonify({'error': 'Phone number required'}), 400
        
        if not supabase:
            return jsonify({'error': 'Database not configured'}), 500
        
        # Find user by phone
        user_result = supabase.table('users').select('*').eq('phone_number', phone_number).execute()
        
        if not user_result.data:
            return jsonify({
                'exists': False,
                'registered': False
            }), 200
        
        user = user_result.data[0]
        
        return jsonify({
            'exists': True,
            'registered': True,
            'user_id': user['id'],
            'full_name': user.get('full_name'),
            'email': user.get('email')
        }), 200

    except Exception as e:
        logger.error(f"[ERROR] Check user error: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Failed to check user status'}), 500


# ============================================================
# IMAGE GENERATION ROUTE - UPDATED WITH IMAGEN 3 SUPPORT
# ============================================================

@app.route('/api/generate-design', methods=['POST', 'OPTIONS'])
@timeout_decorator(180)
def generate_design():
    """OPTIMIZED: Generate interior design in under 10 seconds"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Extract parameters
        room_type = data.get('room_type')
        client_name = data.get('client_name', 'skyline')
        style = data.get('style')
        custom_prompt = data.get('custom_prompt', '').strip()
        width = data.get('width', 1024)
        height = data.get('height', 1024)
        logger.info(f"="*70)
        logger.info(f"[REQUEST] Room: {room_type} | Style: {style} | Client: {client_name}")
        logger.info(f"="*70)

        # Validate client
        VALID_CLIENTS = ['skyline', 'ellington']
        if client_name not in VALID_CLIENTS:
            return jsonify({'error': f'Invalid client. Must be one of: {VALID_CLIENTS}'}), 400

        # Validate inputs
        is_valid, message = validate_inputs(room_type, style, custom_prompt)
        if not is_valid:
            return jsonify({'error': message}), 400

        # ✅ FIX #1: CHECK CACHE FIRST (BEFORE GENERATION)
        is_custom_theme = bool(custom_prompt)
        cache_prompt = custom_prompt if is_custom_theme else f"{room_type}_{style}"
        
        cached_result = get_cached_image(cache_prompt, client_name)
        if cached_result:
            logger.info(f"[CACHE HIT] ⚡ Returning cached result instantly!")
            return jsonify({
                'success': True,
                'cached': True,
                'images': [cached_result],
                'generation_time': '0.1s'
            }), 200

        # Load reference image
        logger.info(f"[STEP 1/3] Loading reference image...")
        reference_image = load_reference_image(room_type, client_name)
        
        if not reference_image:
            return jsonify({
                'error': f'Reference image not found for {room_type}',
                'details': 'Reference image required'
            }), 500

        # Build prompt
        logger.info(f"[STEP 2/3] Building prompt...")
        prompt_data = construct_prompt(room_type, style, custom_prompt)
        if not prompt_data.get('success', True):
            return jsonify({'error': prompt_data.get('error', 'Prompt failed')}), 400
        
        prompt = prompt_data['prompt']
        prompt = optimize_prompt_for_gpt_image1(prompt, room_type)

        # ✅ FIX #2: GENERATE IMAGE (FAST - 7-8 SECONDS)
        logger.info(f"[STEP 3/3] Generating with Replicate...")
        start_time = time.time()
        
        if is_custom_theme:
            result = generate_with_openai_custom_theme(prompt, reference_image,width,height)
        else:
            result = generate_with_openai_style_based(prompt, room_type, reference_image,width,height)

        if not result or not result.get('success'):
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            logger.error(f"[GENERATION FAILED] {error_msg}")
            return jsonify({
                'error': 'Generation failed',
                'details': error_msg
            }), 500
        
        generation_time = time.time() - start_time
        logger.info(f"[SUCCESS] ✨ Generated in {generation_time:.2f}s")

        # ✅ FIX #3: PREPARE RESPONSE IMMEDIATELY (NO BLOCKING)
        image_base64 = result['image_base64']
        
        # Generate response
        response_data = {
            'id': int(time.time()),
            'image_base64': image_base64,  # Keep for backward compatibility
            'client_name': client_name,
            'room_type': room_type,
            'style': style if not is_custom_theme else 'custom',
            'custom_theme': custom_prompt if is_custom_theme else None,
            'model_used': 'adirik/interior-design',
            'generation_method': result.get('method'),
            'resolution': f"{width}x{height}",
            'generation_time': f"{generation_time:.2f}s"
        }

        # ✅ FIX #4: CACHE THE RESULT
        save_to_cache(cache_prompt, response_data, client_name)

        # ✅ FIX #5: DO CLOUDINARY + DATABASE IN BACKGROUND (NON-BLOCKING)
        def background_upload():
            """Upload to Cloudinary and save to DB in background"""
            try:
                # Upload to Cloudinary
                cloudinary_url = upload_to_cloudinary(image_base64, client_name, room_type)
                
                if cloudinary_url:
                    logger.info(f"[BACKGROUND] ✅ Uploaded to Cloudinary: {cloudinary_url}")
                    
                    # ✅ GET user_id and session_id from request data
                    request_user_id = data.get('user_id')
                    request_session_id = data.get('session_id')
                    
                    # Save to database
                    save_generation_to_db(
                        client_name=client_name,
                        room_type=room_type,
                        style=style if not is_custom_theme else 'custom',
                        custom_prompt=custom_prompt if is_custom_theme else None,
                        generated_image_url=cloudinary_url,
                        user_id=request_user_id,      # ✅ CHANGED
                        session_id=request_session_id  # ✅ NEW
                    )
                    logger.info(f"[BACKGROUND] ✅ Saved to database")
                else:
                    logger.error(f"[BACKGROUND] ❌ Cloudinary upload failed")
                        
            except Exception as e:
                logger.error(f"[BACKGROUND] ❌ Error: {e}")

        # Start background thread
        upload_thread = threading.Thread(target=background_upload, daemon=True)
        upload_thread.start()
        logger.info(f"[BACKGROUND] 🚀 Upload thread started (non-blocking)")

        # ✅ RETURN IMMEDIATELY - DON'T WAIT FOR UPLOADS
        logger.info(f"="*70)
        logger.info(f"[RESPONSE] ⚡ Returning to client after {generation_time:.2f}s")
        logger.info(f"="*70)

        return jsonify({
            'success': True,
            'cached': False,
            'images': [response_data],
            'prompt_used': prompt[:300] + '...',
            'generation_details': {
                'model': 'adirik/interior-design',
                'generation_time': f"{generation_time:.2f}s"
            }
        }), 200

    except Exception as e:
        logger.error(f"="*70)
        logger.error(f"[FATAL ERROR] {str(e)}")
        logger.error(f"="*70)
        traceback.print_exc()
        return jsonify({
            'error': 'Internal server error',
            'details': str(e)
        }), 500


# ============================================================
# SESSION MANAGEMENT
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
            logger.info(f"[SUCCESS] New session created: {session_id}")
        else:
            supabase.table('sessions').update({
                'last_activity': datetime.now().isoformat(),
                'status': 'active'
            }).eq('session_id', session_id).execute()
            logger.info(f"[SUCCESS] Session updated: {session_id}")
        
        return jsonify({
            'success': True,
            'session_id': session_id
        }), 200

    except Exception as e:
        logger.error(f"[ERROR] Create session error: {e}")
        return jsonify({'error': 'Session creation failed'}), 500
@app.route('/api/check-session', methods=['POST', 'OPTIONS'])
def check_session():
    """Check session generation count - server-side tracking"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or not supabase:
            return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
        # Get or create session
        session_result = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
        if not session_result.data:
            # Create new session
            session_data = {
                'session_id': session_id,
                'generation_count': 0,
                'is_registered': False,
                'ip_address': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', ''),
                'status': 'active'
            }
            supabase.table('sessions').insert(session_data).execute()
            
            return jsonify({
                'success': True,
                'generation_count': 0,
                'is_registered': False
            }), 200
        
        session = session_result.data[0]
        
        return jsonify({
            'success': True,
            'generation_count': session.get('generation_count', 0),
            'is_registered': session.get('is_registered', False),
            'user_id': session.get('user_id'),
            'email': None
        }), 200

    except Exception as e:
        logger.error(f"[ERROR] Check session error: {e}")
        return jsonify({'success': False, 'error': 'Failed to check session'}), 500


@app.route('/api/increment-generation', methods=['POST', 'OPTIONS'])
def increment_generation():
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or not supabase:
            return jsonify({'success': False}), 400
        
        session_result = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
        if session_result.data:
            current_count = session_result.data[0].get('generation_count', 0)
            new_count = current_count + 1
            
            # ✅ Update count (keep this synchronous)
            supabase.table('sessions').update({
                'generation_count': new_count,
                'last_activity': datetime.now().isoformat()
            }).eq('session_id', session_id).execute()
            
            # ✅ MOVE THIS TO BACKGROUND THREAD
            def log_generation_async():
                try:
                    log_data = {
                        'session_id': session_id,
                        'user_id': session_result.data[0].get('user_id'),
                        'client_name': data.get('client_name', 'skyline'),
                        'room_type': data.get('room_type'),
                        'style': data.get('style'),
                        'custom_prompt': data.get('custom_prompt'),
                        'generation_number': new_count,
                        'was_registered': session_result.data[0].get('is_registered', False),
                        'ip_address': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent', '')
                    }
                    supabase.table('generation_logs').insert(log_data).execute()
                    logger.info(f"[BACKGROUND] ✅ Logged generation #{new_count}")
                except Exception as e:
                    logger.error(f"[BACKGROUND] ❌ Log error: {e}")
            
            # Start background thread
            threading.Thread(target=log_generation_async, daemon=True).start()
            
            # ✅ RETURN IMMEDIATELY
            return jsonify({
                'success': True,
                'generation_count': new_count
            }), 200
        
        return jsonify({'success': False}), 400

    except Exception as e:
        logger.error(f"[ERROR] Increment generation error: {e}")
        return jsonify({'success': False}), 500

# ============================================================
# CACHE MANAGEMENT
# ============================================================

# ============================================================
# CACHE MANAGEMENT
# ============================================================

@app.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached images"""
    cache_count = len(image_cache)
    image_cache.clear()
    logger.info(f"[CLEANUP] Manually cleared {cache_count} cache entries")
    return jsonify({
        'success': True,
        'message': f'Cleared {cache_count} cached images'
    }), 200

# ============================================================
# DEBUG ENDPOINTS - Add after /api/cache/clear
# ============================================================

@app.route('/api/scheduler-status', methods=['GET'])
def scheduler_status():
    """Check if scheduler is running"""
    try:
        if not app_scheduler:
            return jsonify({
                'running': False,
                'error': 'Scheduler not initialized'
            }), 500
        
        is_running = app_scheduler.running
        jobs = app_scheduler.get_jobs()
        
        return jsonify({
            'running': is_running,
            'jobs_count': len(jobs),
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run': str(job.next_run_time) if job.next_run_time else None
                }
                for job in jobs
            ]
        }), 200
    except Exception as e:
        return jsonify({
            'running': False,
            'error': str(e)
        }), 500


@app.route('/api/pending-notifications', methods=['GET'])
def get_pending_notifications():
    """Check pending notifications in database"""
    try:
        if not supabase:
            return jsonify({'error': 'Supabase not configured'}), 500
        
        result = supabase.table('scheduled_notifications')\
            .select('*')\
            .eq('status', 'pending')\
            .order('scheduled_for')\
            .execute()
        
        notifications = result.data if result.data else []
        
        return jsonify({
            'count': len(notifications),
            'notifications': [
                {
                    'id': n['id'],
                    'user_id': n['user_id'],
                    'phone': n['phone_number'],
                    'scheduled_for': n['scheduled_for'],
                    'status': n['status']
                }
                for n in notifications
            ]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/test-whatsapp-direct', methods=['POST'])
def test_whatsapp_direct():
    """Direct test - send WhatsApp/SMS to your phone NOW"""
    try:
        data = request.get_json()
        phone = data.get('phone_number')
        
        if not phone:
            return jsonify({'error': 'phone_number required'}), 400
        
        from whatsapp_service import send_whatsapp_message, send_sms_message
 
        message = f"🎨 Test from AI Interior Design!\n\nYour Twilio is working!\nPhone: {phone}\nTime: {datetime.now().strftime('%I:%M %p')}"
        
        # Try WhatsApp first
        result = send_whatsapp_message(phone, message, 'IN')
        
        if not result.get('success'):
            # Try SMS if WhatsApp fails
            result = send_sms_message(phone, message, 'IN')
        
        return jsonify(result), 200 if result.get('success') else 500
        
    except Exception as e:
        logger.error(f"[TEST] Error: {e}")
        return jsonify({'error': str(e)}), 500
# ============================================================
# TEST ENDPOINT - For debugging WhatsApp (REMOVE IN PRODUCTION)
# ============================================================

@app.route('/api/test-whatsapp/<user_id>', methods=['POST'])
def test_whatsapp_notification(user_id):
    """
    TEST ONLY: Send WhatsApp/SMS immediately without waiting
    Usage: POST http://localhost:5000/api/test-whatsapp/USER_UUID_HERE
    """
    if not supabase:
        return jsonify({'error': 'Supabase not configured'}), 500
    
    result = send_notification_to_user(user_id, supabase)
    
    return jsonify(result), 200 if result.get('success') else 500


# ============================================================
# SCHEDULER INITIALIZATION
# ============================================================
if __name__ == '__main__':
    
    
    # ✅ STEP 2: Initialize scheduler
    if supabase:
        app_scheduler = init_scheduler(supabase)
        start_scheduler()
        logger.info("[SETUP] ✅ Scheduler initialized AND STARTED")
    else:
        logger.warning("[SETUP] ⚠️ Supabase not configured - scheduler disabled")
        app_scheduler = None
    
    # ✅ STEP 3: Start server
    port = int(os.getenv('PORT', 5000))
    
    logger.info("="*70)
    logger.info("🚀 Starting AI Interior Design Backend v10.0.0")
    logger.info("="*70)
    logger.info(f"Port: {port}")
    logger.info(f"OpenAI: {'✓' if OPENAI_API_KEY else '✗'}")
    logger.info(f"Replicate: {'✓' if REPLICATE_API_TOKEN else '✗'}")
    logger.info(f"Email: {'✓' if EMAIL_USER and EMAIL_PASSWORD else '✗'}")
    logger.info(f"Supabase: {'✓' if supabase else '✗'}")
    logger.info(f"Scenario Module: ✓")
    logger.info("="*70)
    
    # ✅ Set debug=True for development (shows errors)
    app.run(host='0.0.0.0', port=port, debug=True)
    
# # Standard library imports first
# import os
# import sys
# import io
# import base64
# import time
# import hashlib
# import logging
# import traceback
# import tempfile
# import secrets
# import smtplib
# import threading
# from functools import wraps
# from datetime import datetime, timedelta, timezone
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# # Third-party imports
# from dotenv import load_dotenv
# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from openai import OpenAI
# from supabase import create_client, Client
# from PIL import Image
# from pymongo import MongoClient
# import cloudinary
# import cloudinary.uploader
# import cloudinary.api
# import requests

# # Load environment variables
# load_dotenv()

# # ============================================================
# # LOGGING SETUP - MUST BE FIRST!
# # ============================================================
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.StreamHandler(sys.stdout)
#     ]
# )
# logger = logging.getLogger(__name__)

# # ============================================================
# # IMPORT PROJECT MODULES - AFTER LOGGER
# # ============================================================
# from config import (
#     INTERIOR_STYLES,
#     FIXED_ROOM_LAYOUTS,
#     ROOM_DESCRIPTIONS, 
#     ROOM_IMAGES,
#     THEME_ELEMENTS
# )
# from prompts import (
#     construct_prompt,
#     construct_fixed_layout_prompt,
#     construct_custom_theme_prompt,
#     validate_inputs, 
#     deconstruct_theme_to_realistic_elements,
#     get_short_prompt_for_cache
# )

# # ============================================================
# # API CONFIGURATION - AFTER LOGGER
# # ============================================================





# # ============================================================
# # CONFIGURATION
# # ============================================================

# # API Keys
# # Initialize Replicate client
# # Set your API key as environment variable: export REPLICATE_API_TOKEN="your_token"
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")



# # Replicate API Token (for interior design model)
# if REPLICATE_API_TOKEN:
#     logger.info("[SETUP] Replicate API configured successfully")
# else:
#     logger.warning("[SETUP] REPLICATE_API_TOKEN not set - Image generation will not work")

# # Supabase
# # Supabase
# SUPABASE_URL = os.getenv("SUPABASE_URL")
# SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
# MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
# mongo_client = MongoClient(MONGO_URI)
# db = mongo_client["interior_design"]
# # Email
# EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
# EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
# EMAIL_USER = os.getenv("EMAIL_USER")
# EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
# EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)




# # Frontend URL
# FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5177/")

# # Cache Settings
# CACHE_DURATION = 1800  # 30 minutes
# image_cache = {}

# # Cloudinary Setup
# cloudinary.config(
#     cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME"),
#     api_key = os.getenv("CLOUDINARY_API_KEY"),
#     api_secret = os.getenv("CLOUDINARY_API_SECRET")
# )
# # ============================================================
# # FLASK APP INITIALIZATION
# # ============================================================
# app = Flask(__name__)

# CORS(app, resources={
#     r"/*": {
#         "origins": "*",
#         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#         "allow_headers": ["Content-Type", "Authorization"],
#         "supports_credentials": False,
#         "max_age": 3600
#     }
# })

# # Force headers on every response
# @app.after_request
# def apply_cors(response):
#     response.headers["Access-Control-Allow-Origin"] = "*"
#     response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
#     response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
#     return response

# # OpenAI client (not needed anymore since we use FLUX)
# openai_client = None

# # ============================================================
# # UTILITY FUNCTIONS
# # ============================================================

# def timeout_decorator(seconds=120):
#     """Decorator to add timeout to routes"""
#     def decorator(func):
#         @wraps(func)
#         def wrapper(*args, **kwargs):
#             start_time = time.time()
#             try:
#                 result = func(*args, **kwargs)
#                 elapsed = time.time() - start_time
#                 if elapsed > seconds:
#                     logger.warning(f"Request took {elapsed:.2f}s (exceeded {seconds}s timeout)")
#                 return result
#             except Exception as e:
#                 elapsed = time.time() - start_time
#                 logger.error(f"Request failed after {elapsed:.2f}s: {str(e)}")
#                 raise
#         return wrapper
#     return decorator


# def get_cached_image(prompt, client_name='default'):
#     """Check if we have a cached image for this prompt + client combo"""
#     cache_key = hashlib.md5(f"{client_name}:{prompt}".encode()).hexdigest()
#     if cache_key in image_cache:
#         cached_data, timestamp = image_cache[cache_key]
#         if time.time() - timestamp < CACHE_DURATION:
#             logger.info(f"[SUCCESS] Cache HIT for client={client_name}, prompt: {prompt[:50]}...")
#             return cached_data
#         else:
#             del image_cache[cache_key]
#             logger.info(f"[INFO] Cache EXPIRED for client={client_name}, prompt: {prompt[:50]}...")
#     logger.info(f"[INFO] Cache MISS for client={client_name}, prompt: {prompt[:50]}...")
#     return None


# def save_to_cache(prompt, image_data, client_name='default'):
#     """Save generated image to cache with client context"""
#     cache_key = hashlib.md5(f"{client_name}:{prompt}".encode()).hexdigest()
#     image_cache[cache_key] = (image_data, time.time())
#     logger.info(f"[CACHE] Cached image for client={client_name}: {prompt[:50]}...")
# def save_generation_to_db(client_name, room_type, style, custom_prompt, generated_image_url, user_id=None):
#     """Save generation to MongoDB for tracking"""
#     try:
#         generation_record = {
#             "client_name": client_name,
#             "room_type": room_type,
#             "style": style,
#             "custom_prompt": custom_prompt,
#             "generated_image_url": generated_image_url,
#             "user_id": user_id,
#             "generated_at": datetime.now(),
#             "downloaded": False,
#             "download_count": 0
#         }
        
#         result = db.generated_images.insert_one(generation_record)
#         logger.info(f"[DB] Saved generation to MongoDB: {result.inserted_id}")
        
#         # Update client stats
#         db.clients.update_one(
#             {"client_name": client_name},
#             {
#                 "$inc": {"total_generations": 1},
#                 "$setOnInsert": {
#                     "created_at": datetime.now(),
#                     "total_downloads": 0
#                 }
#             },
#             upsert=True
#         )
        
#         return str(result.inserted_id)
        
#     except Exception as e:
#         logger.error(f"[DB ERROR] Failed to save to MongoDB: {e}")
#         return None
    
# def upload_to_cloudinary(image_base64, client_name, room_type):
#     """Upload generated image to Cloudinary"""
#     try:
#         upload_result = cloudinary.uploader.upload(
#             f"data:image/png;base64,{image_base64}",
#             folder=f"generated/{client_name}",
#             public_id=f"{room_type}_{int(time.time())}",
#             resource_type="image"
#         )
        
#         image_url = upload_result['secure_url']
#         logger.info(f"[CLOUDINARY] Uploaded image: {image_url}")
#         return image_url
        
#     except Exception as e:
#         logger.error(f"[CLOUDINARY ERROR] Upload failed: {e}")
#         return None
    
# def clean_expired_cache():
#     """Remove expired entries from cache"""
#     current_time = time.time()
#     expired_keys = [
#         key for key, (_, timestamp) in image_cache.items()
#         if current_time - timestamp >= CACHE_DURATION
#     ]
#     for key in expired_keys:
#         del image_cache[key]
#     if expired_keys:
#         logger.info(f"[CLEANUP] Cleaned {len(expired_keys)} expired cache entries")


# def optimize_prompt_for_gpt_image1(prompt, room_type):
#     """Pre-process prompt for GPT Image 1"""
#     replacements = {
#         "⚠️": "", "✅": "", "❌": "", "🔒": "", "🏗️": "", 
#         "🪑": "", "🎨": "", "📸": "", "🚫": "", "━": ""
#     }
#     for old, new in replacements.items():
#         prompt = prompt.replace(old, new)
    
#     prompt = " ".join(prompt.split())
#     logger.info(f"[SUCCESS] Prompt optimized for GPT Image 1 (Length: {len(prompt)} chars)")
#     return prompt


# def load_reference_image(room_type, client_name='skyline'):
#     """Load and convert reference image to PNG format for OpenAI - WITH CLIENT SUPPORT"""
#     try:
#         # Build client-specific path
#         if client_name and client_name != 'default':
#             # Client-specific images
#             base_dir = os.path.dirname(os.path.abspath(__file__))
            
#             # Map room_type to actual filename based on client
#             if client_name == 'skyline':
#                 filename_map = {
#                     'master_bedroom': 'skyline_bedroom.webp',
#                     'living_room': 'skyline_living_room.webp',
#                     'kitchen': 'skyline_kitchen.webp'
#                 }
#             elif client_name == 'ellington':
#                 filename_map = {
#                     'master_bedroom': 'ellington_bedroom.webp',
#                     'living_room': 'ellington_living_room.webp',
#                     'kitchen': 'ellington_kitchen.webp'
#                 }
#             else:
#                 logger.error(f"Unknown client: {client_name}")
#                 return None
            
#             filename = filename_map.get(room_type)
#             if not filename:
#                 logger.error(f"No filename mapping for {room_type} in {client_name}")
#                 return None
            
#             image_path = os.path.join(base_dir, 'images', client_name, filename)
            
#             if not os.path.exists(image_path):
#                 logger.warning(f"Client image not found: {image_path}, falling back to default")
#                 # Fallback to default
#                 image_path = ROOM_IMAGES.get(room_type)
#         else:
#             # Default images (your current setup)
#             if room_type not in ROOM_IMAGES:
#                 logger.error(f"No reference image found for {room_type}")
#                 return None
#             image_path = ROOM_IMAGES[room_type]
        
#         if not os.path.exists(image_path):
#             logger.error(f"Reference image not found at path: {image_path}")
#             return None
        
#         logger.info(f"[INFO] Loading image from: {image_path} (Client: {client_name})")
        
#         img = Image.open(image_path)
        
#         # Convert RGBA to RGB if needed
#         if img.mode == 'RGBA':
#             background = Image.new('RGB', img.size, (255, 255, 255))
#             background.paste(img, mask=img.split()[3])
#             img = background
#         elif img.mode != 'RGB':
#             img = img.convert('RGB')
        
#         # Save as PNG to bytes
#         img_byte_arr = io.BytesIO()
#         img.save(img_byte_arr, format='PNG')
#         img_byte_arr.seek(0)
#         image_data = img_byte_arr.read()
        
#         # Convert to base64
#         image_base64 = base64.b64encode(image_data).decode('utf-8')
        
#         logger.info(f"[SUCCESS] Loaded reference image for {room_type} - {client_name} ({len(image_data)} bytes)")
#         return image_base64
        
#     except Exception as e:
#         logger.error(f"[ERROR] Error loading reference image: {e}")
#         traceback.print_exc()
#         return None





# # ============================================================
# # EMAIL & SMS FUNCTIONS
# # ============================================================

# def send_welcome_email(full_name, email):
#     """Send simple welcome email after registration"""
#     try:
#         if not EMAIL_USER or not EMAIL_PASSWORD:
#             logger.warning("[WARNING] Email not configured")
#             return False
        
#         msg = MIMEMultipart('alternative')
#         msg['Subject'] = '🎨 Welcome to AI Interior Design Generator!'
#         msg['From'] = EMAIL_FROM
#         msg['To'] = email
        
#         html = f"""
#         <html>
#           <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
#             <div style="background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%); padding: 30px; border-radius: 12px 12px 0 0; text-align: center;">
#               <h1 style="color: white; margin: 0; font-size: 28px;">🎨 Welcome {full_name}!</h1>
#             </div>
            
#             <div style="background: white; padding: 30px; border: 2px solid #e5e7eb; border-top: none; border-radius: 0 0 12px 12px;">
#               <p style="font-size: 18px; color: #111827; margin-top: 0;">
#                 Thank you for registering! 🎉
#               </p>
              
#               <p style="font-size: 16px; color: #374151;">
#                 You now have <strong style="color: #9333ea;">unlimited access</strong> to generate stunning AI-powered interior designs!
#               </p>
              
#               <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); padding: 20px; border-radius: 8px; margin: 25px 0; border-left: 4px solid #f59e0b;">
#                 <h3 style="margin-top: 0; color: #92400e; font-size: 18px;">✨ What You Can Do Now:</h3>
#                 <ul style="color: #78350f; margin: 10px 0; padding-left: 20px;">
#                   <li style="margin: 8px 0;">Generate unlimited interior designs</li>
#                   <li style="margin: 8px 0;">Choose from multiple styles (Modern, Scandinavian, Industrial & more)</li>
#                   <li style="margin: 8px 0;">Create custom themes with your imagination</li>
#                   <li style="margin: 8px 0;">Download all your designs in high quality</li>
#                 </ul>
#               </div>
              
#               <div style="text-align: center; margin: 30px 0;">
#                 <a href="{FRONTEND_URL}" style="display: inline-block; background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%); color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 16px; box-shadow: 0 4px 6px rgba(147, 51, 234, 0.3);">
#                   Start Creating Now →
#                 </a>
#               </div>
              
#               <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
#                 <strong>Your Details:</strong><br>
#                 Name: {full_name}<br>
#                 Email: {email}
#               </p>
              
#               <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
              
#               <p style="color: #9ca3af; font-size: 13px; text-align: center; margin-bottom: 0;">
#                 Need help? Reply to this email and we'll assist you.<br>
#                 Happy designing! 🏠✨
#               </p>
#             </div>
#           </body>
#         </html>
#         """
        
#         msg.attach(MIMEText(html, 'html'))
        
#         with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
#             server.starttls()
#             server.login(EMAIL_USER, EMAIL_PASSWORD)
#             server.send_message(msg)
        
#         logger.info(f"[SUCCESS] Welcome email sent to {email}")
#         return True
        
#     except Exception as e:
#         logger.error(f"[ERROR] Email error: {e}")
#         traceback.print_exc()
#         return False





# # ============================================================
# # AI IMAGE GENERATION - IMAGE-TO-IMAGE
# # ============================================================
# # ============================================================
# # AI IMAGE GENERATION - IMAGE-TO-IMAGE
# # ============================================================
# # ============================================================
# # GLOBAL CACHE FOR MODEL VERSION
# # ============================================================
# _cached_model_version = None
# _version_cache_time = None
# VERSION_CACHE_DURATION = 3600  # 1 hour

# def get_cached_model_version():
#     """Get model version with 1-hour caching - SAVES 1-2 SECONDS"""
#     global _cached_model_version, _version_cache_time
    
#     current_time = time.time()
    
#     # Return cached version if valid
#     if _cached_model_version and _version_cache_time:
#         if current_time - _version_cache_time < VERSION_CACHE_DURATION:
#             logger.info("[CACHE] Using cached model version ⚡")
#             return _cached_model_version
    
#     # Fetch new version
#     logger.info("[API] Fetching model version...")
#     try:
#         model_response = requests.get(
#             "https://api.replicate.com/v1/models/adirik/interior-design",
#             headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"},
#             timeout=10
#         )
        
#         if model_response.status_code != 200:
#             # If cache exists, use stale cache
#             if _cached_model_version:
#                 logger.warning("[CACHE] Using stale cache (fetch failed)")
#                 return _cached_model_version
#             raise Exception(f"Model fetch failed: {model_response.status_code}")
        
#         latest_version = model_response.json().get("latest_version", {}).get("id")
#         if not latest_version:
#             if _cached_model_version:
#                 return _cached_model_version
#             raise Exception("No model version found")
        
#         # Cache it
#         _cached_model_version = latest_version
#         _version_cache_time = current_time
        
#         logger.info(f"[CACHE] Cached version: {latest_version[:16]}... ✅")
#         return latest_version
        
#     except Exception as e:
#         if _cached_model_version:
#             logger.warning(f"[CACHE] Using stale cache: {e}")
#             return _cached_model_version
#         raise


# # ============================================================
# # SINGLE UNIFIED GENERATION FUNCTION (REPLACES ALL 3)
# # ============================================================
# def generate_interior_design_unified(
#     prompt, 
#     reference_image_base64,
#     room_type="living_room",
#     is_custom_theme=False
# ):
#     """
#     UNIFIED: Single function for both flows
    
#     FLOW 1: Style-based (is_custom_theme=False)
#     - Parameters: guidance_scale=10, prompt_strength=0.82, steps=28
    
#     FLOW 2: Custom theme (is_custom_theme=True)  
#     - Parameters: guidance_scale=10, prompt_strength=0.92, steps=32
    
#     Expected time: 7-8 seconds
#     """
#     try:
#         if not REPLICATE_API_TOKEN:
#             return {"success": False, "error": "REPLICATE_API_TOKEN not set"}
        
#         flow_name = "CUSTOM THEME" if is_custom_theme else "STYLE-BASED"
#         logger.info(f"[{flow_name}] Starting generation for {room_type}...")
#         start_time = time.time()
        
#         # Optimize prompt length
#         if len(prompt) > 800:
#             prompt = prompt[:800]
        
#         # Enhanced prompt based on flow
#         if is_custom_theme:
#             # FLOW 2: Custom theme - more dramatic
#             enhanced_prompt = (
#                 f"{prompt}, complete interior redesign, dramatic transformation, "
#                 f"professional architectural photography, luxury interior, "
#                 f"high-end design, modern aesthetic, natural lighting, 8k ultra detailed"
#             )
#         else:
#             # FLOW 1: Style-based - balanced
#             enhanced_prompt = (
#                 f"{prompt}, {room_type} interior design, "
#                 f"professional architectural photography, modern luxury space, "
#                 f"high-end real estate photo, natural lighting, 8k quality"
#             )
        
#         # Get cached model version (SAVES 1-2 SECONDS)
#         latest_version = get_cached_model_version()
        
#         logger.info(f"[{flow_name}] Creating prediction...")
        
#         # Parameters optimized by flow
#         if is_custom_theme:
#             # FLOW 2: Custom - Higher transformation
#             guidance_scale = 10
#             prompt_strength = 0.92  # More dramatic change
#             num_inference_steps = 32  # Slightly more for quality
#         else:
#             # FLOW 1: Style - Balanced
#             guidance_scale = 10
#             prompt_strength = 0.82  # Moderate change
#             num_inference_steps = 28  # Faster
        
#         # Create prediction
#         prediction_response = requests.post(
#             "https://api.replicate.com/v1/predictions",
#             headers={
#                 "Authorization": f"Token {REPLICATE_API_TOKEN}",
#                 "Content-Type": "application/json"
#             },
#             json={
#                 "version": latest_version,
#                 "input": {
#                     "image": f"data:image/png;base64,{reference_image_base64}",
#                     "prompt": enhanced_prompt,
#                     "negative_prompt": (
#                         "lowres, bad quality, watermark, text, logo, worst quality, "
#                         "low quality, blurry, pixelated, deformed, ugly" +
#                         (", boring, plain" if is_custom_theme else "")
#                     ),
#                     "guidance_scale": guidance_scale,
#                     "prompt_strength": prompt_strength,
#                     "num_inference_steps": num_inference_steps
#                 }
#             },
#             timeout=30
#         )
        
#         if prediction_response.status_code != 201:
#             return {"success": False, "error": prediction_response.text}
        
#         prediction_id = prediction_response.json().get("id")
#         logger.info(f"[{flow_name}] Polling (ID: {prediction_id[:12]}...)...")
        
#         # Fast polling - 0.5 second intervals
#         max_attempts = 200
#         attempt = 0
        
#         while attempt < max_attempts:
#             time.sleep(0.3)
            
#             status_response = requests.get(
#                 f"https://api.replicate.com/v1/predictions/{prediction_id}",
#                 headers={"Authorization": f"Token {REPLICATE_API_TOKEN}"},
#                 timeout=10
#             )
            
#             status_data = status_response.json()
#             status = status_data.get("status")
            
#             # Reduced logging - only every 10 attempts (~5 seconds)
#             if attempt % 20 == 0 and attempt > 0:
#                 elapsed = attempt * 0.3
#                 logger.info(f"[{flow_name}] {status} (~{elapsed:.1f}s)")
            
#             if status == "succeeded":
#                 output = status_data.get("output")
#                 if not output:
#                     return {"success": False, "error": "No output"}
                
#                 image_url = output[0] if isinstance(output, list) else output
#                 img_response = requests.get(image_url, timeout=30)
#                 image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                
#                 generation_time = time.time() - start_time
                
#                 logger.info(f"{'='*60}")
#                 logger.info(f"[SUCCESS] ⚡ {flow_name}: {generation_time:.2f}s")
#                 logger.info(f"{'='*60}")
                
#                 return {
#                     "success": True,
#                     "image_base64": image_base64,
#                     "model": "adirik/interior-design",
#                     "size": "1024x1024",
#                     "room_type": room_type,
#                     "method": f"unified_{'custom' if is_custom_theme else 'style'}",
#                     "generation_time": f"{generation_time:.2f}s",
#                     "flow": "FLOW 2" if is_custom_theme else "FLOW 1",
#                     "parameters": {
#                         "guidance_scale": guidance_scale,
#                         "prompt_strength": prompt_strength,
#                         "steps": num_inference_steps
#                     }
#                 }
            
#             elif status == "failed":
#                 error = status_data.get("error", "Unknown error")
#                 logger.error(f"[ERROR] {flow_name} failed: {error}")
#                 return {"success": False, "error": error}
            
#             attempt += 1
        
#         return {"success": False, "error": "Timeout after 75 seconds"}
        
#     except Exception as e:
#         logger.error(f"[ERROR] {flow_name}: {str(e)}")
#         traceback.print_exc()
#         return {"success": False, "error": str(e)}


# # ============================================================
# # WRAPPER FUNCTIONS (KEEP YOUR EXISTING API INTACT)
# # ============================================================

# def generate_with_gemini_flash_image(prompt, room_type, reference_image_base64):
#     """
#     WRAPPER: Maintains backward compatibility
#     Calls unified function with is_custom_theme=False
#     """
#     return generate_interior_design_unified(
#         prompt=prompt,
#         reference_image_base64=reference_image_base64,
#         room_type=room_type,
#         is_custom_theme=False
#     )


# def generate_with_openai_style_based(prompt, room_type, reference_image_base64):
#     """
#     FLOW 1 WRAPPER: Style-based generation
#     Calls unified function with is_custom_theme=False
#     """
#     return generate_interior_design_unified(
#         prompt=prompt,
#         reference_image_base64=reference_image_base64,
#         room_type=room_type,
#         is_custom_theme=False
#     )


# def generate_with_openai_custom_theme(prompt, reference_image_base64):
#     """
#     FLOW 2 WRAPPER: Custom theme generation
#     Calls unified function with is_custom_theme=True
#     """
#     return generate_interior_design_unified(
#         prompt=prompt,
#         reference_image_base64=reference_image_base64,
#         room_type="custom",  # Room type not critical for custom themes
#         is_custom_theme=True
#     )


# # ============================================================
# # BASIC ROUTES
# # ============================================================

# @app.route('/', methods=['GET'])
# def home():
#     return jsonify({
#         'status': 'healthy',
#         'message': 'AI Interior Design Backend - Imagen 3 Powered',
#         'version': '12.0.0',
#         'models': ['imagen-3'],
#         'features': ['ai-generation', 'email-verification', 'multi-client']
#     }), 200


# @app.route('/api/health', methods=['GET'])
# def health_check():
#     clean_expired_cache()
#     return jsonify({
#         'status': 'healthy',
#         'replicate_configured': bool(REPLICATE_API_TOKEN),
#         'email_configured': bool(EMAIL_USER and EMAIL_PASSWORD),
#         'supabase_configured': bool(supabase),
#         'cache_entries': len(image_cache),
#         'available_models': ['adirik/interior-design'] if REPLICATE_API_TOKEN else []
#     }), 200


# @app.route('/api/rooms', methods=['GET'])
# def get_rooms():
#     """Get available rooms with reference images"""
#     rooms = [
#         {
#             'id': room_id, 
#             'name': room_id.replace('_', ' ').title(),
#             'has_reference': room_id in ROOM_IMAGES
#         }
#         for room_id in FIXED_ROOM_LAYOUTS.keys()
#     ]
#     return jsonify(rooms), 200


# @app.route('/api/styles', methods=['GET'])
# def get_styles():
#     """Get available interior styles"""
#     styles = [
#         {'id': key, 'name': key.replace('_', ' ').title()}
#         for key in INTERIOR_STYLES.keys()
#     ]
#     return jsonify(styles), 200


# # ============================================================
# # REGISTRATION & OTP ENDPOINTS (unchanged)
# # ============================================================

# @app.route('/api/simple-register', methods=['POST', 'OPTIONS'])
# def simple_register():
#     """Simple registration - NO OTP, NO duplicate checks - ALLOW EVERYTHING"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
        
#         full_name = data.get('full_name', '').strip()
#         email = data.get('email', '').strip().lower()
#         phone_number = data.get('phone_number', '').strip()
#         country_code = data.get('country_code', 'IN')
#         session_id = data.get('session_id')
#         generated_count = data.get('generated_count', 0)
        
#         logger.info(f"[SIMPLE_REGISTER] New registration - Email: {email}, Phone: {phone_number}")
        
#         # Validation - ALL fields required
#         if not full_name or not email or not phone_number:
#             return jsonify({'error': 'All fields are required'}), 400
        
#         if len(phone_number) < 10:
#             return jsonify({'error': 'Phone number must be at least 10 digits'}), 400
        
#         if '@' not in email or '.' not in email:
#             return jsonify({'error': 'Invalid email address'}), 400
        
#         if not supabase:
#             return jsonify({'error': 'Database not configured'}), 500
        
#         # ✅ NO DUPLICATE CHECKS - Allow all registrations (even duplicates)
#         logger.info(f"[SIMPLE_REGISTER] Creating new user (duplicates allowed): {email}, {phone_number}")
        
#         # Create new user - NO checks, always insert
#         user_data = {
#             'full_name': full_name,
#             'email': email,
#             'phone_number': phone_number,
#             'country_code': country_code,
#             'pre_registration_generations': generated_count,
#             'total_generations': 0,
#             'ip_address': request.remote_addr,
#             'user_agent': request.headers.get('User-Agent', '')
#         }
        
#         new_user = supabase.table('users').insert(user_data).execute()
        
#         if not new_user.data:
#             return jsonify({'error': 'Failed to create user'}), 500
        
#         user_id = new_user.data[0]['id']
#         logger.info(f"[SIMPLE_REGISTER] New user created: {email} (ID: {user_id})")
        
#         # Update session
#         if session_id:
#             try:
#                 supabase.table('sessions').update({
#                     'user_id': user_id,
#                     'is_registered': True,
#                     'generation_count': 0
#                 }).eq('session_id', session_id).execute()
#             except Exception as e:
#                 logger.warning(f"[SIMPLE_REGISTER] Session update failed: {e}")
        
#         # ✅ Send welcome email in background thread (non-blocking)
#         def send_email_async():
#             try:
#                 send_welcome_email(full_name, email)
#                 logger.info(f"[SIMPLE_REGISTER] Welcome email sent to {email}")
#             except Exception as e:
#                 logger.warning(f"[SIMPLE_REGISTER] Failed to send welcome email: {e}")
        
#         # Start email thread in background
#         email_thread = threading.Thread(target=send_email_async, daemon=True)
#         email_thread.start()
#         logger.info(f"[SIMPLE_REGISTER] Email queued for background sending")
        
#         logger.info(f"[SIMPLE_REGISTER] Registration complete for {email}")
        
#         return jsonify({
#             'success': True,
#             'message': 'Registration successful! You now have unlimited access.',
#             'user_id': user_id,
#             'email': email,
#             'phone_number': phone_number
#         }), 200

#     except Exception as e:
#         logger.error(f"[SIMPLE_REGISTER] Error: {e}")
#         traceback.print_exc()
#         return jsonify({'error': 'Registration failed', 'details': str(e)}), 500


# @app.route('/api/check-user', methods=['POST', 'OPTIONS'])
# def check_user_status():
#     """Check if user is registered (simplified - no verification needed)"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         phone_number = data.get('phone_number', '').strip()
        
#         if not phone_number:
#             return jsonify({'error': 'Phone number required'}), 400
        
#         if not supabase:
#             return jsonify({'error': 'Database not configured'}), 500
        
#         # Find user by phone
#         user_result = supabase.table('users').select('*').eq('phone_number', phone_number).execute()
        
#         if not user_result.data:
#             return jsonify({
#                 'exists': False,
#                 'registered': False
#             }), 200
        
#         user = user_result.data[0]
        
#         return jsonify({
#             'exists': True,
#             'registered': True,
#             'user_id': user['id'],
#             'full_name': user.get('full_name'),
#             'email': user.get('email')
#         }), 200

#     except Exception as e:
#         logger.error(f"[ERROR] Check user error: {e}")
#         traceback.print_exc()
#         return jsonify({'error': 'Failed to check user status'}), 500


# # ============================================================
# # IMAGE GENERATION ROUTE - UPDATED WITH IMAGEN 3 SUPPORT
# # ============================================================

# @app.route('/api/generate-design', methods=['POST', 'OPTIONS'])
# @timeout_decorator(180)
# def generate_design():
#     """OPTIMIZED: Generate interior design in under 10 seconds"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400

#         # Extract parameters
#         room_type = data.get('room_type')
#         client_name = data.get('client_name', 'skyline')
#         style = data.get('style')
#         custom_prompt = data.get('custom_prompt', '').strip()
        
#         logger.info(f"="*70)
#         logger.info(f"[REQUEST] Room: {room_type} | Style: {style} | Client: {client_name}")
#         logger.info(f"="*70)

#         # Validate client
#         VALID_CLIENTS = ['skyline', 'ellington']
#         if client_name not in VALID_CLIENTS:
#             return jsonify({'error': f'Invalid client. Must be one of: {VALID_CLIENTS}'}), 400

#         # Validate inputs
#         is_valid, message = validate_inputs(room_type, style, custom_prompt)
#         if not is_valid:
#             return jsonify({'error': message}), 400

#         # ✅ FIX #1: CHECK CACHE FIRST (BEFORE GENERATION)
#         is_custom_theme = bool(custom_prompt)
#         cache_prompt = custom_prompt if is_custom_theme else f"{room_type}_{style}"
        
#         cached_result = get_cached_image(cache_prompt, client_name)
#         if cached_result:
#             logger.info(f"[CACHE HIT] ⚡ Returning cached result instantly!")
#             return jsonify({
#                 'success': True,
#                 'cached': True,
#                 'images': [cached_result],
#                 'generation_time': '0.1s'
#             }), 200

#         # Load reference image
#         logger.info(f"[STEP 1/3] Loading reference image...")
#         reference_image = load_reference_image(room_type, client_name)
        
#         if not reference_image:
#             return jsonify({
#                 'error': f'Reference image not found for {room_type}',
#                 'details': 'Reference image required'
#             }), 500

#         # Build prompt
#         logger.info(f"[STEP 2/3] Building prompt...")
#         prompt_data = construct_prompt(room_type, style, custom_prompt)
#         if not prompt_data.get('success', True):
#             return jsonify({'error': prompt_data.get('error', 'Prompt failed')}), 400
        
#         prompt = prompt_data['prompt']
#         prompt = optimize_prompt_for_gpt_image1(prompt, room_type)

#         # ✅ FIX #2: GENERATE IMAGE (FAST - 7-8 SECONDS)
#         logger.info(f"[STEP 3/3] Generating with Replicate...")
#         start_time = time.time()
        
#         if is_custom_theme:
#             result = generate_with_openai_custom_theme(prompt, reference_image)
#         else:
#             result = generate_with_openai_style_based(prompt, room_type, reference_image)

#         if not result or not result.get('success'):
#             error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
#             logger.error(f"[GENERATION FAILED] {error_msg}")
#             return jsonify({
#                 'error': 'Generation failed',
#                 'details': error_msg
#             }), 500
        
#         generation_time = time.time() - start_time
#         logger.info(f"[SUCCESS] ✨ Generated in {generation_time:.2f}s")

#         # ✅ FIX #3: PREPARE RESPONSE IMMEDIATELY (NO BLOCKING)
#         image_base64 = result['image_base64']
        
#         # Generate response
#         response_data = {
#             'id': int(time.time()),
#             'image_base64': image_base64,  # Keep for backward compatibility
#             'client_name': client_name,
#             'room_type': room_type,
#             'style': style if not is_custom_theme else 'custom',
#             'custom_theme': custom_prompt if is_custom_theme else None,
#             'model_used': 'adirik/interior-design',
#             'generation_method': result.get('method'),
#             'resolution': result.get('size', '1024x1024'),
#             'generation_time': f"{generation_time:.2f}s"
#         }

#         # ✅ FIX #4: CACHE THE RESULT
#         save_to_cache(cache_prompt, response_data, client_name)

#         # ✅ FIX #5: DO CLOUDINARY + DATABASE IN BACKGROUND (NON-BLOCKING)
#         def background_upload():
#             """Upload to Cloudinary and save to DB in background"""
#             try:
#                 # Upload to Cloudinary
#                 cloudinary_url = upload_to_cloudinary(image_base64, client_name, room_type)
                
#                 if cloudinary_url:
#                     logger.info(f"[BACKGROUND] ✅ Uploaded to Cloudinary: {cloudinary_url}")
                    
#                     # Save to database
#                     save_generation_to_db(
#                         client_name=client_name,
#                         room_type=room_type,
#                         style=style if not is_custom_theme else 'custom',
#                         custom_prompt=custom_prompt if is_custom_theme else None,
#                         generated_image_url=cloudinary_url,
#                         user_id=None
#                     )
#                     logger.info(f"[BACKGROUND] ✅ Saved to database")
#                 else:
#                     logger.error(f"[BACKGROUND] ❌ Cloudinary upload failed")
                    
#             except Exception as e:
#                 logger.error(f"[BACKGROUND] ❌ Error: {e}")

#         # Start background thread
#         upload_thread = threading.Thread(target=background_upload, daemon=True)
#         upload_thread.start()
#         logger.info(f"[BACKGROUND] 🚀 Upload thread started (non-blocking)")

#         # ✅ RETURN IMMEDIATELY - DON'T WAIT FOR UPLOADS
#         logger.info(f"="*70)
#         logger.info(f"[RESPONSE] ⚡ Returning to client after {generation_time:.2f}s")
#         logger.info(f"="*70)

#         return jsonify({
#             'success': True,
#             'cached': False,
#             'images': [response_data],
#             'prompt_used': prompt[:300] + '...',
#             'generation_details': {
#                 'model': 'adirik/interior-design',
#                 'generation_time': f"{generation_time:.2f}s"
#             }
#         }), 200

#     except Exception as e:
#         logger.error(f"="*70)
#         logger.error(f"[FATAL ERROR] {str(e)}")
#         logger.error(f"="*70)
#         traceback.print_exc()
#         return jsonify({
#             'error': 'Internal server error',
#             'details': str(e)
#         }), 500


# # ============================================================
# # SESSION MANAGEMENT
# # ============================================================

# @app.route('/api/create-session', methods=['POST', 'OPTIONS'])
# def create_session():
#     """Create or update user session"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         session_id = data.get('session_id')
#         user_id = data.get('user_id')
#         ip_address = request.remote_addr
#         user_agent = request.headers.get('User-Agent', '')
        
#         if not session_id or not supabase:
#             return jsonify({'error': 'Invalid request'}), 400
        
#         existing_session = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
#         if not existing_session.data:
#             session_data = {
#                 'session_id': session_id,
#                 'user_id': user_id,
#                 'generation_count': 0,
#                 'is_verified': False,
#                 'ip_address': ip_address,
#                 'user_agent': user_agent,
#                 'status': 'active'
#             }
#             supabase.table('sessions').insert(session_data).execute()
#             logger.info(f"[SUCCESS] New session created: {session_id}")
#         else:
#             supabase.table('sessions').update({
#                 'last_activity': datetime.now().isoformat(),
#                 'status': 'active'
#             }).eq('session_id', session_id).execute()
#             logger.info(f"[SUCCESS] Session updated: {session_id}")
        
#         return jsonify({
#             'success': True,
#             'session_id': session_id
#         }), 200

#     except Exception as e:
#         logger.error(f"[ERROR] Create session error: {e}")
#         return jsonify({'error': 'Session creation failed'}), 500
# @app.route('/api/check-session', methods=['POST', 'OPTIONS'])
# def check_session():
#     """Check session generation count - server-side tracking"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         session_id = data.get('session_id')
        
#         if not session_id or not supabase:
#             return jsonify({'success': False, 'error': 'Invalid request'}), 400
        
#         # Get or create session
#         session_result = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
#         if not session_result.data:
#             # Create new session
#             session_data = {
#                 'session_id': session_id,
#                 'generation_count': 0,
#                 'is_registered': False,
#                 'ip_address': request.remote_addr,
#                 'user_agent': request.headers.get('User-Agent', ''),
#                 'status': 'active'
#             }
#             supabase.table('sessions').insert(session_data).execute()
            
#             return jsonify({
#                 'success': True,
#                 'generation_count': 0,
#                 'is_registered': False
#             }), 200
        
#         session = session_result.data[0]
        
#         return jsonify({
#             'success': True,
#             'generation_count': session.get('generation_count', 0),
#             'is_registered': session.get('is_registered', False),
#             'user_id': session.get('user_id'),
#             'email': None
#         }), 200

#     except Exception as e:
#         logger.error(f"[ERROR] Check session error: {e}")
#         return jsonify({'success': False, 'error': 'Failed to check session'}), 500


# @app.route('/api/increment-generation', methods=['POST', 'OPTIONS'])
# def increment_generation():
#     """Increment generation count for session"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         session_id = data.get('session_id')
        
#         if not session_id or not supabase:
#             return jsonify({'success': False}), 400
        
#         # Update generation count
#         session_result = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
#         if session_result.data:
#             current_count = session_result.data[0].get('generation_count', 0)
#             new_count = current_count + 1
            
#             supabase.table('sessions').update({
#                 'generation_count': new_count,
#                 'last_activity': datetime.now().isoformat()
#             }).eq('session_id', session_id).execute()
            
#             # Log the generation
#             log_data = {
#                 'session_id': session_id,
#                 'user_id': session_result.data[0].get('user_id'),
#                 'client_name': data.get('client_name', 'skyline'),
#                 'room_type': data.get('room_type'),
#                 'style': data.get('style'),
#                 'custom_prompt': data.get('custom_prompt'),
#                 'generation_number': new_count,
#                 'was_registered': session_result.data[0].get('is_registered', False),
#                 'ip_address': request.remote_addr,
#                 'user_agent': request.headers.get('User-Agent', '')
#             }
#             supabase.table('generation_logs').insert(log_data).execute()
            
#             return jsonify({
#                 'success': True,
#                 'generation_count': new_count
#             }), 200
        
#         return jsonify({'success': False}), 400

#     except Exception as e:
#         logger.error(f"[ERROR] Increment generation error: {e}")
#         return jsonify({'success': False}), 500

# # ============================================================
# # CACHE MANAGEMENT
# # ============================================================

# @app.route('/api/cache/clear', methods=['POST'])
# def clear_cache():
#     """Clear all cached images"""
#     cache_count = len(image_cache)
#     image_cache.clear()
#     logger.info(f"[CLEANUP] Manually cleared {cache_count} cache entries")
#     return jsonify({
#         'success': True,
#         'message': f'Cleared {cache_count} cached images'
#     }), 200


# # ============================================================
# # MAIN
# # ============================================================

# if __name__ == '__main__':
#     port = int(os.getenv('PORT', 5000))
#     logger.info(f"Starting AI Interior Design Backend v10.0.0 on port {port}")
#     logger.info(f"OpenAI: {'✓' if OPENAI_API_KEY else '✗'}")
#     logger.info(f"Email: {'✓' if EMAIL_USER and EMAIL_PASSWORD else '✗'}")
#     logger.info(f"Supabase: {'✓' if supabase else '✗'}")
#     app.run(host='0.0.0.0', port=port, debug=False)  # ✅ Production ready