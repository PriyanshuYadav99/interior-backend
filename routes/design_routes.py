"""
Core design-generation, registration, and session-tracking routes.

This was previously ~900 lines of routes defined directly on the Flask
`app` object inside app.py, alongside 6 *other* features that were already
properly split into their own blueprint files. This module brings the
design-generation feature in line with that same pattern. Every route body
below is unchanged from the original — only the decorator (@app.route ->
@design_bp.route) and imports changed.
"""

import time
import logging
import threading
import traceback
from datetime import datetime

from flask import Blueprint, request, jsonify

from config.settings import REPLICATE_API_TOKEN, EMAIL_USER, EMAIL_PASSWORD
from content.design_content import ROOM_IMAGES, FIXED_ROOM_LAYOUTS, INTERIOR_STYLES
from content.prompts import construct_prompt, validate_inputs
from services.external_clients import supabase
from services.design_generation_service import (
    image_cache,
    get_cached_image,
    save_to_cache,
    clean_expired_cache,
    load_reference_image,
    optimize_prompt_for_gpt_image1,
    upload_to_cloudinary,
    save_generation_to_db,
    generate_with_openai_style_based,
    generate_with_openai_custom_theme,
)
from services.email_service import send_welcome_email
from services.scheduler import schedule_user_notification
from utils.decorators import timeout_decorator

logger = logging.getLogger(__name__)

design_bp = Blueprint('design', __name__)


@design_bp.route('/', methods=['GET'])
def home():
    return jsonify({
        'status': 'healthy',
        'message': 'AI Interior Design Backend - Imagen 3 Powered',
        'version': '12.0.0',
        'models': ['imagen-3'],
        'features': ['ai-generation', 'email-verification', 'multi-client']
    }), 200


@design_bp.route('/api/health', methods=['GET'])
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


@design_bp.route('/api/rooms', methods=['GET'])
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


@design_bp.route('/api/styles', methods=['GET'])
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

@design_bp.route('/api/simple-register', methods=['POST', 'OPTIONS'])
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
        client_name = data.get('client_name', 'skyline')
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

        # NO DUPLICATE CHECKS - Allow all registrations (even duplicates)
        logger.info(f"[SIMPLE_REGISTER] Creating new user (duplicates allowed): {email}, {phone_number}")

        # Create new user - NO checks, always insert
        property_section = data.get('property_section', None)
        user_data = {
            'full_name': full_name,
            'email': email,
            'phone_number': phone_number,
            'country_code': country_code,
            'client_name': client_name,
            'property_section': property_section,
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

        # Schedule WhatsApp/SMS notification
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

        # Send welcome email in background thread (non-blocking)
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


@design_bp.route('/api/check-user', methods=['POST', 'OPTIONS'])
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

@design_bp.route('/api/generate-design', methods=['POST', 'OPTIONS'])
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
        property_section = data.get('property_section')
        custom_prompt = data.get('custom_prompt', '').strip()
        width = data.get('width', 1024)
        height = data.get('height', 1024)
        logger.info(f"="*70)
        logger.info(f"[REQUEST] Room: {room_type} | Style: {style} | Client: {client_name}")
        logger.info(f"="*70)

        # Validate client
        VALID_CLIENTS = ['skyline', 'ellington', 'sothebys']
        if client_name not in VALID_CLIENTS:
            return jsonify({'error': f'Invalid client. Must be one of: {VALID_CLIENTS}'}), 400

        # Validate inputs
        is_valid, message = validate_inputs(room_type, style, custom_prompt)
        if not is_valid:
            return jsonify({'error': message}), 400

        # CHECK CACHE FIRST (BEFORE GENERATION)
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

        # GENERATE IMAGE (FAST - 7-8 SECONDS)
        logger.info(f"[STEP 3/3] Generating with Replicate...")
        start_time = time.time()

        if is_custom_theme:
            result = generate_with_openai_custom_theme(prompt, reference_image, width, height)
        else:
            result = generate_with_openai_style_based(prompt, room_type, reference_image, width, height)

        if not result or not result.get('success'):
            error_msg = result.get('error', 'Unknown error') if result else 'No result returned'
            logger.error(f"[GENERATION FAILED] {error_msg}")
            return jsonify({
                'error': 'Generation failed',
                'details': error_msg
            }), 500

        generation_time = time.time() - start_time
        logger.info(f"[SUCCESS] ✨ Generated in {generation_time:.2f}s")

        # PREPARE RESPONSE IMMEDIATELY (NO BLOCKING)
        image_base64 = result['image_base64']

        response_data = {
            'id': int(time.time()),
            'image_base64': image_base64,
            'client_name': client_name,
            'room_type': room_type,
            'style': style if not is_custom_theme else 'custom',
            'custom_theme': custom_prompt if is_custom_theme else None,
            'model_used': 'adirik/interior-design',
            'generation_method': result.get('method'),
            'resolution': f"{width}x{height}",
            'generation_time': f"{generation_time:.2f}s"
        }

        # CACHE THE RESULT
        save_to_cache(cache_prompt, response_data, client_name)

        # DO CLOUDINARY + DATABASE IN BACKGROUND (NON-BLOCKING)
        def background_upload():
            """Upload to Cloudinary and save to DB in background"""
            try:
                cloudinary_url = upload_to_cloudinary(image_base64, client_name, room_type)

                if cloudinary_url:
                    logger.info(f"[BACKGROUND] ✅ Uploaded to Cloudinary: {cloudinary_url}")

                    request_user_id = data.get('user_id')
                    request_session_id = data.get('session_id')

                    save_generation_to_db(
                        client_name=client_name,
                        room_type=room_type,
                        style=style if not is_custom_theme else 'custom',
                        custom_prompt=custom_prompt if is_custom_theme else None,
                        generated_image_url=cloudinary_url,
                        user_id=request_user_id,
                        session_id=request_session_id
                    )
                    logger.info(f"[BACKGROUND] ✅ Saved to database")

                    if request_user_id:
                        try:
                            user_result = supabase.table('users')\
                                .select('total_generations')\
                                .eq('id', request_user_id)\
                                .execute()
                            if user_result.data:
                                current = user_result.data[0]['total_generations'] or 0
                                supabase.table('users')\
                                    .update({'total_generations': current + 1})\
                                    .eq('id', request_user_id)\
                                    .execute()
                                logger.info(f"[DB] ✅ Updated total_generations for {request_user_id}: {current} → {current + 1}")
                        except Exception as e:
                            logger.warning(f"[DB] Could not update total_generations: {e}")

                    try:
                        supabase.table('user_property_interests').insert({
                            'user_id': request_user_id,
                            'client_name': client_name,
                            'property_section': property_section,
                            'room_type': room_type,
                            'style': style if not is_custom_theme else 'custom'
                        }).execute()
                        logger.info(f"[BACKGROUND] ✅ Logged property interest")
                    except Exception as e:
                        logger.warning(f"[BACKGROUND] Could not log interest: {e}")

                else:
                    logger.error(f"[BACKGROUND] ❌ Cloudinary upload failed")

            except Exception as e:
                logger.error(f"[BACKGROUND] ❌ Error: {e}")

        # Start background thread
        upload_thread = threading.Thread(target=background_upload, daemon=True)
        upload_thread.start()
        logger.info(f"[BACKGROUND] 🚀 Upload thread started (non-blocking)")

        # RETURN IMMEDIATELY - DON'T WAIT FOR UPLOADS
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

@design_bp.route('/api/create-session', methods=['POST', 'OPTIONS'])
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


@design_bp.route('/api/check-session', methods=['POST', 'OPTIONS'])
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


@design_bp.route('/api/increment-generation', methods=['POST', 'OPTIONS'])
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

            # Update count (keep this synchronous)
            supabase.table('sessions').update({
                'generation_count': new_count,
                'last_activity': datetime.now().isoformat()
            }).eq('session_id', session_id).execute()

            # MOVE THIS TO BACKGROUND THREAD
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

            # RETURN IMMEDIATELY
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

@design_bp.route('/api/cache/clear', methods=['POST'])
def clear_cache():
    """Clear all cached images"""
    cache_count = len(image_cache)
    image_cache.clear()
    logger.info(f"[CLEANUP] Manually cleared {cache_count} cache entries")
    return jsonify({
        'success': True,
        'message': f'Cleared {cache_count} cached images'
    }), 200


@design_bp.route('/api/room-preview/<client_name>/<room_type>', methods=['GET'])
def get_room_preview(client_name, room_type):
    """Serve the base reference image for a room so frontend can show it immediately on room click"""
    try:
        VALID_CLIENTS = ['skyline', 'ellington','sothebys']
        if client_name not in VALID_CLIENTS:
            return jsonify({'error': f'Invalid client'}), 400

        image_base64 = load_reference_image(room_type, client_name)
        if not image_base64:
            return jsonify({'error': 'Image not found'}), 404

        return jsonify({
            'success': True,
            'image_base64': image_base64,
            'room_type': room_type,
            'client_name': client_name
        }), 200

    except Exception as e:
        logger.error(f"[ROOM PREVIEW] Error: {e}")
        return jsonify({'error': str(e)}), 500

@design_bp.route('/api/track-interest', methods=['POST', 'OPTIONS'])
def track_interest():
    """Log every property/room/style click as its own interest record — never overwrites."""
    if request.method == 'OPTIONS':
        return '', 204

    try:
        data = request.get_json()
        user_id = data.get('user_id')
        client_name = data.get('client_name', 'skyline')
        property_section = data.get('property_section')
        room_type = data.get('room_type')
        style = data.get('style')

        if not user_id:
            return jsonify({'error': 'user_id is required'}), 400
        if not supabase:
            return jsonify({'error': 'Database not configured'}), 500

        supabase.table('user_property_interests').insert({
            'user_id': user_id,
            'client_name': client_name,
            'property_section': property_section,
            'room_type': room_type,
            'style': style
        }).execute()

        return jsonify({'success': True}), 200

    except Exception as e:
        logger.error(f"[TRACK_INTEREST] Error: {e}")
        return jsonify({'error': 'Failed to log interest'}), 500

    @design_bp.route('/api/flat-types/<client_name>', methods=['GET'])
def get_flat_types(client_name):
    try:
        VALID_CLIENTS = ['skyline', 'ellington', 'sothebys']
        if client_name not in VALID_CLIENTS:
            return jsonify({'error': f'Invalid client. Must be one of: {VALID_CLIENTS}'}), 400

        sections = supabase.table('property_sections') \
            .select('section_key, section_name, property_type, display_order') \
            .eq('client_name', client_name) \
            .eq('is_active', True) \
            .order('display_order') \
            .execute().data or []

        flat_types = [{
            'id': s['section_key'],
            'name': s.get('property_type') or s['section_name'],
        } for s in sections]

        return jsonify({'success': True, 'client_name': client_name, 'flat_types': flat_types}), 200

    except Exception as e:
        logger.error(f"[FLAT TYPES] Error: {e}")
        return jsonify({'error': 'Failed to load flat types'}), 500