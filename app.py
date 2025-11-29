# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# import sys
# import requests
# import traceback
# import base64
# import time
# import hashlib
# import logging
# import tempfile
# import io
# import secrets
# from functools import wraps
# from openai import OpenAI
# from datetime import datetime, timedelta
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# from twilio.rest import Client as TwilioClient
# from supabase import create_client, Client
# from PIL import Image
# from pymongo import MongoClient
# import cloudinary
# import cloudinary.uploader
# import cloudinary.api
# from datetime import timezone
# import threading  # ✅ ADD THIS
# # Local imports
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
# # LOGGING SETUP
# # ============================================================
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('app.log', encoding='utf-8'),
#         logging.StreamHandler(sys.stdout)
#     ]
# )
# logger = logging.getLogger(__name__)


# # ============================================================
# # CONFIGURATION
# # ============================================================

# # API Keys
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

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

# # Twilio for Phone OTP
# TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
# TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
# twilio_client = TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) if TWILIO_ACCOUNT_SID else None

# # Frontend URL
# FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

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
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type"]
#     }
# })

# # Force headers on every response
# @app.after_request
# def apply_cors(response):
#     response.headers["Access-Control-Allow-Origin"] = "*"
#     response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
#     response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
#     return response

# openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


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


# def get_cached_image(prompt):
#     """Check if we have a cached image for this prompt"""
#     cache_key = hashlib.md5(prompt.encode()).hexdigest()
#     if cache_key in image_cache:
#         cached_data, timestamp = image_cache[cache_key]
#         if time.time() - timestamp < CACHE_DURATION:
#             logger.info(f"[SUCCESS] Cache HIT for prompt: {prompt[:50]}...")
#             return cached_data
#         else:
#             del image_cache[cache_key]
#             logger.info(f"[INFO] Cache EXPIRED for prompt: {prompt[:50]}...")
#     logger.info(f"[INFO] Cache MISS for prompt: {prompt[:50]}...")
#     return None


# def save_to_cache(prompt, image_data):
#     """Save generated image to cache"""
#     cache_key = hashlib.md5(prompt.encode()).hexdigest()
#     image_cache[cache_key] = (image_data, time.time())
#     logger.info(f"[CACHE] Cached image for prompt: {prompt[:50]}...")
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


# def generate_otp():
#     """Generate 6-digit OTP"""
#     return str(secrets.randbelow(900000) + 100000)


# # ============================================================
# # EMAIL & SMS FUNCTIONS
# # ============================================================

# def send_info_email(full_name, email):
#     """Send informational welcome email (NO verification link)"""
#     try:
#         if not EMAIL_USER or not EMAIL_PASSWORD:
#             logger.warning("[WARNING] Email not configured")
#             return False
        
#         msg = MIMEMultipart('alternative')
#         msg['Subject'] = 'Welcome to AI Interior Design! 🎨'
#         msg['From'] = EMAIL_FROM
#         msg['To'] = email
        
#         html = f"""
#         <html>
#           <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
#             <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
#               <h2 style="color: #9333ea;">Welcome {full_name}! 🎉</h2>
#               <p>Thank you for registering with AI Interior Design Generator!</p>
              
#               <div style="background: linear-gradient(135deg, #7c3aed 0%, #9333ea 100%); 
#                           padding: 20px; 
#                           border-radius: 12px; 
#                           color: white; 
#                           margin: 20px 0;">
#                 <h3 style="margin-top: 0;">Your Registration Details:</h3>
#                 <p style="margin: 5px 0;"><strong>Name:</strong> {full_name}</p>
#                 <p style="margin: 5px 0;"><strong>Email:</strong> {email}</p>
#                 <p style="margin: 5px 0;">✅ <strong>Status:</strong> Verify your phone to unlock unlimited designs!</p>
#               </div>
              
#               <div style="background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 20px 0;">
#                 <h4 style="margin-top: 0; color: #9333ea;">What's Next?</h4>
#                 <p>✨ Complete phone verification with the OTP sent to your mobile</p>
#                 <p>🎨 Unlock unlimited AI-generated interior designs</p>
#                 <p>💫 Save and download all your creations</p>
#               </div>
              
#               <p style="color: #666; font-size: 14px;">
#                 Need help? Reply to this email and we'll assist you.
#               </p>
              
#               <p style="color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #eee; padding-top: 20px;">
#                 This is an informational email. No action required via email.<br>
#                 Complete verification using the OTP sent to your phone.
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
        
#         logger.info(f"[SUCCESS] Info email sent to {email}")
#         return True
        
#     except Exception as e:
#         logger.error(f"[ERROR] Email error: {e}")
#         traceback.print_exc()
#         return False


# def send_phone_otp(phone_number, country_code, otp):
#     """Send OTP via Twilio SMS - ASYNC (non-blocking)"""
    
#     def send_sms_background():
#         """Background thread function"""
#         try:
#             if not twilio_client:
#                 logger.warning("[WARNING] Twilio not configured")
#                 return
            
#             country_dial_codes = {
#                 'IN': '+91', 'US': '+1', 'GB': '+44', 'CA': '+1', 'AU': '+61'
#             }
            
#             full_phone = f"{country_dial_codes.get(country_code, '+1')}{phone_number}"
            
#             # ✅ This happens in background thread
#             message = twilio_client.messages.create(
#                 body=f"Your Design Generator verification code is: {otp}. Valid for 10 minutes.",
#                 from_=TWILIO_PHONE_NUMBER,
#                 to=full_phone
#             )
            
#             logger.info(f"[SUCCESS] OTP sent to {full_phone} (SID: {message.sid})")
            
#         except Exception as e:
#             logger.error(f"[ERROR] SMS error: {e}")
    
#     # ✅ Start background thread
#     try:
#         thread = threading.Thread(target=send_sms_background)
#         thread.daemon = True  # Dies when main thread dies
#         thread.start()
        
#         logger.info(f"[SMS] OTP queued for {phone_number} (async)")
#         return True  # ✅ Return immediately without waiting
        
#     except Exception as e:
#         logger.error(f"[ERROR] Failed to start SMS thread: {e}")
#         return False


# # ============================================================
# # AI IMAGE GENERATION - IMAGE-TO-IMAGE
# # ============================================================

# def generate_with_openai_style_based(prompt, room_type, reference_image_base64):
#     """FLOW 1: OpenAI GPT Image 1 - Image-to-Image with Predefined Styles"""
#     temp_path = None
    
#     try:
#         if not openai_client:
#             logger.warning("[WARNING] No OpenAI API key found")
#             return {"success": False, "error": "No API key"}
        
#         if not reference_image_base64:
#             logger.error("[ERROR] No reference image provided for Flow 1")
#             return {"success": False, "error": "Reference image required"}
        
#         logger.info(f"[DESIGN] FLOW 1: Style-Based Image-to-Image for {room_type}...")
        
#         original_length = len(prompt)
        
#         if len(prompt) > 4500:
#             logger.warning(f"[WARNING] Prompt very long ({original_length} chars), trimming...")
#             prompt = prompt[:4500]
        
#         image_bytes = base64.b64decode(reference_image_base64)
#         temp_dir = tempfile.gettempdir()
#         temp_path = os.path.join(temp_dir, f'flow1_ref_{room_type}_{int(time.time())}.png')
        
#         with open(temp_path, 'wb') as f:
#             f.write(image_bytes)
        
#         logger.info(f"[SUCCESS] Reference image saved ({os.path.getsize(temp_path)} bytes)")
        
#         size = "1024x1024"
#         enhanced_prompt = f"Transform this room interior to {prompt}. Maintain the exact room layout, dimensions, and structural elements. Only change the style, colors, materials, and decorative elements."
        
#         with open(temp_path, 'rb') as image_file:
#             response = openai_client.images.edit(
#                 model="gpt-image-1",
#                 image=image_file,
#                 prompt=enhanced_prompt,
#                 size=size,
#                 n=1
#             )
        
#         image_data = response.data[0]
        
#         if hasattr(image_data, 'url') and image_data.url:
#             img_response = requests.get(image_data.url, timeout=30)
#             if img_response.status_code != 200:
#                 return {"success": False, "error": f"Failed to download image"}
#             image_base64 = base64.b64encode(img_response.content).decode('utf-8')
#         elif hasattr(image_data, 'b64_json') and image_data.b64_json:
#             image_base64 = image_data.b64_json
#         else:
#             return {"success": False, "error": "No image data in response"}
        
#         logger.info(f"[SUCCESS] Flow 1 Image-to-Image Success! Resolution: {size}")
        
#         return {
#             "success": True,
#             "image_base64": image_base64,
#             "model": "gpt-image-1-flow1",
#             "size": size,
#             "room_type": room_type,
#             "method": "style_with_layout_preservation"
#         }
        
#     except Exception as e:
#         logger.error(f"[ERROR] Flow 1 failed: {str(e)}")
#         traceback.print_exc()
#         return {"success": False, "error": str(e)}
    
#     finally:
#         if temp_path and os.path.exists(temp_path):
#             try:
#                 os.unlink(temp_path)
#             except Exception as cleanup_error:
#                 logger.warning(f"[WARNING] Could not delete temp file: {cleanup_error}")


# def generate_with_openai_custom_theme(prompt, reference_image_base64):
#     """FLOW 2: OpenAI GPT Image 1 - Image-to-Image (Custom Theme)"""
#     temp_path = None
    
#     try:
#         if not openai_client:
#             return {"success": False, "error": "No API key"}
        
#         logger.info("[DESIGN] FLOW 2: Custom Theme Image-to-Image...")
        
#         image_bytes = base64.b64decode(reference_image_base64)
#         temp_dir = tempfile.gettempdir()
#         temp_path = os.path.join(temp_dir, f'flow2_ref_{int(time.time())}.png')
        
#         with open(temp_path, 'wb') as f:
#             f.write(image_bytes)
        
#         with open(temp_path, 'rb') as image_file:
#             response = openai_client.images.edit(
#                 model="gpt-image-1",
#                 image=image_file,
#                 prompt=prompt,
#                 size="1024x1024",
#                 n=1
#             )
        
#         image_data = response.data[0]
        
#         if hasattr(image_data, 'url') and image_data.url:
#             img_response = requests.get(image_data.url, timeout=30)
#             if img_response.status_code != 200:
#                 return {"success": False, "error": "Failed to download"}
#             image_base64 = base64.b64encode(img_response.content).decode('utf-8')
#         elif hasattr(image_data, 'b64_json'):
#             image_base64 = image_data.b64_json
#         else:
#             return {"success": False, "error": "No image data"}
        
#         logger.info("[SUCCESS] Flow 2 Image-to-Image Success!")
        
#         return {
#             "success": True,
#             "image_base64": image_base64,
#             "model": "gpt-image-1-flow2",
#             "size": "1024x1024",
#             "method": "custom_theme_edit"
#         }
        
#     except Exception as e:
#         logger.error(f"[ERROR] Flow 2 failed: {str(e)}")
#         traceback.print_exc()
#         return {"success": False, "error": str(e)}
    
#     finally:
#         if temp_path and os.path.exists(temp_path):
#             try:
#                 os.unlink(temp_path)
#             except:
#                 pass


# # ============================================================
# # BASIC ROUTES
# # ============================================================

# @app.route('/', methods=['GET'])
# def home():
#     return jsonify({
#         'status': 'healthy',
#         'message': 'AI Interior Design Backend - Complete with Auth',
#         'version': '10.0.0',
#         'model': 'gpt-image-1',
#         'features': ['image-to-image', 'phone-otp', 'email-verification']
#     }), 200


# @app.route('/api/health', methods=['GET'])
# def health_check():
#     clean_expired_cache()
#     return jsonify({
#         'status': 'healthy',
#         'openai_configured': bool(OPENAI_API_KEY),
#         'twilio_configured': bool(twilio_client),
#         'email_configured': bool(EMAIL_USER and EMAIL_PASSWORD),
#         'supabase_configured': bool(supabase),
#         'cache_entries': len(image_cache)
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
# # REGISTRATION & OTP ENDPOINTS
# # ============================================================

# @app.route('/api/register', methods=['POST', 'OPTIONS'])
# def register_user():
#     """Register user and send Phone OTP + Email verification"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
        
#         full_name = data.get('full_name', '').strip()
#         email = data.get('email', '').strip().lower()
#         phone_number = data.get('phone_number', '').strip()
#         country_code = data.get('country_code', 'IN')
#         session_id = data.get('session_id')
        
#         logger.info(f"[REGISTRATION] New registration attempt - Email: {email}, Phone: {phone_number}")
        
#         # Email is now OPTIONAL
#         if not full_name or not phone_number:
#             logger.warning(f"[VALIDATION] Missing required fields")
#             return jsonify({'error': 'Name and phone number are required'}), 400
        
#         # Make email optional - if provided, clean it, otherwise set to None
#         email = email if email else None
        
#         if not supabase:
#             logger.error(f"[ERROR] Database not configured")
#             return jsonify({'error': 'Database not configured'}), 500
        
#         # Check existing user
#         existing_user = supabase.table('users').select('*').eq('phone_number', phone_number).execute()

        
#         if existing_user.data and len(existing_user.data) > 0:
#             user = existing_user.data[0]
            
#             if user.get('phone_verified'):
#                 logger.info(f"[INFO] Phone {phone_number} already verified")
#                 return jsonify({
#                     'success': True,
#                     'already_verified': True,
#                     'message': 'Phone already verified! You have unlimited access.',
#                     'user_id': user['id']
#                 }), 200
            
#             user_id = user['id']
#             logger.info(f"[INFO] Existing unverified user found: {email}")
#             # Update email if provided
#             if email:
#                 supabase.table('users').update({
#                     'email': email,
#                     'full_name': full_name
#                 }).eq('id', user_id).execute()
#         else:
#             # Create new user
#             user_data = {
#                 'full_name': full_name,
#                 'email': email,  # Can be None
#                 'phone_number': phone_number,
#                 'country_code': country_code,
#                 'email_verified': False,  # Not used for access control
#                 'phone_verified': False  # This is the ONLY field that grants access
#             }
            
#             new_user = supabase.table('users').insert(user_data).execute()
#             if not new_user.data:
#                 logger.error(f"[ERROR] Failed to create user in database")
#                 return jsonify({'error': 'Failed to create user'}), 500
            
#             user_id = new_user.data[0]['id']
#             logger.info(f"[SUCCESS] New user created: {email} (ID: {user_id})")
        
#         # Generate OTP
#         otp = generate_otp()
#         otp_expires = datetime.now() + timedelta(minutes=10)
        
#         logger.info(f"[OTP] Generated OTP for {email}: {otp} (Expires: {otp_expires})")
        
#         # Save OTP to logs
#         otp_data = {
#             'user_id': user_id,
#             'phone_number': phone_number,
#             'otp': otp,
#             'expires_at': otp_expires.isoformat(),
#             'ip_address': request.remote_addr,
#             'status': 'sent',
#             'attempts': 0
#         }
#         supabase.table('phone_otp_logs').insert(otp_data).execute()
#         logger.info(f"[OTP] OTP logged to database")
        
#         # Update user with OTP
#         supabase.table('users').update({
#             'phone_otp': otp,
#             'phone_otp_expires_at': otp_expires.isoformat()
#         }).eq('id', user_id).execute()
#         logger.info(f"[OTP] User record updated with OTP")
        
#         # Send SMS
#         logger.info(f"[SMS] Attempting to send OTP to {phone_number}...")
#         sms_sent = send_phone_otp(phone_number, country_code, otp)
        
#         if sms_sent:
#             logger.info(f"[SMS] OTP sent successfully to {phone_number}")
#         else:
#             logger.warning(f"[SMS] Failed to send OTP to {phone_number}")
        
#         # Generate email token
#         # Send info email ONLY if email is provided (NO verification token)
#         email_sent = False
#         if email:
#             logger.info(f"[EMAIL] Attempting to send info email to {email}...")
#             email_sent = send_info_email(full_name, email)
            
#             if email_sent:
#                 logger.info(f"[EMAIL] Info email sent to {email}")
#             else:
#                 logger.warning(f"[EMAIL] Failed to send info email to {email}")
        
#         # Log activity
#         if session_id:
#             activity_log = {
#                 'user_id': user_id,
#                 'session_id': session_id,
#                 'activity_type': 'registration_initiated',
#                 'ip_address': request.remote_addr,
#                 'user_agent': request.headers.get('User-Agent', '')
#             }
#             supabase.table('user_activity_logs').insert(activity_log).execute()
        
#         logger.info(f"[SUCCESS] Registration process complete for {email}")
        
#         # IMPORTANT: Do NOT return the OTP in production
#         response_data = {
#             'success': True,
#             'message': 'OTP sent to your phone. Please enter it to verify.',
#             'user_id': user_id,
#             'phone_number': phone_number,
#             'email': email,
#             'otp_expires_in_minutes': 10,
#             'info_email_sent': email_sent if email else None,
#             'sms_sent': sms_sent
#         }
        
#         # Only add OTP in development mode
#         if os.getenv('ENVIRONMENT') == 'development':
#             response_data['otp_for_testing'] = otp
#             logger.warning(f"[DEV] OTP exposed in response (development mode): {otp}")
        
#         return jsonify(response_data), 200

#     except Exception as e:
#         logger.error(f"[ERROR] Registration error: {e}")
#         traceback.print_exc()
#         return jsonify({'error': 'Registration failed', 'details': str(e)}), 500


# @app.route('/api/verify-otp', methods=['POST', 'OPTIONS'])
# def verify_otp():
#     """Verify Phone OTP"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
        
#         phone_number = data.get('phone_number', '').strip()
#         otp = data.get('otp', '').strip()
#         session_id = data.get('session_id')
        
#         # Validation
#         if not phone_number or not otp:
#             logger.warning(f"[VALIDATION] Missing phone or OTP")
#             return jsonify({'error': 'Phone number and OTP required'}), 400
        
#         # Validate OTP format (must be exactly 6 digits)
#         if not otp.isdigit() or len(otp) != 6:
#             logger.warning(f"[VALIDATION] Invalid OTP format: {otp}")
#             return jsonify({'error': 'OTP must be 6 digits'}), 400
        
#         if not supabase:
#             return jsonify({'error': 'Database not configured'}), 500
        
#         # Find user
#         # Find user by phone number
#         user_result = supabase.table('users').select('*').eq('phone_number', phone_number).execute()
        
#         if not user_result.data:
#             logger.warning(f"[VALIDATION] User not found: {phone_number}")
#             return jsonify({'error': 'User not found'}), 404
        
#         user = user_result.data[0]
#         user_id = user['id']
        
#         # Check if already verified
#         if user.get('phone_verified'):
#             logger.info(f"[INFO] Phone already verified: {phone_number}")
#             return jsonify({
#                 'success': True,
#                 'already_verified': True,
#                 'message': 'Phone already verified! You have unlimited access.'
#             }), 200
        
#         # Check OTP exists
#         stored_otp = user.get('phone_otp')
#         otp_expires_at = user.get('phone_otp_expires_at')
        
#         if not stored_otp or not otp_expires_at:
#             logger.warning(f"[VALIDATION] No OTP found for user: {phone_number}")
#             return jsonify({'error': 'No OTP found. Please request a new one.'}), 400
        
#         # Log OTP comparison
#         logger.info(f"[OTP_CHECK] Phone: {phone_number}, Stored: {stored_otp}, Received: {otp}, Match: {stored_otp == otp}")
        
#         # Check expiration
#         otp_expires = datetime.fromisoformat(otp_expires_at.replace('Z', '+00:00'))
#         now = datetime.now(otp_expires.tzinfo)
        
#         if now > otp_expires:
#             logger.warning(f"[VALIDATION] OTP expired for {phone_number}")
#             return jsonify({'error': 'OTP has expired. Please request a new one.'}), 400
        
#         # Verify OTP - CRITICAL: Must match exactly
#         if stored_otp != otp:
#             logger.warning(f"[VALIDATION] Invalid OTP attempt for {phone_number}. Expected: {stored_otp}, Got: {otp}")
            
#             # Update failed attempt count
#             try:
#                 supabase.table('phone_otp_logs').update({
#                     'status': 'failed',
#                     'failed_attempts': supabase.table('phone_otp_logs').select('failed_attempts').eq('user_id', user_id).eq('otp', stored_otp).order('created_at', desc=True).limit(1).execute().data[0].get('failed_attempts', 0) + 1
#                 }).eq('user_id', user_id).eq('otp', stored_otp).execute()
#             except:
#                 pass
            
#             return jsonify({'error': 'Invalid OTP. Please check and try again.'}), 400
        
        
#         # OTP is correct - Mark phone as verified (ONLY THIS GRANTS ACCESS)
#         logger.info(f"[SUCCESS] Correct OTP provided for {phone_number}. Marking as verified...")
        
#         supabase.table('users').update({
#             'phone_verified': True,  # THIS IS THE ONLY FIELD THAT MATTERS FOR ACCESS
#             'phone_otp': None,
#             'phone_otp_expires_at': None,
#             'updated_at': datetime.now().isoformat()
#         }).eq('id', user_id).execute()
        
#         # Update OTP log status
#         supabase.table('phone_otp_logs').update({
#             'status': 'verified',
#             'verified_at': datetime.now().isoformat()
#         }).eq('user_id', user_id).eq('otp', otp).execute()
        
#         # Update session
#         if session_id:
#             supabase.table('sessions').update({
#                 'is_verified': True,
#                 'user_id': user_id
#             }).eq('session_id', session_id).execute()
        
#         # Log activity
#         activity_log = {
#             'user_id': user_id,
#             'session_id': session_id,
#             'activity_type': 'phone_verified',
#             'activity_data': {'phone_number': phone_number, 'verification_method': 'otp'},
#             'ip_address': request.remote_addr,
#             'user_agent': request.headers.get('User-Agent', '')
#         }
#         supabase.table('user_activity_logs').insert(activity_log).execute()
        
#         logger.info(f"[SUCCESS] Phone verified successfully for {phone_number}")
        
#         return jsonify({
#             'success': True,
#             'message': '🎉 Phone verified! Unlimited designs unlocked.',
#             'verified': True,
#             'user_id': user_id,
#             'phone_number': phone_number,
#             'email': user.get('email')
#         }), 200

#     except Exception as e:
#         logger.error(f"[ERROR] OTP verification error: {e}")
#         traceback.print_exc()
#         return jsonify({'error': 'Verification failed', 'details': str(e)}), 500


# @app.route('/api/resend-otp', methods=['POST', 'OPTIONS'])
# def resend_otp():
#     """Resend OTP to phone"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         phone_number = data.get('phone_number', '').strip()
        
#         if not phone_number:
#             return jsonify({'error': 'Phone number required'}), 400
        
#         if not supabase:
#             return jsonify({'error': 'Database not configured'}), 500
        
#         user_result = supabase.table('users').select('*').eq('phone_number', phone_number).execute()
        
#         if not user_result.data:
#             return jsonify({'error': 'User not found'}), 404
        
#         user = user_result.data[0]
#         user_id = user['id']
#         country_code = user.get('country_code', 'IN')
        
#         # Generate new OTP
#         otp = generate_otp()
#         otp_expires = datetime.now() + timedelta(minutes=10)
        
#         supabase.table('users').update({
#             'phone_otp': otp,
#             'phone_otp_expires_at': otp_expires.isoformat()
#         }).eq('id', user_id).execute()
        
#         # Send SMS
#         sms_sent = send_phone_otp(phone_number, country_code, otp)
        
#         if not sms_sent:
#             return jsonify({'error': 'Failed to send OTP'}), 500
        
#         logger.info(f"[SUCCESS] OTP resent to {phone_number}")
        
#         response_data = {
#             'success': True,
#             'message': 'New OTP sent to your phone',
#             'otp_expires_in_minutes': 10
#         }
        
#         # Development mode
#         if os.getenv('ENVIRONMENT') == 'development':
#             response_data['otp_for_testing'] = otp
        
#         return jsonify(response_data), 200

#     except Exception as e:
#         logger.error(f"[ERROR] Resend OTP error: {e}")
#         return jsonify({'error': 'Failed to resend OTP'}), 500





# @app.route('/api/check-user', methods=['POST', 'OPTIONS'])
# def check_user_status():
#     """Check if user is verified (for cross-device sync) - READ ONLY, does not modify verification status"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         phone_number = data.get('phone_number', '').strip()
        
#         if not phone_number:
#             logger.warning(f"[CHECK_USER] No phone number provided")
#             return jsonify({'error': 'Phone number required'}), 400
        
#         if not supabase:
#             return jsonify({'error': 'Database not configured'}), 500
        
#         # Find user by phone
#         user_result = supabase.table('users').select('*').eq('phone_number', phone_number).execute()
        
#         if not user_result.data:
#             logger.info(f"[CHECK_USER] User not found: {phone_number}")
#             return jsonify({
#                 'exists': False,
#                 'verified': False
#             }), 200
        
#         user = user_result.data[0]
#         # ONLY phone_verified matters for unlimited access
#         is_verified = user.get('phone_verified', False)
        
#         logger.info(f"[CHECK_USER] Phone: {phone_number}, Verified: {is_verified}")
        
#         return jsonify({
#             'exists': True,
#             'verified': is_verified,  # This is what frontend should check
#             'phone_verified': user.get('phone_verified', False),
#             'user_id': user['id'],
#             'full_name': user.get('full_name'),
#             'email': user.get('email')
#         }), 200

#     except Exception as e:
#         logger.error(f"[ERROR] Check user error: {e}")
#         traceback.print_exc()
#         return jsonify({'error': 'Failed to check user status'}), 500


# # ============================================================
# # IMAGE GENERATION ROUTE - DUAL IMAGE-TO-IMAGE FLOW
# # ============================================================

# @app.route('/api/generate-design', methods=['POST', 'OPTIONS'])
# @timeout_decorator(180)
# def generate_design():
#     """Generate interior design with DUAL IMAGE-TO-IMAGE FLOW"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400

#         room_type = data.get('room_type')
#         client_name = data.get('client_name', 'skyline')  # Default to skyline
#         style = data.get('style')
#         custom_prompt = data.get('custom_prompt', '').strip()

#         # Validate client name
#         VALID_CLIENTS = ['skyline', 'ellington']
#         if client_name not in VALID_CLIENTS:
#             return jsonify({'error': f'Invalid client. Must be one of: {VALID_CLIENTS}'}), 400

#         # Validate inputs
#         is_valid, message = validate_inputs(room_type, style, custom_prompt)
#         if not is_valid:
#             return jsonify({'error': message}), 400

#         # Load reference image (required for both flows)
#         logger.info(f"[IMAGE] Loading reference image for {room_type}...")
#         reference_image = load_reference_image(room_type, client_name)
        
#         if not reference_image:
#             return jsonify({
#                 'error': f'Reference image not found for {room_type}',
#                 'details': 'Both flows require reference images'
#             }), 500

#         # Determine flow
#         is_custom_theme = bool(custom_prompt)
#         flow_type = "FLOW 2 (Custom Theme)" if is_custom_theme else "FLOW 1 (Style-Based)"
        
#         logger.info(f"[TARGET] {flow_type}: Room={room_type}, Style={style}, Client={client_name}")

#         # Build prompt
#         prompt_data = construct_prompt(room_type, style, custom_prompt)
#         if not prompt_data.get('success', True):
#             return jsonify({'error': prompt_data.get('error', 'Prompt construction failed')}), 400
        
#         prompt = prompt_data['prompt']
#         prompt = optimize_prompt_for_gpt_image1(prompt, room_type)

#         # Check cache
#         cached_result = get_cached_image(prompt)
#         if cached_result:
#             return jsonify({
#                 'success': True,
#                 'cached': True,
#                 'flow': flow_type,
#                 'images': [cached_result],
#                 'prompt_used': prompt[:200] + '...'
#             }), 200

#         # Execute appropriate flow
#         result = None
        
#         if is_custom_theme:
#             logger.info("[GENERATE] Flow 2: Custom theme image-to-image...")
#             result = generate_with_openai_custom_theme(prompt, reference_image)
#         else:
#             logger.info("[GENERATE] Flow 1: Style-based image-to-image...")
#             result = generate_with_openai_style_based(prompt, room_type, reference_image)

#         # Handle result
#         if not result or not result.get('success'):
#             return jsonify({
#                 'error': 'Generation failed',
#                 'flow': flow_type,
#                 'details': result.get('error', 'Unknown error') if result else 'No result'
#             }), 500
        
#         # Upload to Cloudinary FIRST
#         cloudinary_url = upload_to_cloudinary(result['image_base64'], client_name, room_type)
        
#         if not cloudinary_url:
#             logger.warning("[WARNING] Cloudinary upload failed, continuing without URL")
#             cloudinary_url = None

#         # Save to MongoDB SECOND (to get the ID)
#         generation_id = save_generation_to_db(
#             client_name=client_name,
#             room_type=room_type,
#             style=style,
#             custom_prompt=custom_prompt,
#             generated_image_url=cloudinary_url,
#             user_id=data.get('user_id')
#         )

#         # Create response_data THIRD (now generation_id exists)
#         response_data = {
#             'id': generation_id or 0,  # Use actual ID or fallback to 0
#             'image_base64': result['image_base64'],
#             'client_name': client_name,
#             'cloudinary_url': cloudinary_url,
#             'room_type': room_type,
#             'style': style if not is_custom_theme else 'custom',
#             'custom_theme': custom_prompt if is_custom_theme else None,
#             'model_used': result.get('model', 'gpt-image-1'),
#             'generation_method': result.get('method', flow_type),
#             'layout_system': 'image-to-image-preserved',
#             'resolution': result.get('size', '1024x1024'),
#             'flow': flow_type,
#             'used_reference_image': True
#         }

#         # Cache it LAST
#         save_to_cache(prompt, response_data)

#         return jsonify({
#             'success': True,
#             'cached': False,
#             'flow': flow_type,
#             'images': [response_data],
#             'prompt_used': prompt[:300] + '...',
#             'generation_details': {
#                 'method': 'image-to-image',
#                 'used_reference': True,
#                 'model': result.get('model'),
#                 'layout_preserved': True
#             }
#         }), 200

#     except Exception as e:
#         logger.error(f"[ERROR] Server Error: {e}")
#         traceback.print_exc()
#         return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


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
#     logger.info(f"Twilio: {'✓' if twilio_client else '✗'}")
#     logger.info(f"Email: {'✓' if EMAIL_USER and EMAIL_PASSWORD else '✗'}")
#     logger.info(f"Supabase: {'✓' if supabase else '✗'}")
#     app.run(host='0.0.0.0', port=port, debug=True)
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import requests
import traceback
import base64
import time
import hashlib
import logging
import tempfile
import io
import secrets
from functools import wraps
from openai import OpenAI
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from supabase import create_client, Client
from PIL import Image
from pymongo import MongoClient
import cloudinary
import cloudinary.uploader
import cloudinary.api
from datetime import timezone
import threading  # ✅ ADD THIS
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
    construct_custom_theme_prompt,
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
        logging.StreamHandler(sys.stdout)  # ✅ Console only
    ]
)
logger = logging.getLogger(__name__)  # ✅ ADD THIS LINE


# ============================================================
# CONFIGURATION
# ============================================================

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
mongo_client = MongoClient(MONGO_URI)
db = mongo_client["interior_design"]
# Email
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_USER)




# Frontend URL
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

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

CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Force headers on every response
@app.after_request
def apply_cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response

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
def save_generation_to_db(client_name, room_type, style, custom_prompt, generated_image_url, user_id=None):
    """Save generation to MongoDB for tracking"""
    try:
        generation_record = {
            "client_name": client_name,
            "room_type": room_type,
            "style": style,
            "custom_prompt": custom_prompt,
            "generated_image_url": generated_image_url,
            "user_id": user_id,
            "generated_at": datetime.now(),
            "downloaded": False,
            "download_count": 0
        }
        
        result = db.generated_images.insert_one(generation_record)
        logger.info(f"[DB] Saved generation to MongoDB: {result.inserted_id}")
        
        # Update client stats
        db.clients.update_one(
            {"client_name": client_name},
            {
                "$inc": {"total_generations": 1},
                "$setOnInsert": {
                    "created_at": datetime.now(),
                    "total_downloads": 0
                }
            },
            upsert=True
        )
        
        return str(result.inserted_id)
        
    except Exception as e:
        logger.error(f"[DB ERROR] Failed to save to MongoDB: {e}")
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

def generate_with_openai_style_based(prompt, room_type, reference_image_base64):
    """FLOW 1: OpenAI GPT Image 1 - Image-to-Image with Predefined Styles"""
    temp_path = None
    
    try:
        if not openai_client:
            logger.warning("[WARNING] No OpenAI API key found")
            return {"success": False, "error": "No API key"}
        
        if not reference_image_base64:
            logger.error("[ERROR] No reference image provided for Flow 1")
            return {"success": False, "error": "Reference image required"}
        
        logger.info(f"[DESIGN] FLOW 1: Style-Based Image-to-Image for {room_type}...")
        
        original_length = len(prompt)
        
        if len(prompt) > 4500:
            logger.warning(f"[WARNING] Prompt very long ({original_length} chars), trimming...")
            prompt = prompt[:4500]
        
        image_bytes = base64.b64decode(reference_image_base64)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f'flow1_ref_{room_type}_{int(time.time())}.png')
        
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        logger.info(f"[SUCCESS] Reference image saved ({os.path.getsize(temp_path)} bytes)")
        
        size = "1024x1024"
        enhanced_prompt = f"Transform this room interior to {prompt}. Maintain the exact room layout, dimensions, and structural elements. Only change the style, colors, materials, and decorative elements."
        
        with open(temp_path, 'rb') as image_file:
            response = openai_client.images.edit(
                model="gpt-image-1",
                image=image_file,
                prompt=enhanced_prompt,
                size=size,
                n=1
            )
        
        image_data = response.data[0]
        
        if hasattr(image_data, 'url') and image_data.url:
            img_response = requests.get(image_data.url, timeout=30)
            if img_response.status_code != 200:
                return {"success": False, "error": f"Failed to download image"}
            image_base64 = base64.b64encode(img_response.content).decode('utf-8')
        elif hasattr(image_data, 'b64_json') and image_data.b64_json:
            image_base64 = image_data.b64_json
        else:
            return {"success": False, "error": "No image data in response"}
        
        logger.info(f"[SUCCESS] Flow 1 Image-to-Image Success! Resolution: {size}")
        
        return {
            "success": True,
            "image_base64": image_base64,
            "model": "gpt-image-1-flow1",
            "size": size,
            "room_type": room_type,
            "method": "style_with_layout_preservation"
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Flow 1 failed: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as cleanup_error:
                logger.warning(f"[WARNING] Could not delete temp file: {cleanup_error}")


def generate_with_openai_custom_theme(prompt, reference_image_base64):
    """FLOW 2: OpenAI GPT Image 1 - Image-to-Image (Custom Theme)"""
    temp_path = None
    
    try:
        if not openai_client:
            return {"success": False, "error": "No API key"}
        
        logger.info("[DESIGN] FLOW 2: Custom Theme Image-to-Image...")
        
        image_bytes = base64.b64decode(reference_image_base64)
        temp_dir = tempfile.gettempdir()
        temp_path = os.path.join(temp_dir, f'flow2_ref_{int(time.time())}.png')
        
        with open(temp_path, 'wb') as f:
            f.write(image_bytes)
        
        with open(temp_path, 'rb') as image_file:
            response = openai_client.images.edit(
                model="gpt-image-1",
                image=image_file,
                prompt=prompt,
                size="1024x1024",
                n=1
            )
        
        image_data = response.data[0]
        
        if hasattr(image_data, 'url') and image_data.url:
            img_response = requests.get(image_data.url, timeout=30)
            if img_response.status_code != 200:
                return {"success": False, "error": "Failed to download"}
            image_base64 = base64.b64encode(img_response.content).decode('utf-8')
        elif hasattr(image_data, 'b64_json'):
            image_base64 = image_data.b64_json
        else:
            return {"success": False, "error": "No image data"}
        
        logger.info("[SUCCESS] Flow 2 Image-to-Image Success!")
        
        return {
            "success": True,
            "image_base64": image_base64,
            "model": "gpt-image-1-flow2",
            "size": "1024x1024",
            "method": "custom_theme_edit"
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Flow 2 failed: {str(e)}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}
    
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass


# ============================================================
# BASIC ROUTES
# ============================================================

@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'healthy',
        'message': 'AI Interior Design Backend - Complete with Auth',
        'version': '10.0.0',
        'model': 'gpt-image-1',
        'features': ['image-to-image', 'phone-otp', 'email-verification']
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    clean_expired_cache()
    return jsonify({
        'status': 'healthy',
        'openai_configured': bool(OPENAI_API_KEY),
        'twilio_configured': False,  
        'email_configured': bool(EMAIL_USER and EMAIL_PASSWORD),
        'supabase_configured': bool(supabase),
        'cache_entries': len(image_cache)
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
# REGISTRATION & OTP ENDPOINTS
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
        
        # Send welcome email (non-blocking)
        try:
            send_welcome_email(full_name, email)
            logger.info(f"[SIMPLE_REGISTER] Welcome email sent to {email}")
        except Exception as e:
            logger.warning(f"[SIMPLE_REGISTER] Failed to send welcome email: {e}")
        
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
# IMAGE GENERATION ROUTE - DUAL IMAGE-TO-IMAGE FLOW
# ============================================================

@app.route('/api/generate-design', methods=['POST', 'OPTIONS'])
@timeout_decorator(180)
def generate_design():
    """Generate interior design with DUAL IMAGE-TO-IMAGE FLOW"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        room_type = data.get('room_type')
        client_name = data.get('client_name', 'skyline')  # Default to skyline
        style = data.get('style')
        custom_prompt = data.get('custom_prompt', '').strip()

        # Validate client name
        VALID_CLIENTS = ['skyline', 'ellington']
        if client_name not in VALID_CLIENTS:
            return jsonify({'error': f'Invalid client. Must be one of: {VALID_CLIENTS}'}), 400

        # Validate inputs
        is_valid, message = validate_inputs(room_type, style, custom_prompt)
        if not is_valid:
            return jsonify({'error': message}), 400

        # Load reference image (required for both flows)
        logger.info(f"[IMAGE] Loading reference image for {room_type}...")
        reference_image = load_reference_image(room_type, client_name)
        
        if not reference_image:
            return jsonify({
                'error': f'Reference image not found for {room_type}',
                'details': 'Both flows require reference images'
            }), 500

        # Determine flow
        is_custom_theme = bool(custom_prompt)
        flow_type = "FLOW 2 (Custom Theme)" if is_custom_theme else "FLOW 1 (Style-Based)"
        
        logger.info(f"[TARGET] {flow_type}: Room={room_type}, Style={style}, Client={client_name}")

        # Build prompt
        prompt_data = construct_prompt(room_type, style, custom_prompt)
        if not prompt_data.get('success', True):
            return jsonify({'error': prompt_data.get('error', 'Prompt construction failed')}), 400
        
        prompt = prompt_data['prompt']
        prompt = optimize_prompt_for_gpt_image1(prompt, room_type)

        # Check cache
        # Check cache (with client_name)
        cached_result = get_cached_image(prompt, client_name)
        if cached_result:
            return jsonify({
                'success': True,
                'cached': True,
                'flow': flow_type,
                'client': client_name,
                'images': [cached_result],
                'prompt_used': prompt[:200] + '...'
            }), 200

        # ADD THIS DEBUG LINE
        logger.info(f"[DEBUG] Cache miss confirmed, proceeding to generation...")
        logger.info(f"[DEBUG] is_custom_theme={is_custom_theme}, reference_image exists={bool(reference_image)}")

        # Execute appropriate flow
        result = None

        # Execute appropriate flow
        result = None
        
        if is_custom_theme:
            logger.info("[GENERATE] Flow 2: Custom theme image-to-image...")
            result = generate_with_openai_custom_theme(prompt, reference_image)
        else:
            logger.info("[GENERATE] Flow 1: Style-based image-to-image...")
            result = generate_with_openai_style_based(prompt, room_type, reference_image)

        # Handle result
        if not result or not result.get('success'):
            return jsonify({
                'error': 'Generation failed',
                'flow': flow_type,
                'details': result.get('error', 'Unknown error') if result else 'No result'
            }), 500
        
        # Upload to Cloudinary FIRST
        cloudinary_url = upload_to_cloudinary(result['image_base64'], client_name, room_type)
        
        if not cloudinary_url:
            logger.warning("[WARNING] Cloudinary upload failed, continuing without URL")
            cloudinary_url = None

        # Save to MongoDB SECOND (to get the ID)
        generation_id = save_generation_to_db(
            client_name=client_name,
            room_type=room_type,
            style=style,
            custom_prompt=custom_prompt,
            generated_image_url=cloudinary_url,
            user_id=data.get('user_id')
        )

        # Create response_data THIRD (now generation_id exists)
        response_data = {
            'id': generation_id or 0,  # Use actual ID or fallback to 0
            'image_base64': result['image_base64'],
            'client_name': client_name,
            'cloudinary_url': cloudinary_url,
            'room_type': room_type,
            'style': style if not is_custom_theme else 'custom',
            'custom_theme': custom_prompt if is_custom_theme else None,
            'model_used': result.get('model', 'gpt-image-1'),
            'generation_method': result.get('method', flow_type),
            'layout_system': 'image-to-image-preserved',
            'resolution': result.get('size', '1024x1024'),
            'flow': flow_type,
            'used_reference_image': True
        }

        # Cache it LAST (with client_name)
        save_to_cache(prompt, response_data, client_name)

        return jsonify({
            'success': True,
            'cached': False,
            'flow': flow_type,
            'images': [response_data],
            'prompt_used': prompt[:300] + '...',
            'generation_details': {
                'method': 'image-to-image',
                'used_reference': True,
                'model': result.get('model'),
                'layout_preserved': True
            }
        }), 200

    except Exception as e:
        logger.error(f"[ERROR] Server Error: {e}")
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


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
    """Increment generation count for session"""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id or not supabase:
            return jsonify({'success': False}), 400
        
        # Update generation count
        session_result = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
        
        if session_result.data:
            current_count = session_result.data[0].get('generation_count', 0)
            new_count = current_count + 1
            
            supabase.table('sessions').update({
                'generation_count': new_count,
                'last_activity': datetime.now().isoformat()
            }).eq('session_id', session_id).execute()
            
            # Log the generation
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
# MAIN
# ============================================================

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    logger.info(f"Starting AI Interior Design Backend v10.0.0 on port {port}")
    logger.info(f"OpenAI: {'✓' if OPENAI_API_KEY else '✗'}")
    logger.info(f"Email: {'✓' if EMAIL_USER and EMAIL_PASSWORD else '✗'}")
    logger.info(f"Supabase: {'✓' if supabase else '✗'}")
    app.run(host='0.0.0.0', port=port, debug=False)  # ✅ Production ready