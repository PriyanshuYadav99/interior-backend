"""
AI interior-design generation pipeline.

Everything here is moved verbatim from app.py's module-level helper
functions — caching, Supabase persistence, Cloudinary upload, prompt
processing, and the Replicate model-call/polling logic. No business logic
was changed; only imports and two `__file__`-relative path lookups were
adjusted so they still resolve correctly now that this code lives one
folder deeper than app.py used to (see the BASE_DIR note below).
"""

import os
import io
import time
import base64
import hashlib
import secrets
import logging
import traceback
from datetime import datetime

import requests
import cloudinary.uploader
from PIL import Image

from config.settings import (
    REPLICATE_API_TOKEN,
    CACHE_DURATION,
    VERSION_CACHE_DURATION,
)
from content.design_content import ROOM_IMAGES, BASE_DIR
from services.external_clients import supabase

logger = logging.getLogger(__name__)

# ── In-process caches (module-level state, same as the original app.py) ──
image_cache = {}
_cached_model_version = None
_version_cache_time = None


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

        # STEP 1: Save generation to user_generations
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

        # STEP 2: Update client statistics
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
            # NOTE: BASE_DIR is imported from content.design_content rather
            # than recomputed via __file__ here, since this module now lives
            # one folder deeper than app.py used to — reusing the already
            # project-root-relative BASE_DIR keeps this path identical to
            # the original behavior.
            base_dir = BASE_DIR

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
            elif client_name == 'sothebys':
                filename_map = {
                'master_bedroom': 'sothebys_bedroom.webp',
                'living_room': 'sothebys_living_room.webp',
                'kitchen': 'sothebys_kitchen.webp'
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
            timeout=15
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
                timeout=15
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


# ── Wrapper functions (kept for backward-compatible call sites) ──────────

def generate_with_gemini_flash_image(prompt, room_type, reference_image_base64):
    """WRAPPER: Maintains backward compatibility. Calls unified function with is_custom_theme=False"""
    return generate_interior_design_unified(
        prompt=prompt,
        reference_image_base64=reference_image_base64,
        room_type=room_type,
        is_custom_theme=False
    )


def generate_with_openai_style_based(prompt, room_type, reference_image_base64, width=1024, height=1024):
    """FLOW 1 WRAPPER: Style-based generation. Calls unified function with is_custom_theme=False"""
    return generate_interior_design_unified(
        prompt=prompt,
        reference_image_base64=reference_image_base64,
        room_type=room_type,
        is_custom_theme=False,
        width=width,
        height=height
    )


def generate_with_openai_custom_theme(prompt, reference_image_base64, width=1024, height=1024):
    """FLOW 2 WRAPPER: Custom theme generation. Calls unified function with is_custom_theme=True"""
    return generate_interior_design_unified(
        prompt=prompt,
        reference_image_base64=reference_image_base64,
        room_type="custom",
        is_custom_theme=True,
        width=width,
        height=height
    )
