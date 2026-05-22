from flask import Blueprint, request, jsonify
from datetime import datetime
from src.models.user import db
from src.models.event import Event

events_bp = Blueprint('events', __name__)

@events_bp.route('/events', methods=['GET'])
def get_events():
    """Get all active events"""
    try:
        events = Event.query.filter_by(is_active=True).order_by(Event.date.asc()).all()
        return jsonify({
            'success': True,
            'events': [event.to_dict() for event in events]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching events: {str(e)}'
        }), 500

@events_bp.route('/events', methods=['POST'])
def create_event():
    """Create a new event (Admin only)"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'date', 'time', 'location']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Parse date
        try:
            event_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Validate image_data if provided
        if 'image_data' in data and data['image_data']:
            if not isinstance(data['image_data'], str):
                return jsonify({
                    'success': False,
                    'message': 'Invalid image upload format'
                }), 400
        
        # Create new event
        event = Event(
            title=data['title'],
            description=data.get('description', ''),
            date=event_date,
            time=data['time'],
            location=data['location'],
            image_name=data.get('image_name'),
            image_data=data.get('image_data')
        )
        
        db.session.add(event)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event created successfully',
            'event': event.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating event: {str(e)}'
        }), 500

@events_bp.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """Update an existing event (Admin only)"""
    try:
        event = Event.query.get_or_404(event_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'title' in data:
            event.title = data['title']
        if 'description' in data:
            event.description = data['description']
        if 'date' in data:
            try:
                event.date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({
                    'success': False,
                    'message': 'Invalid date format. Use YYYY-MM-DD'
                }), 400
        if 'time' in data:
            event.time = data['time']
        if 'location' in data:
            event.location = data['location']
        if 'image_data' in data and data['image_data']:
            if not isinstance(data['image_data'], str):
                return jsonify({
                    'success': False,
                    'message': 'Invalid image upload format'
                }), 400
            event.image_data = data['image_data']
            event.image_name = data.get('image_name')
        if 'is_active' in data:
            event.is_active = data['is_active']
        
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event updated successfully',
            'event': event.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating event: {str(e)}'
        }), 500

@events_bp.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """Delete an event (Admin only)"""
    try:
        event = Event.query.get_or_404(event_id)
        event.is_active = False
        event.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Event deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting event: {str(e)}'
        }), 500

@events_bp.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """Get a specific event"""
    try:
        event = Event.query.get_or_404(event_id)
        return jsonify({
            'success': True,
            'event': event.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching event: {str(e)}'
        }), 500

