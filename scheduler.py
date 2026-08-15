import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from supabase import Client as SupabaseClient

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None


def schedule_user_notification(user_id, phone_number, country_code, delay_minutes, supabase: SupabaseClient):
    """
    Schedule a notification for a user
    Called immediately after registration
    
    Args:
        user_id: User UUID
        phone_number: User's phone number
        country_code: Country code (e.g., 'IN')
        delay_minutes: Delay in minutes (usually 30)
        supabase: Supabase client
    """
    try:
        scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        
        notification_data = {
            'user_id': user_id,
            'phone_number': phone_number,
            'country_code': country_code,
            'scheduled_for': scheduled_time.isoformat(),
            'status': 'pending'
        }
        
        result = supabase.table('scheduled_notifications').insert(notification_data).execute()
        
        if result.data:
            logger.info(f"[SCHEDULER] ✅ Scheduled notification for user {user_id} at {scheduled_time.strftime('%H:%M:%S')}")
            return True
        else:
            logger.error(f"[SCHEDULER] ❌ Failed to schedule notification for user {user_id}")
            return False
            
    except Exception as e:
        logger.error(f"[SCHEDULER] ❌ Error scheduling notification: {e}")
        return False


def process_pending_notifications(supabase: SupabaseClient):
    """
    Background job that runs every minute
    Finds notifications that are due and sends them
    """
    try:
        current_time = datetime.now()
        
        # Find notifications due to send (scheduled_for <= now AND status = pending)
        result = supabase.table('scheduled_notifications')\
            .select('*')\
            .eq('status', 'pending')\
            .lte('scheduled_for', current_time.isoformat())\
            .execute()
        
        pending = result.data if result.data else []
        
        if len(pending) > 0:
            logger.info(f"[SCHEDULER] Found {len(pending)} notification(s) to process")
        
        # Import here to avoid circular dependency
        from whatsapp_service import send_notification_to_user
        
        for notification in pending:
            user_id = notification.get('user_id')
            notification_id = notification.get('id')
            
            logger.info(f"[SCHEDULER] Processing notification {notification_id} for user {user_id}")
            
            # Send notification
            result = send_notification_to_user(user_id, supabase)
            
            if result.get('success'):
                logger.info(f"[SCHEDULER] ✅ Successfully sent notification {notification_id}")
            else:
                logger.error(f"[SCHEDULER] ❌ Failed to send notification {notification_id}: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"[SCHEDULER] ❌ Error processing notifications: {e}")


def init_scheduler(supabase: SupabaseClient):
    """
    Initialize APScheduler
    Called once when Flask app starts
    """
    global scheduler
    
    if scheduler is not None:
        logger.warning("[SCHEDULER] Scheduler already initialized")
        return scheduler
    
    scheduler = BackgroundScheduler(daemon=True)
    
    # Add job: Check every 1 minute for pending notifications
    scheduler.add_job(
        func=lambda: process_pending_notifications(supabase),
        trigger=IntervalTrigger(minutes=1),
        id='process_whatsapp_notifications',
        name='Process pending WhatsApp/SMS notifications',
        replace_existing=True
    )
    
    logger.info("[SCHEDULER] ✅ Scheduler initialized (checks every 1 minute)")
    return scheduler


def start_scheduler():
    """Start the background scheduler"""
    global scheduler
    
    if scheduler is None:
        logger.error("[SCHEDULER] Cannot start - scheduler not initialized")
        return False
    
    if not scheduler.running:
        scheduler.start()
        logger.info("[SCHEDULER] ✅ Background scheduler started")
        return True
    else:
        logger.warning("[SCHEDULER] Scheduler already running")
        return False


def shutdown_scheduler():
    """Gracefully shutdown scheduler (called on app exit)"""
    global scheduler
    
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("[SCHEDULER] Scheduler shut down gracefully")