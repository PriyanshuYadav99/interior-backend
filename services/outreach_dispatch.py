"""
outreach_dispatch.py — single place that actually sends a message
on a given channel. Used by both properties_routes.py (bulk) and
ai_routes.py (single lead) so the sending logic only lives once.
"""

import logging

logger = logging.getLogger(__name__)


def dispatch_message(user, channel, message):
    """
    Sends `message` to `user` on `channel` ('sms' | 'whatsapp' | 'email').
    Returns (success: bool, error: str | None).

    Wire these into your real providers:
      - services/whatsapp_service.py -> send_whatsapp_message(phone, message)
      - services/email_service.py    -> send_email(to_email, subject, body)
      - services/sms_service.py      -> NOT YET CREATED. You have no SMS
        provider in the repo (e.g. Twilio) — add one before enabling this
        channel, or hide the SMS tab on the frontend until it exists.
    """
    try:
        country_code = str(user.get('country_code', '91')).strip()
        phone_number = str(user.get('phone_number', '')).strip()

        # country_code may be stored as a numeric dialing code ('91', '1')
        # or an ISO abbreviation ('US', 'IN') depending on how the lead was
        # captured. Map the common ones; numeric values pass through as-is.
        ISO_TO_DIALING_CODE = {
            'US': '1', 'CA': '1', 'IN': '91', 'GB': '44', 'UK': '44',
            'AE': '971', 'AU': '61', 'SG': '65'
        }
        if not country_code.isdigit():
            country_code = ISO_TO_DIALING_CODE.get(country_code.upper(), country_code)

        phone = f"+{country_code}{phone_number}"

        if channel == 'whatsapp':
            from services.whatsapp_service import send_whatsapp_message
            send_whatsapp_message(phone, message)

        elif channel == 'email':
            from services.email_service import send_email
            send_email(
                to_email=user.get('email'),
                subject="An update on your property search",
                body=message
            )

        elif channel == 'sms':
            from services.sms_service import send_sms_message  # TODO: implement (Twilio, etc.)
            send_sms_message(phone, message)

        else:
            return False, f"Unknown channel: {channel}"

        return True, None

    except ModuleNotFoundError as e:
        logger.error(f"[DISPATCH] Missing service module for channel '{channel}': {e}")
        return False, f"Channel '{channel}' is not wired up yet"
    except Exception as e:
        logger.error(f"[DISPATCH] {channel} to user {user.get('id')} failed: {e}")
        return False, str(e)