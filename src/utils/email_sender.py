import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("EMAIL_HOST")
SMTP_PORT = int(os.getenv("EMAIL_PORT", 587)) 
SMTP_USER = os.getenv("EMAIL_USER")
SMTP_PASS = os.getenv("EMAIL_PASS")

def send_email(to_address: str, subject: str, body_html: str):
    """
    Sends an email using the configured SMTP settings from the .env file.

    Args:
        to_address: The recipient's email address.
        subject: The subject line of the email.
        body_html: The HTML content of the email body.
    """
    
    if not all([SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS]):
        print("\n--- EMAIL ERROR ---")
        print("Email configuration is missing. Please check your .env file.")
        print("Required variables: EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASS")
        print("---------------------\n")
        raise ValueError("Email configuration is incomplete.")

    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = SMTP_USER
        msg['To'] = to_address
        msg['Subject'] = subject

        msg.attach(MIMEText(body_html, 'html'))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()  
            server.login(SMTP_USER, SMTP_PASS) 
            server.send_message(msg) 
            print(f"Email sent successfully to {to_address}")

    except Exception as e:
        print(f"Failed to send email to {to_address}: {e}")
        raise

