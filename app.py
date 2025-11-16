# from flask import Flask, request, jsonify
# from flask_cors import CORS
# import os
# import requests
# import traceback
# import base64
# import time
# from config import INTERIOR_STYLES, ROOM_DIMENSIONS
# from prompts import construct_prompt, validate_inputs

# # ✅ Load API keys (optional for some providers)
# HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")  # Optional but recommended

# app = Flask(__name__)

# # Enable CORS for frontend
# CORS(app, resources={
#     r"/api/*": {
#         "origins": ["http://localhost:5173", "http://localhost:3000"],
#         "methods": ["GET", "POST", "OPTIONS"],
#         "allow_headers": ["Content-Type"]
#     }
# })


# # --------------------------
# # 🏠 BASIC ROUTES
# # --------------------------
# @app.route('/', methods=['GET'])
# def home():
#     return jsonify({
#         'status': 'healthy',
#         'message': 'Property AI Backend (Free AI) is running',
#         'version': '3.0.0'
#     }), 200


# @app.route('/api/health', methods=['GET'])
# def health_check():
#     return jsonify({
#         'status': 'healthy',
#         'providers': ['pollinations', 'huggingface', 'fal'],
#         'endpoints': ['/api/generate-design', '/api/rooms', '/api/styles']
#     }), 200


# @app.route('/api/rooms', methods=['GET'])
# def get_rooms():
#     rooms = [
#         {'id': 'master_bedroom', 'name': 'Master Bedroom'},
#         {'id': 'living_room', 'name': 'Living Room'},
#         {'id': 'kitchen', 'name': 'Kitchen'},
#         {'id': 'main_bathroom', 'name': 'Main Bathroom'},
#         {'id': 'home_office', 'name': 'Home Office'},
#         {'id': 'dining_room', 'name': 'Dining Room'}
#     ]
#     return jsonify(rooms), 200


# @app.route('/api/styles', methods=['GET'])
# def get_styles():
#     styles = [
#         {'id': key, 'name': key.replace('_', ' ').title()}
#         for key in INTERIOR_STYLES.keys()
#     ]
#     return jsonify(styles), 200


# # --------------------------
# # 🎨 IMAGE GENERATION
# # --------------------------
# @app.route('/api/generate-design', methods=['POST', 'OPTIONS'])
# def generate_design():
#     """Generate interior design using free AI providers"""
#     if request.method == 'OPTIONS':
#         return '', 204

#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'error': 'No data provided'}), 400

#         room_type = data.get('room_type')
#         style = data.get('style')
#         custom_prompt = data.get('custom_prompt', '').strip()
#         custom_dimensions = data.get('dimensions', '').strip()
#         provider = data.get('provider', 'pollinations')  # pollinations, huggingface, or fal

#         is_valid, message = validate_inputs(room_type, style, custom_prompt)
#         if not is_valid:
#             return jsonify({'error': message}), 400

#         if custom_dimensions:
#             ROOM_DIMENSIONS[room_type] = custom_dimensions

#         prompt_data = construct_prompt(room_type, style, custom_prompt)
#         prompt = prompt_data['prompt']

#         print(f"🧠 Generating {room_type} ({style}) using {provider}...")

#         # Try providers in order of preference
#         result = None
#         if provider == 'pollinations':
#             result = generate_with_pollinations(prompt)
#         elif provider == 'huggingface':
#             result = generate_with_huggingface(prompt)
#         elif provider == 'fal':
#             result = generate_with_fal(prompt)
        
#         # Fallback chain if primary fails
#         if not result or not result['success']:
#             print(f"⚠️ {provider} failed, trying fallback...")
#             if provider != 'pollinations':
#                 result = generate_with_pollinations(prompt)
#             if not result['success'] and provider != 'huggingface':
#                 result = generate_with_huggingface(prompt)

#         if not result['success']:
#             return jsonify({
#                 'error': 'Generation failed',
#                 'details': result.get('error', 'All providers failed')
#             }), 500

#         return jsonify({
#             'success': True,
#             'images': [{
#                 'id': 0,
#                 'image_base64': result['image_base64'],
#                 'room_type': room_type,
#                 'style': style or 'custom',
#                 'model_used': result.get('model', 'unknown')
#             }],
#             'prompt_used': prompt
#         }), 200

#     except Exception as e:
#         print("⚠️ Server Error:", e)
#         traceback.print_exc()
#         return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


# # --------------------------
# # 🧠 FREE AI PROVIDERS
# # --------------------------

# def generate_with_pollinations(prompt):
#     """
#     Pollinations AI - Completely FREE, no API key needed
#     Best for: Quick testing, unlimited generations
#     """
#     try:
#         # Pollinations uses URL-based generation
#         import urllib.parse
#         encoded_prompt = urllib.parse.quote(prompt)
        
#         # High quality settings
#         url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&model=flux&nologo=true&enhance=true"
        
#         print(f"📡 Fetching from Pollinations: {url[:100]}...")
        
#         response = requests.get(url, timeout=60)
        
#         if response.status_code != 200:
#             return {"success": False, "error": f"HTTP {response.status_code}"}
        
#         # Convert to base64
#         image_base64 = base64.b64encode(response.content).decode('utf-8')
        
#         return {
#             "success": True, 
#             "image_base64": image_base64,
#             "model": "pollinations-flux"
#         }
        
#     except Exception as e:
#         print(f"❌ Pollinations failed: {e}")
#         return {"success": False, "error": str(e)}


# def generate_with_huggingface(prompt):
#     """
#     Hugging Face - FREE tier with 1000 requests/month
#     Best for: High quality, various models
#     Get free API key: https://huggingface.co/settings/tokens
#     """
#     try:
#         if not HUGGINGFACE_API_KEY:
#             print("⚠️ No HuggingFace API key found, skipping...")
#             return {"success": False, "error": "No API key"}
        
#         # Using FLUX.1 Schnell (fast, high quality, free)
#         API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        
#         headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
#         payload = {
#             "inputs": prompt,
#             "parameters": {
#                 "width": 1024,
#                 "height": 576,
#                 "num_inference_steps": 4  # Faster generation
#             }
#         }
        
#         print("📡 Calling Hugging Face API...")
#         response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
#         if response.status_code != 200:
#             print(f"❌ HuggingFace error: {response.text}")
#             return {"success": False, "error": response.text}
        
#         # Convert to base64
#         image_base64 = base64.b64encode(response.content).decode('utf-8')
        
#         return {
#             "success": True,
#             "image_base64": image_base64,
#             "model": "huggingface-flux-schnell"
#         }
        
#     except Exception as e:
#         print(f"❌ Hugging Face failed: {e}")
#         return {"success": False, "error": str(e)}


# def generate_with_fal(prompt):
#     """
#     FAL.ai - Generous free tier, very fast
#     Get free API key: https://fal.ai/dashboard
#     """
#     try:
#         FAL_API_KEY = os.getenv("FAL_API_KEY")
#         if not FAL_API_KEY:
#             print("⚠️ No FAL API key found, skipping...")
#             return {"success": False, "error": "No API key"}
        
#         url = "https://fal.run/fal-ai/flux/schnell"
        
#         headers = {
#             "Authorization": f"Key {FAL_API_KEY}",
#             "Content-Type": "application/json"
#         }
        
#         payload = {
#             "prompt": prompt,
#             "image_size": {
#                 "width": 1024,
#                 "height": 576
#             },
#             "num_inference_steps": 4
#         }
        
#         print("📡 Calling FAL.ai API...")
#         response = requests.post(url, headers=headers, json=payload, timeout=60)
        
#         if response.status_code != 200:
#             return {"success": False, "error": response.text}
        
#         result = response.json()
#         image_url = result.get('images', [{}])[0].get('url')
        
#         if not image_url:
#             return {"success": False, "error": "No image URL returned"}
        
#         # Download and convert to base64
#         img_response = requests.get(image_url, timeout=30)
#         image_base64 = base64.b64encode(img_response.content).decode('utf-8')
        
#         return {
#             "success": True,
#             "image_base64": image_base64,
#             "model": "fal-flux-schnell"
#         }
        
#     except Exception as e:
#         print(f"❌ FAL.ai failed: {e}")
#         return {"success": False, "error": str(e)}


# # --------------------------
# # 🚀 Run Server
# # --------------------------
# if __name__ == '__main__':
#     print("\n✅ Free AI Image Generation Ready!")
#     print("📌 Pollinations: Always available (no key needed)")
#     print(f"📌 Hugging Face: {'✅ Configured' if HUGGINGFACE_API_KEY else '❌ Not configured'}")
#     print(f"📌 FAL.ai: {'✅ Configured' if os.getenv('FAL_API_KEY') else '❌ Not configured'}")
#     print("\n🚀 Starting Flask server on http://localhost:5000")
#     app.run(debug=True, host='0.0.0.0', port=5000)
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests
import traceback
import base64
import time
from config import INTERIOR_STYLES, ROOM_DIMENSIONS
from prompts import construct_prompt, validate_inputs

# ✅ Load API keys (optional for some providers)
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")  # Optional but recommended

app = Flask(__name__)

# Enable CORS for frontend
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:5173", "http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})


# --------------------------
# 🏠 BASIC ROUTES
# --------------------------
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'healthy',
        'message': 'Property AI Backend (Free AI) is running',
        'version': '3.0.0'
    }), 200


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'providers': ['pollinations', 'huggingface', 'fal'],
        'endpoints': ['/api/generate-design', '/api/rooms', '/api/styles']
    }), 200


@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    rooms = [
        {'id': 'master_bedroom', 'name': 'Master Bedroom'},
        {'id': 'living_room', 'name': 'Living Room'},
        {'id': 'kitchen', 'name': 'Kitchen'},
        {'id': 'main_bathroom', 'name': 'Main Bathroom'},
        {'id': 'home_office', 'name': 'Home Office'},
        {'id': 'dining_room', 'name': 'Dining Room'}
    ]
    return jsonify(rooms), 200


@app.route('/api/styles', methods=['GET'])
def get_styles():
    styles = [
        {'id': key, 'name': key.replace('_', ' ').title()}
        for key in INTERIOR_STYLES.keys()
    ]
    return jsonify(styles), 200


# --------------------------
# 🎨 IMAGE GENERATION
# --------------------------
@app.route('/api/generate-design', methods=['POST', 'OPTIONS'])
def generate_design():
    """Generate interior design using free AI providers"""
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
        provider = data.get('provider', 'pollinations')  # pollinations, huggingface, or fal

        is_valid, message = validate_inputs(room_type, style, custom_prompt)
        if not is_valid:
            return jsonify({'error': message}), 400

        if custom_dimensions:
            ROOM_DIMENSIONS[room_type] = custom_dimensions

        prompt_data = construct_prompt(room_type, style, custom_prompt)
        prompt = prompt_data['prompt']

        print(f"🧠 Generating {room_type} ({style}) using {provider}...")

        # Try providers in order of preference
        result = None
        if provider == 'pollinations':
            result = generate_with_pollinations(prompt)
        elif provider == 'huggingface':
            result = generate_with_huggingface(prompt)
        elif provider == 'fal':
            result = generate_with_fal(prompt)
        
        # Fallback chain if primary fails
        if not result or not result['success']:
            print(f"⚠️ {provider} failed, trying fallback chain...")
            
            # Try Pollinations first (always available)
            if provider != 'pollinations':
                print("🔄 Trying Pollinations...")
                result = generate_with_pollinations(prompt)
            
            # Try Together AI (free, no key needed)
            if not result['success']:
                print("🔄 Trying Together AI...")
                result = generate_with_together(prompt)
            
            # Try HuggingFace if available
            if not result['success'] and provider != 'huggingface' and HUGGINGFACE_API_KEY:
                print("🔄 Trying HuggingFace...")
                result = generate_with_huggingface(prompt)
            
            # Try FAL if available
            if not result['success'] and provider != 'fal' and os.getenv('FAL_API_KEY'):
                print("🔄 Trying FAL.ai...")
                result = generate_with_fal(prompt)

        if not result['success']:
            return jsonify({
                'error': 'Generation failed',
                'details': result.get('error', 'All providers failed')
            }), 500

        return jsonify({
            'success': True,
            'images': [{
                'id': 0,
                'image_base64': result['image_base64'],
                'room_type': room_type,
                'style': style or 'custom',
                'model_used': result.get('model', 'unknown')
            }],
            'prompt_used': prompt
        }), 200

    except Exception as e:
        print("⚠️ Server Error:", e)
        traceback.print_exc()
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


# --------------------------
# 🧠 FREE AI PROVIDERS
# --------------------------

def generate_with_pollinations(prompt):
    """
    Pollinations AI - Completely FREE, no API key needed
    Best for: Quick testing, unlimited generations
    Updated: 2024 API format with retry logic
    """
    try:
        import urllib.parse
        
        # Shorten prompt if too long (URL length limits)
        if len(prompt) > 600:
            prompt = prompt[:600]
        
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Try multiple API formats (Pollinations API has changed)
        urls_to_try = [
            # Format 1: Direct image endpoint (most reliable)
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576&nologo=true&seed={int(time.time())}",
            # Format 2: Simple format
            f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=576",
            # Format 3: New API format
            f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=576&nologo=true",
        ]
        
        for i, url in enumerate(urls_to_try):
            # Retry each URL up to 2 times for transient errors
            for retry in range(2):
                try:
                    if retry > 0:
                        print(f"🔄 Retry {retry+1}/2 for format {i+1}")
                        time.sleep(2)  # Wait before retry
                    else:
                        print(f"📡 Pollinations attempt {i+1}/{len(urls_to_try)}: {url[:100]}...")
                    
                    # Add headers to look like a browser
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'image/png,image/jpeg,image/*'
                    }
                    
                    response = requests.get(url, headers=headers, timeout=90, allow_redirects=True)
                    
                    # HTTP 530 is a temporary error - retry
                    if response.status_code == 530 and retry < 1:
                        print(f"⚠️ Service temporarily unavailable (530), retrying...")
                        continue
                    
                    # Check if we got valid image data
                    if response.status_code == 200 and len(response.content) > 5000:
                        # Verify it's actually an image
                        content_type = response.headers.get('content-type', '')
                        if 'image' in content_type or response.content[:4] in [b'\x89PNG', b'\xff\xd8\xff']:
                            image_base64 = base64.b64encode(response.content).decode('utf-8')
                            print(f"✅ Pollinations success with format {i+1}")
                            return {
                                "success": True, 
                                "image_base64": image_base64,
                                "model": "pollinations"
                            }
                    
                    print(f"⚠️ Attempt {i+1} failed: HTTP {response.status_code}, size: {len(response.content)} bytes")
                    break  # Don't retry if it's not a 530 error
                    
                except requests.exceptions.Timeout:
                    print(f"⚠️ Attempt {i+1} timed out")
                    if retry < 1:
                        continue  # Retry on timeout
                    break
                except Exception as attempt_error:
                    print(f"⚠️ Attempt {i+1} error: {attempt_error}")
                    break
        
        return {"success": False, "error": "Pollinations temporarily unavailable (HTTP 530) - service may be overloaded"}
        
    except Exception as e:
        print(f"❌ Pollinations error: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def generate_with_huggingface(prompt):
    """
    Hugging Face - FREE tier with 1000 requests/month
    Best for: High quality, various models
    Get free API key: https://huggingface.co/settings/tokens
    """
    try:
        if not HUGGINGFACE_API_KEY:
            print("⚠️ No HuggingFace API key found, skipping...")
            return {"success": False, "error": "No API key"}
        
        # Using FLUX.1 Schnell (fast, high quality, free)
        API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
        
        headers = {"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"}
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "width": 1024,
                "height": 576,
                "num_inference_steps": 4  # Faster generation
            }
        }
        
        print("📡 Calling Hugging Face API...")
        response = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        
        if response.status_code != 200:
            print(f"❌ HuggingFace error: {response.text}")
            return {"success": False, "error": response.text}
        
        # Convert to base64
        image_base64 = base64.b64encode(response.content).decode('utf-8')
        
        return {
            "success": True,
            "image_base64": image_base64,
            "model": "huggingface-flux-schnell"
        }
        
    except Exception as e:
        print(f"❌ Hugging Face failed: {e}")
        return {"success": False, "error": str(e)}


def generate_with_fal(prompt):
    """
    FAL.ai - Generous free tier, very fast
    Get free API key: https://fal.ai/dashboard
    With retry logic for transient errors
    """
    try:
        FAL_API_KEY = os.getenv("FAL_API_KEY")
        if not FAL_API_KEY:
            print("⚠️ No FAL API key found, skipping...")
            return {"success": False, "error": "No API key"}
        
        url = "https://fal.run/fal-ai/flux/schnell"
        
        headers = {
            "Authorization": f"Key {FAL_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "prompt": prompt,
            "image_size": {
                "width": 1024,
                "height": 576
            },
            "num_inference_steps": 4
        }
        
        # Retry up to 2 times for transient errors
        for attempt in range(2):
            try:
                if attempt > 0:
                    print(f"🔄 FAL.ai retry {attempt+1}/2...")
                    time.sleep(3)  # Wait before retry
                else:
                    print("📡 Calling FAL.ai API...")
                
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                
                print(f"📊 FAL Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    image_url = result.get('images', [{}])[0].get('url')
                    
                    if not image_url:
                        print(f"❌ No image URL in response: {result}")
                        return {"success": False, "error": "No image URL returned"}
                    
                    # Download and convert to base64
                    img_response = requests.get(image_url, timeout=30)
                    
                    if img_response.status_code != 200:
                        print(f"❌ Image download failed: HTTP {img_response.status_code}")
                        if attempt < 1:
                            continue  # Retry
                        return {"success": False, "error": f"Image download failed: {img_response.status_code}"}
                    
                    image_base64 = base64.b64encode(img_response.content).decode('utf-8')
                    print(f"✅ FAL.ai success! Image size: {len(img_response.content)} bytes")
                    
                    return {
                        "success": True,
                        "image_base64": image_base64,
                        "model": "fal-flux-schnell"
                    }
                
                # Check for rate limit or temporary errors
                elif response.status_code in [429, 500, 502, 503, 504]:
                    print(f"⚠️ Transient error {response.status_code}, may retry...")
                    if attempt < 1:
                        continue  # Retry
                
                # Other errors
                error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                print(f"❌ FAL.ai error: {error_msg}")
                return {"success": False, "error": error_msg}
                
            except requests.exceptions.Timeout:
                print(f"⚠️ FAL.ai request timed out (attempt {attempt+1})")
                if attempt < 1:
                    continue  # Retry on timeout
                return {"success": False, "error": "Request timed out after retries"}
            
            except Exception as attempt_error:
                print(f"❌ FAL.ai attempt {attempt+1} error: {attempt_error}")
                if attempt < 1:
                    continue
                traceback.print_exc()
                return {"success": False, "error": str(attempt_error)}
        
        return {"success": False, "error": "All FAL.ai attempts failed"}
        
    except Exception as e:
        print(f"❌ FAL.ai failed: {e}")
        traceback.print_exc()
        return {"success": False, "error": str(e)}


def generate_with_together(prompt):
    """
    Together AI - Free tier with no API key needed (via inference endpoint)
    Uses their public demo endpoint
    """
    try:
        print("📡 Trying Together AI free endpoint...")
        
        # Shorten prompt if needed
        if len(prompt) > 500:
            prompt = prompt[:500]
        
        # Try the public inference API (no key required)
        url = "https://api.together.xyz/inference"
        
        payload = {
            "model": "black-forest-labs/FLUX.1-schnell-Free",
            "prompt": prompt,
            "width": 1024,
            "height": 576,
            "steps": 4,
            "n": 1
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=90)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check for image URL or base64 in response
            if 'output' in result and 'choices' in result['output']:
                image_data = result['output']['choices'][0].get('image_base64')
                if image_data:
                    print("✅ Together AI success!")
                    return {
                        "success": True,
                        "image_base64": image_data,
                        "model": "together-flux-free"
                    }
        
        print(f"⚠️ Together AI failed: {response.status_code}")
        return {"success": False, "error": f"HTTP {response.status_code}"}
        
    except Exception as e:
        print(f"❌ Together AI error: {e}")
        return {"success": False, "error": str(e)}


# --------------------------
# 🚀 Run Server
# --------------------------
if __name__ == '__main__':
    print("\n✅ Free AI Image Generation Ready!")
    print("📌 Pollinations: Always available (no key needed)")
    print(f"📌 Hugging Face: {'✅ Configured' if HUGGINGFACE_API_KEY else '❌ Not configured'}")
    print(f"📌 FAL.ai: {'✅ Configured' if os.getenv('FAL_API_KEY') else '❌ Not configured'}")
    print("\n🚀 Starting Flask server on http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)