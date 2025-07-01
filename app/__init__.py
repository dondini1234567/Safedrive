import os
import sys
import logging
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from flask_socketio import SocketIO  # ✅ only once
from .config import Config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
mail = Mail()
socketio = SocketIO(cors_allowed_origins="*")  # ✅ CORS for socket.io

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)  # ✅ Flask-SocketIO initialization

    # Register blueprints
    from app.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.api import bp as api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    from app.drive import bp as drive_api_bp
    app.register_blueprint(drive_api_bp)

    from app.drive.routes import bp as drive_routes_bp
    app.register_blueprint(drive_routes_bp)

    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500

    # Ensure uploads directory exists
    os.makedirs(os.path.join(app.static_folder, 'uploads/profile_images'), exist_ok=True)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Create database tables if they don't exist
    with app.app_context():
        try:
            db.create_all()

            from app.models.user import User
            from werkzeug.security import generate_password_hash

            admin_email = app.config.get('ADMIN_EMAIL', 'admin@example.com')
            if not User.query.filter_by(email=admin_email).first():
                admin = User(
                    email=admin_email,
                    password_hash=generate_password_hash(app.config.get('ADMIN_PASSWORD', 'admin123')),
                    is_verified=True
                )
                db.session.add(admin)
                db.session.commit()
                app.logger.info(f"Created admin user with email: {admin_email}")
        except Exception as e:
            app.logger.error(f"Error during database initialization: {str(e)}")

    # ✅ Register socket events and models
    from app import models
    from app import realtime

    return app



