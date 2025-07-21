import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from twilio.rest import Client
from flask import current_app
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_email_notification(recipient_email, subject, body):
    """
    Send email notification using SMTP
    Args:
        recipient_email (str): Email address of recipient
        subject (str): Email subject
        body (str): Email body content
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        # Get email config from environment variables
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', 587))
        sender_email = os.getenv('EMAIL_USER')
        email_password = os.getenv('EMAIL_PASSWORD')

        if not all([sender_email, email_password]):
            logger.error("Email credentials not configured")
            return False

        # Create message
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, email_password)
            server.send_message(msg)
        
        logger.info(f"Email sent to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

def send_sms_notification(phone_number, message):
    """
    Send SMS notification using Twilio
    Args:
        phone_number (str): Recipient phone number with country code
        message (str): SMS message content
    Returns:
        bool: True if sent successfully, False otherwise
    """
    try:
        # Get Twilio config from environment variables
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        twilio_number = os.getenv('TWILIO_PHONE_NUMBER')

        if not all([account_sid, auth_token, twilio_number]):
            logger.error("Twilio credentials not configured")
            return False

        # Send SMS
        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message,
            from_=twilio_number,
            to=phone_number
        )
        
        logger.info(f"SMS sent to {phone_number}")
        return True

    except Exception as e:
        logger.error(f"Failed to send SMS: {str(e)}")
        return False

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Basic phone number validation (E.164 format)"""
    import re
    pattern = r'^\+[1-9]\d{1,14}$'
    return re.match(pattern, phone) is not None
