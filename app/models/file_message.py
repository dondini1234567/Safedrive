from datetime import datetime
from app import db

class FileMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    sender = db.relationship('User', foreign_keys=[sender_id])
    recipient = db.relationship('User', foreign_keys=[recipient_id])
    filename = db.Column(db.String(255), nullable=True)   # Optional for text
    filepath = db.Column(db.String(255), nullable=True)   # Optional for text
    file_data = db.Column(db.Text, nullable=True)         # Can store base64 or plain text
    
    is_file = db.Column(db.Boolean, default=False)        # Distinguish file vs message
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
