
import os
import logging

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazily creates the Twilio client so importing this module
    never fails just because env vars aren't set yet."""
    global _client
    if _client is None:
        from twilio.rest import Client
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        if not account_sid or not auth_token:
            raise RuntimeError(
                "TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN not set in environment"
            )
        _client = Client(account_sid, auth_token)
    return _client


def send_sms_message(phone, message):
    """
    Sends an SMS to `phone` (must include country code, e.g. '+919876543210').
    Raises an exception on failure — outreach_dispatch.py catches it and
    logs the error to outreach_logs, so no try/except is needed here.
    """
    from_number = os.getenv('TWILIO_PHONE_NUMBER')
    if not from_number:
        raise RuntimeError("TWILIO_PHONE_NUMBER not set in environment")

    client = _get_client()

    result = client.messages.create(
        body=message,
        from_=from_number,
        to=phone
    )

    logger.info(f"[SMS] Sent to {phone}, sid={result.sid}, status={result.status}")
    return result.sid