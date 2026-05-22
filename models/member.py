from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db
import uuid

class Member(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    musical_experience = db.Column(db.Text, nullable=True)
    motivation = db.Column(db.Text, nullable=True)
    member_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    qr_code_data = db.Column(db.Text, nullable=True)  # Base64 encoded QR code image
    photo_name = db.Column(db.String(255), nullable=True)  # Member photo filename
    photo_data = db.Column(db.Text, nullable=True)  # Base64 encoded photo image
    status = db.Column(db.String(50), nullable=False, default='Pending')  # Pending, Approved, Active, Inactive
    documents = db.Column(db.JSON, nullable=True)  # Store document metadata as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Member {self.full_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'age': self.age,
            'musical_experience': self.musical_experience,
            'motivation': self.motivation,
            'member_id': self.member_id,
            'qr_code_data': self.qr_code_data,
            'photo_name': self.photo_name,
            'photo_data': self.photo_data,
            'status': self.status,
            'documents': self.documents,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

class MemberApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    musical_experience = db.Column(db.Text, nullable=True)
    motivation = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default='Pending')  # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    reviewed_by = db.Column(db.String(200), nullable=True)
    photo_name = db.Column(db.String(255), nullable=True)
    photo_data = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<MemberApplication {self.full_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'phone': self.phone,
            'age': self.age,
            'musical_experience': self.musical_experience,
            'motivation': self.motivation,
            'status': self.status,
            'photo_name': self.photo_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewed_by': self.reviewed_by
        }

