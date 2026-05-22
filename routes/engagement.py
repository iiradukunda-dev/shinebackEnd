from flask import Blueprint, request, jsonify
from src.models.user import db
from src.models.engagement import ContactMessage, TuneNotification

engagement_bp = Blueprint('engagement', __name__)


def get_json_payload():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def require_fields(data, fields):
    missing = [field for field in fields if not str(data.get(field, '')).strip()]
    if missing:
        return f"Missing required field: {missing[0]}"
    return None


@engagement_bp.route('/contact-messages', methods=['POST'])
def create_contact_message():
    """Store a public contact form message."""
    try:
        data = get_json_payload()
        if data is None:
            return jsonify({'success': False, 'message': 'Invalid JSON payload'}), 400

        error = require_fields(data, ['name', 'email', 'message'])
        if error:
            return jsonify({'success': False, 'message': error}), 400

        message = ContactMessage(
            name=data['name'].strip(),
            email=data['email'].strip().lower(),
            message=data['message'].strip()
        )
        db.session.add(message)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Message received successfully',
            'contact_message': message.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error saving message: {str(e)}'}), 500


@engagement_bp.route('/contact-messages', methods=['GET'])
def get_contact_messages():
    """List contact messages for admin dashboards."""
    try:
        messages = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return jsonify({
            'success': True,
            'contact_messages': [message.to_dict() for message in messages]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching messages: {str(e)}'}), 500


@engagement_bp.route('/tune-notifications', methods=['POST'])
def create_tune_notification():
    """Subscribe a visitor to updates for a tune."""
    try:
        data = get_json_payload()
        if data is None:
            return jsonify({'success': False, 'message': 'Invalid JSON payload'}), 400

        error = require_fields(data, ['tune_title', 'email'])
        if error:
            return jsonify({'success': False, 'message': error}), 400

        email = data['email'].strip().lower()
        tune_title = data['tune_title'].strip()
        tune_id = data.get('tune_id')

        existing = TuneNotification.query.filter_by(
            email=email,
            tune_title=tune_title,
            status='Subscribed'
        ).first()
        if existing:
            return jsonify({
                'success': True,
                'message': 'You are already subscribed for this tune',
                'notification': existing.to_dict()
            }), 200

        notification = TuneNotification(
            tune_id=tune_id,
            tune_title=tune_title,
            email=email
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Notification signup saved successfully',
            'notification': notification.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error saving notification: {str(e)}'}), 500


@engagement_bp.route('/tune-notifications', methods=['GET'])
def get_tune_notifications():
    """List tune notification signups for admin dashboards."""
    try:
        notifications = TuneNotification.query.order_by(TuneNotification.created_at.desc()).all()
        return jsonify({
            'success': True,
            'notifications': [notification.to_dict() for notification in notifications]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error fetching notifications: {str(e)}'}), 500
