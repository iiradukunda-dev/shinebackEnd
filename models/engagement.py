from datetime import datetime
from src.models.user import db


class ContactMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='New')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class TuneNotification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tune_id = db.Column(db.Integer, nullable=True)
    tune_title = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Subscribed')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'tune_id': self.tune_id,
            'tune_title': self.tune_title,
            'email': self.email,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
