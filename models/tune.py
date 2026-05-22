from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from src.models.user import db

class Tune(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist = db.Column(db.String(200), nullable=False, default='Shining Ministries')
    genre = db.Column(db.String(100), nullable=False)
    release_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='Coming Soon')  # Coming Soon, In Production, Recording, Released
    description = db.Column(db.Text, nullable=True)
    cover_image_url = db.Column(db.String(500), nullable=True)
    cover_image_name = db.Column(db.String(255), nullable=True)
    cover_image_data = db.Column(db.Text, nullable=True)  # Base64 encoded image
    audio_url = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f'<Tune {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'artist': self.artist,
            'genre': self.genre,
            'release_date': self.release_date.isoformat() if self.release_date else None,
            'status': self.status,
            'description': self.description,
            'cover_image_url': self.cover_image_url,
            'cover_image_name': self.cover_image_name,
            'cover_image_data': self.cover_image_data,
            'audio_url': self.audio_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

