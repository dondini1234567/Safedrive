from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import time
from app import db, login_manager
from flask import current_app, session, request
import os

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    is_verified = db.Column(db.Boolean, default=False)
    google_id = db.Column(db.String(128), unique=True, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    otp_secret = db.Column(db.String(16), nullable=True)
    # We'll handle profile image without adding a column for now
    files = db.relationship('File', backref='owner', lazy='dynamic')
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time.time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['reset_password']
        except:
            return None
        return User.query.get(id)
    
    def get_email_verification_token(self, expires_in=3600):
        return jwt.encode(
            {'verify_email': self.id, 'exp': time.time() + expires_in},
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
    
    @staticmethod
    def verify_email_token(token):
        try:
            id = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )['verify_email']
        except:
            return None
        return User.query.get(id)
        
    # Renamed method to avoid conflict with potential SQLAlchemy relationship
    def get_shared_files(self):
        from app.models.file import File
        return File.query.filter(File.shared_with.any(id=self.id)).all()
    
    def get_profile_image_url(self):
        """Get the URL for the user's profile image with cache busting"""
        # Check if a custom profile image exists for this user
        profile_images_dir = os.path.join(current_app.static_folder, 'uploads', 'profile_images')
        custom_image_path = os.path.join(profile_images_dir, f"user_{self.id}.png")
        
        if os.path.exists(custom_image_path):
            # Get file modification time for cache busting
            mod_time = int(os.path.getmtime(custom_image_path))
            return f'/static/uploads/profile_images/user_{self.id}.png?v={mod_time}'
        
        return '/static/assets/avatar.png'
