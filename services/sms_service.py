"""
sms_service.py — SMS sending via Twilio.

Setup:
1. pip install twilio
2. Add to your .env:
     TWILIO_ACCOUNT_SID=your_account_sid
     TWILIO_AUTH_TOKEN=your_auth_token
     TWILIO_PHONE_NUMBER=+1xxxxxxxxxx   (the number Twilio gave you)

Note: Sending SMS to Indian numbers (+91) via Twilio requires DLT
(Distributed Ledger Technology) registration with Indian telecom
authorities — a template/sender-ID approval process done through
Twilio's console. Until that's approved, sends to +91 numbers will
fail or be blocked. If your leads are mostly India-based, consider
MSG91 or Gupshup instead, which handle DLT registration directly.
"""

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