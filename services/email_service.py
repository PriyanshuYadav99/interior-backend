"""
Transactional email — currently just the post-registration welcome email.
Moved verbatim from app.py's send_welcome_email function.
"""

import logging
import smtplib
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config.settings import EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD, EMAIL_FROM, FRONTEND_URL

logger = logging.getLogger(__name__)


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
