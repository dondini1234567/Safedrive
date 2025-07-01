import pyotp
import os
from datetime import datetime, timedelta
from flask import current_app, render_template
from flask_mail import Message
from app import db, mail

def generate_otp(user):
    """Generate a new OTP for the user"""
    # Generate a random secret key if not exists
    if not user.otp_secret:
        user.otp_secret = pyotp.random_base32()
        db.session.commit()
    
    # Create a TOTP object
    totp = pyotp.TOTP(user.otp_secret, interval=current_app.config['OTP_EXPIRY'])
    
    # Generate the OTP
    otp = totp.now()
    
    return otp

def verify_otp(user, otp):
    """Verify the OTP for the user"""
    if not user.otp_secret:
        return False
    
    # Create a TOTP object
    totp = pyotp.TOTP(user.otp_secret, interval=current_app.config['OTP_EXPIRY'])
    
    # Verify the OTP
    return totp.verify(otp)

def send_otp_email(user, otp):
    """Send OTP to user's email"""
    msg = Message(
        
        subject="SafeDrive - Email Verification",
        sender="dinisaufee2002@gmail.com",  # <-- Explicit sender here
        recipients=[user.email]
    )
    
    msg.body = f"""
    Hello {user.first_name or user.email},
    
    Your verification code for SafeDrive is: {otp}
    
    This code will expire in 10 minutes.
    
    If you did not request this code, please ignore this email.
    
    Best regards,
    The SafeDrive Team
    """
    
    msg.html = f"""
    <p>Hello {user.first_name or user.email},</p>
    <p>Your verification code for SafeDrive is: <strong>{otp}</strong></p>
    <p>This code will expire in 10 minutes.</p>
    <p>If you did not request this code, please ignore this email.</p>
    <p>Best regards,<br>The SafeDrive Team</p>
    """
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False