from datetime import datetime
from app import db
from app.models.file_share import file_shares

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    drive_file_id = db.Column(db.String(255), nullable=True)  # Google Drive file ID
    mime_type = db.Column(db.String(128), nullable=True)
    size = db.Column(db.Integer, nullable=True)  # File size in bytes
    encrypted = db.Column(db.Boolean, default=True)
    encryption_hint = db.Column(db.String(255), nullable=True)  # Optional hint for the encryption password
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship for shared files
    shared_with = db.relationship('User', 
                                 secondary=file_shares,
                                 backref=db.backref('shared_files', lazy='dynamic'),
                                 lazy='dynamic')
    
    def __repr__(self):
        return f'<File {self.filename}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.original_filename,
            'mime_type': self.mime_type,
            'size': self.size,
            'encrypted': self.encrypted,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'encryption_hint': self.encryption_hint
        }
    
    def is_shared_with(self, user_id):
        """Check if file is shared with a specific user"""
        return self.shared_with.filter_by(id=user_id).first() is not None
    
    def share_with(self, user_id, note=None):
        """Share file with another user"""
        from app.models.user import User
        user = User.query.get(user_id)
        if user and not self.is_shared_with(user_id):
            self.shared_with.append(user)
            return True
        return False
    
    def unshare_with(self, user_id):
        """Unshare file with a user"""
        from app.models.user import User
        user = User.query.get(user_id)
        if user and self.is_shared_with(user_id):
            self.shared_with.remove(user)
            return True
        return False
