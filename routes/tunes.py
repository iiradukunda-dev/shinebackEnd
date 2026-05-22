from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.tune import Tune

tunes_bp = Blueprint('tunes', __name__)

@tunes_bp.route('/tunes', methods=['GET'])
def get_tunes():
    """Get all active tunes"""
    try:
        tunes = Tune.query.filter_by(is_active=True).order_by(Tune.release_date.asc()).all()
        return jsonify({
            'success': True,
            'tunes': [tune.to_dict() for tune in tunes]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching tunes: {str(e)}'
        }), 500

@tunes_bp.route('/tunes', methods=['POST'])
def create_tune():
    """Create a new tune (Admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'genre', 'release_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Parse date
        try:
            release_date = datetime.strptime(data['release_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Validate cover_image_data if provided
        if 'cover_image_data' in data and data['cover_image_data']:
            if not isinstance(data['cover_image_data'], str):
                return jsonify({
                    'success': False,
                    'message': 'Invalid image upload format'
                }), 400
        
        # Create new tune
        tune = Tune(
            title=data['title'],
            artist=data.get('artist', 'Shining Ministries'),
            genre=data['genre'],
            release_date=release_date,
            status=data.get('status', 'Coming Soon'),
            description=data.get('description', ''),
            cover_image_url=data.get('cover_image_url', ''),
            cover_image_name=data.get('cover_image_name'),
            cover_image_data=data.get('cover_image_data'),
            audio_url=data.get('audio_url', '')
        )
        
        db.session.add(tune)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tune created successfully',
            'tune': tune.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating tune: {str(e)}'
        }), 500

@tunes_bp.route('/tunes/<int:tune_id>', methods=['PUT'])
def update_tune(tune_id):
    """Update an existing tune (Admin only)"""
    try:
        tune = Tune.query.get_or_404(tune_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            tune.title = data['title']
        if 'artist' in data:
            tune.artist = data['artist']
        if 'genre' in data:
            tune.genre = data['genre']
        if 'release_date' in data:
            try:
                tune.release_date = datetime.strptime(data['release_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        if 'status' in data:
            tune.status = data['status']
        if 'description' in data:
            tune.description = data['description']
        if 'cover_image_url' in data:
            tune.cover_image_url = data['cover_image_url']
        if 'cover_image_data' in data and data['cover_image_data']:
            if not isinstance(data['cover_image_data'], str):
                return jsonify({
                    'success': False,
                    'message': 'Invalid image upload format'
                }), 400
            tune.cover_image_data = data['cover_image_data']
            tune.cover_image_name = data.get('cover_image_name')
        if 'audio_url' in data:
            tune.audio_url = data['audio_url']
        if 'is_active' in data:
            tune.is_active = data['is_active']
        
        tune.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tune updated successfully',
            'tune': tune.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating tune: {str(e)}'
        }), 500

@tunes_bp.route('/tunes/<int:tune_id>', methods=['DELETE'])
def delete_tune(tune_id):
    """Delete a tune (Admin only)"""
    try:
        tune = Tune.query.get_or_404(tune_id)
        tune.is_active = False
        tune.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Tune deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting tune: {str(e)}'
        }), 500

@tunes_bp.route('/tunes/<int:tune_id>', methods=['GET'])
def get_tune(tune_id):
    """Get a specific tune"""
    try:
        tune = Tune.query.get_or_404(tune_id)
        return jsonify({
            'success': True,
            'tune': tune.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching tune: {str(e)}'
        }), 500

@tunes_bp.route('/tunes/upcoming', methods=['GET'])
def get_upcoming_tunes():
    """Get upcoming tunes (not yet released)"""
    try:
        today = datetime.now().date()
        tunes = Tune.query.filter(
            Tune.is_active == True,
            Tune.release_date >= today
        ).order_by(Tune.release_date.asc()).all()
        
        return jsonify({
            'success': True,
            'tunes': [tune.to_dict() for tune in tunes]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching upcoming tunes: {str(e)}'
        }), 500

