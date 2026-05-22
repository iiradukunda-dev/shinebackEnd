import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.events import events_bp
from src.routes.tunes import tunes_bp
from src.routes.members import members_bp   
from src.routes.admin import admin_bp
from src.routes.payments import payments_bp
from src.routes.engagement import engagement_bp

backend_static_folder = os.path.join(os.path.dirname(__file__), 'static')
frontend_build_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'shining-ministries-website', 'dist'))
static_folder = frontend_build_folder if os.path.isdir(frontend_build_folder) else backend_static_folder

if static_folder == frontend_build_folder:
    print(f"Serving frontend build from: {frontend_build_folder}")
else:
    print(f"Serving backend static files from: {backend_static_folder}")

app = Flask(__name__, static_folder=static_folder, static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

# Enable CORS for all routes
CORS(app, supports_credentials=True)

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(events_bp, url_prefix='/api')
app.register_blueprint(tunes_bp, url_prefix='/api')
app.register_blueprint(members_bp, url_prefix='/api')
app.register_blueprint(admin_bp, url_prefix='/api')
app.register_blueprint(payments_bp, url_prefix='/api')
app.register_blueprint(engagement_bp, url_prefix='/api')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Import all models to ensure they are registered
from src.models.event import Event
from src.models.tune import Tune
from src.models.member import Member, MemberApplication
from src.models.admin import Admin
from src.models.engagement import ContactMessage, TuneNotification
from src.routes.payments import Donation

with app.app_context():
    db.create_all()
    
    # Create default admin if none exists
    if not Admin.query.first():
        default_admin = Admin(
            username='admin',
            email='admin@shiningministries.com',
            full_name='System Administrator',
            role='super_admin'
        )
        default_admin.set_password('admin123')
        db.session.add(default_admin)
        db.session.commit()
        print("Default admin created: username=admin, password=admin123")

@app.route('/api/health', methods=['GET'])
def health_check():
    return {
        'success': True,
        'status': 'healthy',
        'service': 'shining-ministries-backend'
    }, 200

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
