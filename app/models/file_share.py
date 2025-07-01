from datetime import datetime
from app import db

# Association table for file sharing
file_shares = db.Table('file_shares',
    db.Column('file_id', db.Integer, db.ForeignKey('file.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('shared_at', db.DateTime, default=datetime.utcnow),
    db.Column('share_note', db.String(255), nullable=True)
)

# Create a proper FileShare model for easier querying
class FileShare(db.Model):
    __tablename__ = 'file_share'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow)
    share_note = db.Column(db.String(255), nullable=True)
    
    # Relationships
    file = db.relationship('File', backref=db.backref('shares', lazy='dynamic'))
    user = db.relationship('User', backref=db.backref('received_shares', lazy='dynamic'))
    
    def __repr__(self):
        return f'<FileShare {self.file_id} shared with {self.user_id}>'
