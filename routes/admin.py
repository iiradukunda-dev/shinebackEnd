from flask import Blueprint, request, jsonify, session
from datetime import datetime
from src.models.user import db
from src.models.admin import Admin

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/login', methods=['POST'])
def admin_login():
    """Admin login"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('username') or not data.get('password'):
            return jsonify({
                'success': False,
                'message': 'Username and password are required'
            }), 400
        
        # Find admin by username
        admin = Admin.query.filter_by(username=data['username']).first()
        
        if not admin or not admin.check_password(data['password']):
            return jsonify({
                'success': False,
                'message': 'Invalid username or password'
            }), 401
        
        if not admin.is_active:
            return jsonify({
                'success': False,
                'message': 'Account is deactivated'
            }), 401
        
        # Update last login
        admin.last_login = datetime.utcnow()
        db.session.commit()
        
        # Store admin info in session
        session['admin_id'] = admin.id
        session['admin_username'] = admin.username
        session['admin_role'] = admin.role
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'admin': admin.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error during login: {str(e)}'
        }), 500

@admin_bp.route('/admin/logout', methods=['POST'])
def admin_logout():
    """Admin logout"""
    try:
        session.clear()
        return jsonify({
            'success': True,
            'message': 'Logout successful'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error during logout: {str(e)}'
        }), 500

@admin_bp.route('/admin/profile', methods=['GET'])
def get_admin_profile():
    """Get current admin profile"""
    try:
        if 'admin_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        admin = Admin.query.get(session['admin_id'])
        if not admin:
            return jsonify({
                'success': False,
                'message': 'Admin not found'
            }), 404
        
        return jsonify({
            'success': True,
            'admin': admin.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching profile: {str(e)}'
        }), 500

@admin_bp.route('/admin/create', methods=['POST'])
def create_admin():
    """Create a new admin (Super Admin only)"""
    try:
        # Check if user is authenticated and is super admin
        if 'admin_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        current_admin = Admin.query.get(session['admin_id'])
        if not current_admin or current_admin.role != 'super_admin':
            return jsonify({
                'success': False,
                'message': 'Insufficient permissions'
            }), 403
        
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Check if username or email already exists
        existing_admin = Admin.query.filter(
            (Admin.username == data['username']) | (Admin.email == data['email'])
        ).first()
        
        if existing_admin:
            return jsonify({
                'success': False,
                'message': 'Username or email already exists'
            }), 400
        
        # Create new admin
        admin = Admin(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            role=data.get('role', 'admin')
        )
        admin.set_password(data['password'])
        
        db.session.add(admin)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Admin created successfully',
            'admin': admin.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating admin: {str(e)}'
        }), 500

@admin_bp.route('/admin/dashboard', methods=['GET'])
def admin_dashboard():
    """Get admin dashboard statistics"""
    try:
        if 'admin_id' not in session:
            return jsonify({
                'success': False,
                'message': 'Not authenticated'
            }), 401
        
        from src.models.event import Event
        from src.models.tune import Tune
        from src.models.member import Member, MemberApplication
        
        # Get statistics
        total_events = Event.query.filter_by(is_active=True).count()
        total_tunes = Tune.query.filter_by(is_active=True).count()
        total_members = Member.query.filter_by(is_active=True).count()
        pending_applications = MemberApplication.query.filter_by(status='Pending').count()
        
        # Get recent activities
        recent_events = Event.query.filter_by(is_active=True).order_by(Event.created_at.desc()).limit(5).all()
        recent_applications = MemberApplication.query.order_by(MemberApplication.created_at.desc()).limit(5).all()
        
        return jsonify({
            'success': True,
            'dashboard': {
                'statistics': {
                    'total_events': total_events,
                    'total_tunes': total_tunes,
                    'total_members': total_members,
                    'pending_applications': pending_applications
                },
                'recent_events': [event.to_dict() for event in recent_events],
                'recent_applications': [app.to_dict() for app in recent_applications]
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching dashboard: {str(e)}'
        }), 500

# Middleware to check admin authentication
def require_admin_auth():
    """Decorator to require admin authentication"""
    def decorator(f):
        def wrapper(*args, **kwargs):
            if 'admin_id' not in session:
                return jsonify({
                    'success': False,
                    'message': 'Authentication required'
                }), 401
            return f(*args, **kwargs)
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator

