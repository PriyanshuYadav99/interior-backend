# import os
# import logging
# from datetime import datetime
# from twilio.rest import Client
# from twilio.base.exceptions import TwilioRestException
# from supabase import Client as SupabaseClient

# logger = logging.getLogger(__name__)

# # Twilio Configuration
# TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
# TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
# TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
# FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5177/")

# # Initialize Twilio client
# twilio_client = None
# if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
#     try:
#         twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
#         logger.info("[TWILIO] Client initialized successfully")
#     except Exception as e:
#         logger.error(f"[TWILIO] Failed to initialize: {e}")
# else:
#     logger.warning("[TWILIO] Credentials not configured")


# def format_phone_number(phone, country_code='IN'):
#     """Format phone number for Twilio (E.164 format)"""
#     # Remove any spaces, dashes, parentheses
#     phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
#     # Remove leading zeros
#     phone = phone.lstrip('0')
    
#     # Add country code if not present
#     if not phone.startswith('+'):
#         country_codes = {
#             'IN': '+91',
#             'US': '+1',
#             'UK': '+44',
#             'AE': '+971'
#         }
#         phone = country_codes.get(country_code, '+91') + phone
    
#     return phone


# def check_whatsapp_availability(phone_number):
#     """
#     Check if phone number has WhatsApp using Twilio Lookup API
#     Returns: True if WhatsApp available, False otherwise
#     """
#     try:
#         if not twilio_client:
#             logger.error("[WHATSAPP] Twilio client not initialized")
#             return False
        
#         formatted_phone = format_phone_number(phone_number)
#         logger.info(f"[WHATSAPP] Checking availability for {formatted_phone}")
        
#         # Use Twilio Lookup API
#         phone_info = twilio_client.lookups.v1.phone_numbers(formatted_phone).fetch()
        
#         # If we get here without error, phone is valid
#         # For trial accounts, we'll assume WhatsApp is available
#         # In production, you can check carrier info
#         logger.info(f"[WHATSAPP] ✅ Phone validated: {formatted_phone}")
#         return True
        
#     except TwilioRestException as e:
#         logger.error(f"[WHATSAPP] ❌ Lookup failed: {e}")
#         return False
#     except Exception as e:
#         logger.error(f"[WHATSAPP] ❌ Error checking availability: {e}")
#         return False


# def format_message_short(user_name, generation_count, user_id):
#     """Format short message with link (Option B)"""
#     gallery_url = f"{FRONTEND_URL}gallery/{user_id}"
    
#     message = f"""Hi {user_name}! 🎨

# Your {generation_count} AI interior design{"s" if generation_count != 1 else ""} {"are" if generation_count != 1 else "is"} ready!

# View & download all your designs:
# {gallery_url}

# Generate more stunning designs:
# {FRONTEND_URL}

# - AI Interior Design Team"""
    
#     return message


# def send_whatsapp_message(phone_number, message, country_code='IN'):
#     """Send WhatsApp message via Twilio"""
#     try:
#         if not twilio_client:
#             logger.error("[WHATSAPP] Twilio client not initialized")
#             return {'success': False, 'error': 'Twilio not configured'}
        
#         formatted_phone = format_phone_number(phone_number, country_code)
        
#         # Send WhatsApp message
#         twilio_message = twilio_client.messages.create(
#             from_=TWILIO_WHATSAPP_NUMBER,
#             body=message,
#             to=f'whatsapp:{formatted_phone}'
#         )
        
#         logger.info(f"[WHATSAPP] ✅ Message sent: SID={twilio_message.sid}")
        
#         return {
#             'success': True,
#             'method': 'whatsapp',
#             'message_sid': twilio_message.sid,
#             'to': formatted_phone
#         }
        
#     except TwilioRestException as e:
#         logger.error(f"[WHATSAPP] ❌ Failed to send: {e}")
#         return {'success': False, 'error': str(e)}
#     except Exception as e:
#         logger.error(f"[WHATSAPP] ❌ Error: {e}")
#         return {'success': False, 'error': str(e)}


# def send_sms_message(phone_number, message, country_code='IN'):
#     """Send SMS as fallback"""
#     try:
#         if not twilio_client:
#             logger.error("[SMS] Twilio client not initialized")
#             return {'success': False, 'error': 'Twilio not configured'}
        
#         formatted_phone = format_phone_number(phone_number, country_code)
        
#         # Shorten message for SMS (160 char limit awareness)
#         sms_message = message[:300]  # Keep it reasonable
        
#         # Send SMS
#         twilio_message = twilio_client.messages.create(
#             from_=TWILIO_PHONE_NUMBER,
#             body=sms_message,
#             to=formatted_phone
#         )
        
#         logger.info(f"[SMS] ✅ Message sent: SID={twilio_message.sid}")
        
#         return {
#             'success': True,
#             'method': 'sms',
#             'message_sid': twilio_message.sid,
#             'to': formatted_phone
#         }
        
#     except TwilioRestException as e:
#         logger.error(f"[SMS] ❌ Failed to send: {e}")
#         return {'success': False, 'error': str(e)}
#     except Exception as e:
#         logger.error(f"[SMS] ❌ Error: {e}")
#         return {'success': False, 'error': str(e)}


# def send_notification_to_user(user_id, supabase: SupabaseClient):
#     """
#     Main function: Send WhatsApp/SMS notification to user
#     Called by scheduler after 10 minutes of registration
#     """
#     try:
#         logger.info(f"[NOTIFICATION] Starting process for user_id: {user_id}")
        
#         # Step 1: Get user data
#         user_result = supabase.table('users').select('*').eq('id', user_id).execute()
        
#         if not user_result.data:
#             logger.error(f"[NOTIFICATION] User not found: {user_id}")
#             return {'success': False, 'error': 'User not found'}
        
#         user = user_result.data[0]
#         user_name = user.get('full_name', 'there')
#         phone_number = user.get('phone_number')
#         country_code = user.get('country_code', 'IN')
        
#         if not phone_number:
#             logger.error(f"[NOTIFICATION] No phone number for user: {user_id}")
#             return {'success': False, 'error': 'No phone number'}
        
#         # Step 2: Check if already sent
#         if user.get('whatsapp_notification_sent'):
#             logger.info(f"[NOTIFICATION] Already sent for user: {user_id}")
#             return {'success': False, 'error': 'Already sent'}
        
#         # Step 3: Count user's generations
#         generations_result = supabase.table('user_generations').select('*', count='exact').eq('user_id', user_id).execute()
#         generation_count = generations_result.count if generations_result.count else 0
        
#         logger.info(f"[NOTIFICATION] Found {generation_count} generations for user: {user_id}")
        
#         # Step 4: Format message
#         message = format_message_short(user_name, generation_count, user_id)
        
#         # Step 5: Check WhatsApp availability
#         has_whatsapp = check_whatsapp_availability(phone_number)
        
#         # Step 6: Send message
#         if has_whatsapp:
#             logger.info(f"[NOTIFICATION] Sending WhatsApp to {phone_number}")
#             result = send_whatsapp_message(phone_number, message, country_code)
#         else:
#             logger.info(f"[NOTIFICATION] WhatsApp not available, sending SMS to {phone_number}")
#             result = send_sms_message(phone_number, message, country_code)
        
#         # Step 7: Update database
#         if result.get('success'):
#             # Update user record
#             supabase.table('users').update({
#                 'whatsapp_notification_sent': True,
#                 'notification_sent_at': datetime.now().isoformat()
#             }).eq('id', user_id).execute()
            
#             # Update scheduled notification
#             supabase.table('scheduled_notifications').update({
#                 'status': 'sent',
#                 'delivery_method': result.get('method'),
#                 'sent_at': datetime.now().isoformat()
#             }).eq('user_id', user_id).eq('status', 'pending').execute()
            
#             logger.info(f"[NOTIFICATION] ✅ Successfully sent via {result.get('method')} to {phone_number}")
#         else:
#             # Mark as failed
#             supabase.table('scheduled_notifications').update({
#                 'status': 'failed',
#                 'error_message': result.get('error')
#             }).eq('user_id', user_id).eq('status', 'pending').execute()
            
#             logger.error(f"[NOTIFICATION] ❌ Failed to send: {result.get('error')}")
        
#         return result
        
#     except Exception as e:
#         logger.error(f"[NOTIFICATION] ❌ Error: {e}")
        
#         # Mark as failed in DB
#         try:
#             supabase.table('scheduled_notifications').update({
#                 'status': 'failed',
#                 'error_message': str(e)
#             }).eq('user_id', user_id).eq('status', 'pending').execute()
#         except:
#             pass
        
#         return {'success': False, 'error': str(e)}
import os
import logging
import requests
from datetime import datetime
from supabase import Client as SupabaseClient

logger = logging.getLogger(__name__)

# Meta WhatsApp Configuration
META_PHONE_NUMBER_ID = os.getenv("META_PHONE_NUMBER_ID")
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN")
META_API_VERSION = os.getenv("META_WHATSAPP_API_VERSION", "v21.0")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5177/")

# Validate configuration
if META_PHONE_NUMBER_ID and META_ACCESS_TOKEN:
    logger.info("[META WHATSAPP] Configuration loaded successfully")
else:
    logger.warning("[META WHATSAPP] Credentials not configured")


def format_phone_number(phone, country_code='IN'):
    """
    Format phone number for WhatsApp (no + prefix needed for Meta API)
    Example: 919876543210
    """
    phone = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    phone = phone.lstrip('0').lstrip('+')
    
    country_codes = {
        'IN': '91',
        'US': '1',
        'UK': '44',
        'GB': '44',
        'CA': '1',
        'AU': '61',
        'AE': '971'
    }
    
    if not any(phone.startswith(code) for code in country_codes.values()):
        phone = country_codes.get(country_code, '91') + phone
    
    return phone


def format_message_short(user_name, generation_count, user_id):
    """Format short WhatsApp message with links"""
    gallery_url = f"{FRONTEND_URL}gallery/{user_id}"
    
    message = f"""Hi {user_name}! 🎨

Your {generation_count} AI interior design{"s" if generation_count != 1 else ""} {"are" if generation_count != 1 else "is"} ready!

View & download:
{gallery_url}

Generate more:
{FRONTEND_URL}

- AI Interior Design Team"""
    
    return message


def send_whatsapp_message(phone_number, message, country_code='IN'):
    """
    Send WhatsApp message using Meta Cloud API
    Uses 'hello_world' template for now (you'll create custom templates later)
    """
    try:
        if not META_PHONE_NUMBER_ID or not META_ACCESS_TOKEN:
            logger.error("[META WHATSAPP] Credentials not configured")
            return {'success': False, 'error': 'WhatsApp not configured'}
        
        formatted_phone = format_phone_number(phone_number, country_code)
        
        url = f"https://graph.facebook.com/{META_API_VERSION}/{META_PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {META_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # For now, using hello_world template (works immediately)
        # Later you'll create custom templates with variables
        payload = {
            "messaging_product": "whatsapp",
            "to": formatted_phone,
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {
                    "code": "en_US"
                }
            }
        }
        
        logger.info(f"[META WHATSAPP] Sending to {formatted_phone}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"[META WHATSAPP] ✅ Message sent: {result}")
            
            return {
                'success': True,
                'method': 'whatsapp',
                'message_id': result.get('messages', [{}])[0].get('id'),
                'to': formatted_phone
            }
        else:
            error_data = response.json()
            logger.error(f"[META WHATSAPP] ❌ Failed: {error_data}")
            
            return {
                'success': False,
                'error': error_data.get('error', {}).get('message', 'Unknown error'),
                'error_code': error_data.get('error', {}).get('code')
            }
        
    except requests.exceptions.Timeout:
        logger.error("[META WHATSAPP] ❌ Request timeout")
        return {'success': False, 'error': 'Request timeout'}
    except Exception as e:
        logger.error(f"[META WHATSAPP] ❌ Error: {e}")
        return {'success': False, 'error': str(e)}


def send_sms_message(phone_number, message, country_code='IN'):
    """
    SMS fallback - NOT NEEDED for Meta WhatsApp
    Keep this function for compatibility but log that it's not used
    """
    logger.info("[SMS] SMS fallback not implemented - using WhatsApp only")
    return {'success': False, 'error': 'SMS not configured - using WhatsApp only'}


def send_notification_to_user(user_id, supabase: SupabaseClient):
    """
    Main function: Send WhatsApp notification to user
    Called by scheduler after 2 minutes of registration
    """
    try:
        logger.info(f"[NOTIFICATION] Starting for user_id: {user_id}")
        
        # Get user data
        user_result = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if not user_result.data:
            logger.error(f"[NOTIFICATION] User not found: {user_id}")
            return {'success': False, 'error': 'User not found'}
        
        user = user_result.data[0]
        user_name = user.get('full_name', 'there')
        phone_number = user.get('phone_number')
        country_code = user.get('country_code', 'IN')
        
        if not phone_number:
            logger.error(f"[NOTIFICATION] No phone number for user: {user_id}")
            return {'success': False, 'error': 'No phone number'}
        
        # Check if already sent
        if user.get('whatsapp_notification_sent'):
            logger.info(f"[NOTIFICATION] Already sent for user: {user_id}")
            return {'success': False, 'error': 'Already sent'}
        
        # Count user's generations
        generations_result = supabase.table('user_generations')\
            .select('*', count='exact')\
            .eq('user_id', user_id)\
            .execute()
        
        generation_count = generations_result.count if generations_result.count else 0
        
        logger.info(f"[NOTIFICATION] Found {generation_count} generations")
        
        # Format message
        message = format_message_short(user_name, generation_count, user_id)
        
        # Send WhatsApp message
        logger.info(f"[NOTIFICATION] Sending WhatsApp to {phone_number}")
        result = send_whatsapp_message(phone_number, message, country_code)
        
        # Update database
        if result.get('success'):
            # Update user record
            supabase.table('users').update({
                'whatsapp_notification_sent': True,
                'notification_sent_at': datetime.now().isoformat()
            }).eq('id', user_id).execute()
            
            # Update scheduled notification
            supabase.table('scheduled_notifications').update({
                'status': 'sent',
                'delivery_method': 'whatsapp',
                'sent_at': datetime.now().isoformat()
            }).eq('user_id', user_id).eq('status', 'pending').execute()
            
            logger.info(f"[NOTIFICATION] ✅ Successfully sent to {phone_number}")
        else:
            # Mark as failed
            supabase.table('scheduled_notifications').update({
                'status': 'failed',
                'error_message': result.get('error')
            }).eq('user_id', user_id).eq('status', 'pending').execute()
            
            logger.error(f"[NOTIFICATION] ❌ Failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"[NOTIFICATION] ❌ Error: {e}")
        
        # Mark as failed in DB
        try:
            supabase.table('scheduled_notifications').update({
                'status': 'failed',
                'error_message': str(e)
            }).eq('user_id', user_id).eq('status', 'pending').execute()
        except:
            pass
        
        return {'success': False, 'error': str(e)}