from flask import Blueprint, request, jsonify
from datetime import datetime
import uuid
from src.models.user import db

payments_bp = Blueprint('payments', __name__)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    donor_name = db.Column(db.String(200), nullable=True)
    donor_email = db.Column(db.String(120), nullable=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='USD')
    payment_method = db.Column(db.String(50), nullable=False)  # mtn, paypal, western_union
    payment_status = db.Column(db.String(50), nullable=False, default='pending')  # pending, completed, failed, cancelled
    transaction_id = db.Column(db.String(200), nullable=True)
    payment_details = db.Column(db.JSON, nullable=True)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Donation {self.donation_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'donation_id': self.donation_id,
            'donor_name': self.donor_name,
            'donor_email': self.donor_email,
            'amount': self.amount,
            'currency': self.currency,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'transaction_id': self.transaction_id,
            'payment_details': self.payment_details,
            'message': self.message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

@payments_bp.route('/donations', methods=['POST'])
def create_donation():
    """Create a new donation record"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['amount', 'payment_method']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Validate payment method
        valid_methods = ['mtn', 'paypal', 'western_union']
        if data['payment_method'] not in valid_methods:
            return jsonify({
                'success': False,
                'message': 'Invalid payment method'
            }), 400
        
        # Validate amount
        try:
            amount = float(data['amount'])
            if amount <= 0:
                raise ValueError("Amount must be positive")
        except (ValueError, TypeError):
            return jsonify({
                'success': False,
                'message': 'Invalid amount'
            }), 400
        
        # Create donation record
        donation = Donation(
            donor_name=data.get('donor_name', ''),
            donor_email=data.get('donor_email', ''),
            amount=amount,
            currency=data.get('currency', 'USD'),
            payment_method=data['payment_method'],
            message=data.get('message', ''),
            payment_details=data.get('payment_details', {})
        )
        
        db.session.add(donation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Donation record created successfully',
            'donation': donation.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error creating donation: {str(e)}'
        }), 500

@payments_bp.route('/donations/mtn', methods=['POST'])
def process_mtn_payment():
    """Process MTN Mobile Money payment"""
    try:
        data = request.get_json()
        
        # Validate required fields for MTN
        required_fields = ['donation_id', 'phone_number', 'amount']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Find donation record
        donation = Donation.query.filter_by(donation_id=data['donation_id']).first()
        if not donation:
            return jsonify({
                'success': False,
                'message': 'Donation record not found'
            }), 404
        
        # Simulate MTN Mobile Money API call
        # In a real implementation, you would integrate with MTN Mobile Money API
        mtn_response = {
            'status': 'success',
            'transaction_id': f'MTN_{uuid.uuid4().hex[:12].upper()}',
            'phone_number': data['phone_number'],
            'amount': data['amount'],
            'currency': 'RWF',
            'message': 'Payment processed successfully'
        }
        
        # Update donation record
        donation.payment_status = 'completed'
        donation.transaction_id = mtn_response['transaction_id']
        donation.payment_details = mtn_response
        donation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'MTN Mobile Money payment processed successfully',
            'transaction': mtn_response,
            'donation': donation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error processing MTN payment: {str(e)}'
        }), 500

@payments_bp.route('/donations/paypal', methods=['POST'])
def process_paypal_payment():
    """Process PayPal payment"""
    try:
        data = request.get_json()
        
        # Validate required fields for PayPal
        required_fields = ['donation_id', 'paypal_order_id']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Find donation record
        donation = Donation.query.filter_by(donation_id=data['donation_id']).first()
        if not donation:
            return jsonify({
                'success': False,
                'message': 'Donation record not found'
            }), 404
        
        # Simulate PayPal API verification
        # In a real implementation, you would verify the payment with PayPal API
        paypal_response = {
            'status': 'COMPLETED',
            'order_id': data['paypal_order_id'],
            'transaction_id': f'PP_{uuid.uuid4().hex[:12].upper()}',
            'amount': donation.amount,
            'currency': donation.currency,
            'payer_email': data.get('payer_email', ''),
            'message': 'PayPal payment completed successfully'
        }
        
        # Update donation record
        donation.payment_status = 'completed'
        donation.transaction_id = paypal_response['transaction_id']
        donation.payment_details = paypal_response
        donation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'PayPal payment processed successfully',
            'transaction': paypal_response,
            'donation': donation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error processing PayPal payment: {str(e)}'
        }), 500

@payments_bp.route('/donations/western-union', methods=['POST'])
def process_western_union_payment():
    """Process Western Union payment"""
    try:
        data = request.get_json()
        
        # Validate required fields for Western Union
        required_fields = ['donation_id', 'mtcn', 'sender_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Find donation record
        donation = Donation.query.filter_by(donation_id=data['donation_id']).first()
        if not donation:
            return jsonify({
                'success': False,
                'message': 'Donation record not found'
            }), 404
        
        # Simulate Western Union verification
        # In a real implementation, you would verify the MTCN with Western Union API
        wu_response = {
            'status': 'verified',
            'mtcn': data['mtcn'],
            'sender_name': data['sender_name'],
            'amount': donation.amount,
            'currency': donation.currency,
            'receiver_name': 'Shining Ministries',
            'message': 'Western Union transfer verified successfully'
        }
        
        # Update donation record
        donation.payment_status = 'completed'
        donation.transaction_id = data['mtcn']
        donation.payment_details = wu_response
        donation.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Western Union payment verified successfully',
            'transaction': wu_response,
            'donation': donation.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error processing Western Union payment: {str(e)}'
        }), 500

@payments_bp.route('/donations', methods=['GET'])
def get_donations():
    """Get all donations (Admin only)"""
    try:
        donations = Donation.query.order_by(Donation.created_at.desc()).all()
        return jsonify({
            'success': True,
            'donations': [donation.to_dict() for donation in donations]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching donations: {str(e)}'
        }), 500

@payments_bp.route('/donations/<string:donation_id>', methods=['GET'])
def get_donation(donation_id):
    """Get a specific donation"""
    try:
        donation = Donation.query.filter_by(donation_id=donation_id).first()
        if not donation:
            return jsonify({
                'success': False,
                'message': 'Donation not found'
            }), 404
        
        return jsonify({
            'success': True,
            'donation': donation.to_dict()
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching donation: {str(e)}'
        }), 500

@payments_bp.route('/donations/stats', methods=['GET'])
def get_donation_stats():
    """Get donation statistics (Admin only)"""
    try:
        total_donations = db.session.query(db.func.sum(Donation.amount)).filter_by(payment_status='completed').scalar() or 0
        total_count = Donation.query.filter_by(payment_status='completed').count()
        
        # Get donations by payment method
        mtn_total = db.session.query(db.func.sum(Donation.amount)).filter_by(
            payment_method='mtn', payment_status='completed'
        ).scalar() or 0
        
        paypal_total = db.session.query(db.func.sum(Donation.amount)).filter_by(
            payment_method='paypal', payment_status='completed'
        ).scalar() or 0
        
        wu_total = db.session.query(db.func.sum(Donation.amount)).filter_by(
            payment_method='western_union', payment_status='completed'
        ).scalar() or 0
        
        return jsonify({
            'success': True,
            'stats': {
                'total_amount': total_donations,
                'total_count': total_count,
                'by_method': {
                    'mtn': mtn_total,
                    'paypal': paypal_total,
                    'western_union': wu_total
                }
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error fetching donation stats: {str(e)}'
        }), 500

