# Standard library imports first
import os
import sys
import logging
from datetime import datetime

# Third-party imports
from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, jsonify
from flask_cors import CORS

from config.settings import OPENAI_API_KEY, REPLICATE_API_TOKEN, EMAIL_USER, EMAIL_PASSWORD, PORT
from services.external_clients import supabase
from services.scheduler import init_scheduler, start_scheduler
from services.whatsapp_service import send_whatsapp_message, send_sms_message, send_notification_to_user

from routes.design_routes import design_bp
from routes.life_echo_routes import scenario_bp as Life_bp
from routes.virtual_tour_routes import virtual_tour_bp
from routes.admin_routes import admin_bp
from routes.activity_routes import activity_bp
from routes.ai_routes import ai_bp
from routes.news_routes import news_bp

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

if REPLICATE_API_TOKEN:
    logger.info("[SETUP] Replicate API configured successfully")
else:
    logger.warning("[SETUP] REPLICATE_API_TOKEN not set - Image generation will not work")

# ============================================================
# FLASK APP INITIALIZATION
# ============================================================
app = Flask(__name__)

# Configure CORS - Simple and working
CORS(app, resources={
    r"/api/*": {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["Content-Type"],
        "supports_credentials": False,
        "max_age": 3600
    }
})


@app.before_request
def handle_preflight():
    """Handle OPTIONS requests"""
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
        response.headers['Access-Control-Max-Age'] = '3600'
        return response, 200


@app.after_request
def after_request(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Requested-With'
    response.headers['Access-Control-Max-Age'] = '3600'
    return response

# ============================================================
# REGISTER BLUEPRINTS
# ============================================================
logger.info("=" * 70)
logger.info("[BLUEPRINT] Registering blueprints...")

app.register_blueprint(design_bp)
app.register_blueprint(Life_bp)
app.register_blueprint(news_bp)
app.register_blueprint(virtual_tour_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(activity_bp)
app.register_blueprint(ai_bp)

logger.info("[BLUEPRINT] ✅ All blueprints registered!")

with app.app_context():
    logger.info("[ROUTES] All registered routes:")
    for rule in app.url_map.iter_rules():
        logger.info(f"  {rule.rule} -> {rule.endpoint}")

logger.info("=" * 70)

# ============================================================
# DEBUG / SCHEDULER ENDPOINTS
# ============================================================
# These stay here (rather than in routes/) because `app_scheduler` below
# is only ever assigned inside the `if __name__ == '__main__':` block at
# the bottom of this file — see the note there. Keeping these routes in
# the same module keeps that (pre-existing) global lookup working exactly
# as it did before this reorg; moving them to a separate file would need
# either duplicating that scoping quirk elsewhere or fixing it outright,
# and this pass is a structure-only move, not a behavior change.

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


# ============================================================
# TEST ENDPOINT - For debugging WhatsApp (REMOVE IN PRODUCTION)
# ============================================================

@app.route('/api/test-whatsapp-direct', methods=['POST'])
def test_whatsapp_direct():
    """Direct test - send WhatsApp/SMS to your phone NOW"""
    try:
        data = request.get_json()
        phone = data.get('phone_number')

        if not phone:
            return jsonify({'error': 'phone_number required'}), 400

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

    # NOTE (found during restructuring, intentionally left unchanged):
    # `app_scheduler` is only ever assigned in this __main__ block. This
    # file is served in production via gunicorn per the Procfile
    # (`gunicorn app:app`), and gunicorn never executes this block, since
    # __name__ is the module name ('app'), not '__main__', when imported
    # that way. That means in production the scheduler is likely never
    # actually initialized/started, and /api/scheduler-status will always
    # report "Scheduler not initialized". This predates this restructure;
    # flagged in the README rather than silently changed here.

    # STEP 2: Initialize scheduler
    if supabase:
        app_scheduler = init_scheduler(supabase)
        start_scheduler()
        logger.info("[SETUP] ✅ Scheduler initialized AND STARTED")
    else:
        logger.warning("[SETUP] ⚠️ Supabase not configured - scheduler disabled")
        app_scheduler = None

    # STEP 3: Start server
    port = PORT

    logger.info("=" * 70)
    logger.info("🚀 Starting AI Interior Design Backend v10.0.0")
    logger.info("=" * 70)
    logger.info(f"Port: {port}")
    logger.info(f"OpenAI: {'✓' if OPENAI_API_KEY else '✗'}")
    logger.info(f"Replicate: {'✓' if REPLICATE_API_TOKEN else '✗'}")
    logger.info(f"Email: {'✓' if EMAIL_USER and EMAIL_PASSWORD else '✗'}")
    logger.info(f"Supabase: {'✓' if supabase else '✗'}")
    logger.info(f"Scenario Module: ✓")
    logger.info("=" * 70)

    # Set debug=True for development (shows errors) — unchanged from the
    # original; this only runs under `python app.py` directly, never under
    # gunicorn, so it doesn't affect the Procfile-based production deploy.
    app.run(host='0.0.0.0', port=port, debug=True)
