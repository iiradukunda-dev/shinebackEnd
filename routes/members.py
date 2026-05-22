from flask import Blueprint, request, jsonify
from datetime import datetime
import qrcode
import io
import base64
from src.models.user import db
from src.models.member import Member, MemberApplication

members_bp = Blueprint('members', __name__)

def generate_qr_code(member_id, member_name):
    """Generate QR code for member"""
    try:
        # Create QR code data
        qr_data = f"MEMBER_ID:{member_id}\nNAME:{member_name}\nORG:Shining Ministries"
        
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    except Exception as e:
        print(f"Error generating QR code: {str(e)}")
        return None


def parse_member_payload():
    """Parse JSON or multipart form payload for member/photo uploads."""
    data = request.get_json(silent=True)
    if isinstance(data, dict) and data:
        if 'photo' in data and 'photo_data' not in data:
            data['photo_data'] = data['photo']
        return data

    data = request.form.to_dict() if request.form else {}
    if 'photo' in data and 'photo_data' not in data:
        data['photo_data'] = data['photo']

    photo_file = request.files.get('photo')
    if photo_file:
        try:
            file_bytes = photo_file.read()
            encoded = base64.b64encode(file_bytes).decode()
            content_type = photo_file.content_type or 'application/octet-stream'
            data['photo_data'] = f"data:{content_type};base64,{encoded}"
            data['photo_name'] = photo_file.filename or data.get('photo_name')
        except Exception as e:
            return {
                'parse_error': f'Error reading uploaded file: {str(e)}'
            }

    return data

@members_bp.route('/members', methods=['GET'])
def get_members():
    """Get all active members"""
    try:
        members = Member.query.filter_by(is_active=True).order_by(Member.created_at.desc()).all()
        return jsonify({
            'success': True,
            'members': [member.to_dict() for member in members] 
        }), 200 
    
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching members: {str(e)}'
        }), 500

@members_bp.route('/members/<string:member_id>/qr', methods=['GET'])
def get_member_qr(member_id):
    """Get member QR code"""
    try:
        member = Member.query.filter_by(member_id=member_id).first()
        if not member:
            return jsonify({
                'success': False,
                'message': 'Member not found'
            }), 404
        
        # Generate QR code if not exists
        if not member.qr_code_data:
            qr_code = generate_qr_code(member.member_id, member.full_name)
            if qr_code:
                member.qr_code_data = qr_code
                db.session.commit()
        
        return jsonify({
            'success': True,
            'member': {
                'id': member.id,
                'full_name': member.full_name,
                'member_id': member.member_id,
                'qr_code_data': member.qr_code_data,
                'status': member.status
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching member QR code: {str(e)}'
        }), 500

@members_bp.route('/members', methods=['POST'])
def create_member():
    """Create a new member (Admin only)"""
    try:
        data = parse_member_payload()
        if isinstance(data, dict) and data.get('parse_error'):
            return jsonify({
                'success': False,
                'message': data['parse_error']
            }), 400

        # Validate required fields
        required_fields = ['full_name', 'email', 'photo_data']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Validate photo_data is string
        if not isinstance(data['photo_data'], str):
            return jsonify({
                'success': False,
                'message': 'Invalid photo upload format'
            }), 400
        
        # Check if email already exists
        existing_member = Member.query.filter_by(email=data['email']).first()
        if existing_member:
            return jsonify({
                'success': False,
                'message': 'Member with this email already exists'
            }), 400
        
        # Create new member
        member = Member(
            full_name=data['full_name'],
            email=data['email'],
            phone=data.get('phone', ''),
            age=data.get('age'),
            musical_experience=data.get('musical_experience', ''),
            motivation=data.get('motivation', ''),
            photo_name=data.get('photo_name'),
            photo_data=data['photo_data'],
            status=data.get('status', 'Active')
        )
        
        db.session.add(member)
        db.session.flush()  # Get the ID
        
        # Generate QR code
        qr_code = generate_qr_code(member.member_id, member.full_name)
        if qr_code:
            member.qr_code_data = qr_code
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Member created successfully',
            'member': member.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating member: {str(e)}'
        }), 500

@members_bp.route('/members/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    """Update an existing member (Admin only)"""
    try:
        member = Member.query.get_or_404(member_id)
        data = request.get_json()
        
        # Update fields if provided
        if 'full_name' in data:
            member.full_name = data['full_name']
            # Regenerate QR code if name changed
            qr_code = generate_qr_code(member.member_id, member.full_name)
            if qr_code:
                member.qr_code_data = qr_code
        if 'email' in data:
            # Check if email already exists for another member
            existing_member = Member.query.filter(
                Member.email == data['email'],
                Member.id != member_id
            ).first()
            if existing_member:
                return jsonify({
                    'success': False,
                    'message': 'Email already exists for another member'
                }), 400
            member.email = data['email']
        if 'phone' in data:
            member.phone = data['phone']
        if 'age' in data:
            member.age = data['age']
        if 'musical_experience' in data:
            member.musical_experience = data['musical_experience']
        if 'motivation' in data:
            member.motivation = data['motivation']
        if 'status' in data:
            member.status = data['status']
        if 'documents' in data:
            member.documents = data['documents']
        if 'is_active' in data:
            member.is_active = data['is_active']
        
        member.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Member updated successfully',
            'member': member.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error updating member: {str(e)}'
        }), 500

@members_bp.route('/members/<int:member_id>', methods=['DELETE'])
def delete_member(member_id):
    """Delete a member (Admin only)"""
    try:
        member = Member.query.get_or_404(member_id)
        member.is_active = False
        member.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Member deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting member: {str(e)}'
        }), 500

@members_bp.route('/members', methods=['DELETE'])
def clear_members():
    """Delete all members (Admin only)"""
    try:
        deleted = Member.query.filter_by(is_active=True).delete()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'All members cleared ({deleted} records removed).'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error clearing members: {str(e)}'
        }), 500

# Member Applications Routes
@members_bp.route('/applications', methods=['POST'])
def submit_application():
    """Submit a new member application"""
    try:
        data = parse_member_payload()
        if isinstance(data, dict) and data.get('parse_error'):
            return jsonify({
                'success': False,
                'message': data['parse_error']
            }), 400

        # Validate required fields
        required_fields = ['full_name', 'email', 'photo_data']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400

        if not isinstance(data['photo_data'], str):
            return jsonify({
                'success': False,
                'message': 'Invalid photo upload format. Please upload a valid image.'
            }), 400
        
        # Create new application
        application = MemberApplication(
            full_name=data['full_name'],
            email=data['email'],
            phone=data.get('phone', ''),
            age=data.get('age'),
            musical_experience=data.get('musical_experience', ''),
            motivation=data.get('motivation', ''),
            photo_name=data.get('photo_name'),
            photo_data=data['photo_data']
        )
        
        db.session.add(application)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application submitted successfully',
            'application': application.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error submitting application: {str(e)}'
        }), 500

@members_bp.route('/applications', methods=['GET'])
def get_applications():
    """Get all member applications (Admin only)"""
    try:
        applications = MemberApplication.query.order_by(MemberApplication.created_at.desc()).all()
        return jsonify({
            'success': True,
            'applications': [app.to_dict() for app in applications]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching applications: {str(e)}'
        }), 500

@members_bp.route('/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    """Delete a single member application (Admin only)"""
    try:
        application = MemberApplication.query.get_or_404(app_id)
        db.session.delete(application)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': 'Application deleted successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error deleting application: {str(e)}'
        }), 500

@members_bp.route('/applications', methods=['DELETE'])
def clear_applications():
    """Delete all member applications (Admin only)"""
    try:
        deleted = MemberApplication.query.delete()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'All applications cleared ({deleted} records removed).'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error clearing applications: {str(e)}'
        }), 500

@members_bp.route('/applications/history', methods=['DELETE'])
def clear_application_history():
    """Delete processed member applications (Approved/Rejected) (Admin only)"""
    try:
        deleted = MemberApplication.query.filter(MemberApplication.status != 'Pending').delete()
        db.session.commit()
        return jsonify({
            'success': True,
            'message': f'Application history cleared ({deleted} records removed).'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error clearing application history: {str(e)}'
        }), 500

@members_bp.route('/applications/<int:app_id>/approve', methods=['POST'])
def approve_application(app_id):
    """Approve a member application and create member (Admin only)"""
    try:
        application = MemberApplication.query.get_or_404(app_id)
        
        if application.status != 'Pending':
            return jsonify({
                'success': False,
                'message': 'Application has already been processed'
            }), 400
        
        # Check if email already exists as member
        existing_member = Member.query.filter_by(email=application.email).first()
        if existing_member:
            return jsonify({
                'success': False,
                'message': 'Member with this email already exists'
            }), 400
        
        # Create new member from application
        member = Member(
            full_name=application.full_name,
            email=application.email,
            phone=application.phone,
            age=application.age,
            musical_experience=application.musical_experience,
            motivation=application.motivation,
            photo_name=application.photo_name,
            photo_data=application.photo_data,
            status='Active'
        )
        
        db.session.add(member)
        db.session.flush()  # Get the ID
        
        # Generate QR code
        qr_code = generate_qr_code(member.member_id, member.full_name)
        if qr_code:
            member.qr_code_data = qr_code
        
        # Update application status
        application.status = 'Approved'
        application.reviewed_at = datetime.utcnow()
        application.reviewed_by = 'Admin'  # In real app, get from session
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application approved and member created successfully',
            'member': member.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error approving application: {str(e)}'
        }), 500

@members_bp.route('/applications/<int:app_id>/reject', methods=['POST'])
def reject_application(app_id):
    """Reject a member application (Admin only)"""
    try:
        application = MemberApplication.query.get_or_404(app_id)
        
        if application.status != 'Pending':
            return jsonify({
                'success': False,
                'message': 'Application has already been processed'
            }), 400
        
        application.status = 'Rejected'
        application.reviewed_at = datetime.utcnow()
        application.reviewed_by = 'Admin'  # In real app, get from session
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Application rejected successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error rejecting application: {str(e)}'
        }), 500

