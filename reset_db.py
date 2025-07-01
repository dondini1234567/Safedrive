import os
import sys
from pathlib import Path

# Add the parent directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app import create_app, db
from app.models.user import User
from app.models.file import File
from app.models.file_share import FileShare

app = create_app()

def reset_database():
    with app.app_context():
        # Drop all tables
        db.drop_all()
        print("All tables dropped.")
        
        # Create all tables
        db.create_all()
        print("All tables recreated.")
        
        # Create admin user
        from werkzeug.security import generate_password_hash
        admin = User(
            email=app.config.get('ADMIN_EMAIL', 'admin@example.com'),
            password_hash=generate_password_hash(app.config.get('ADMIN_PASSWORD', 'admin123')),
            is_verified=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin user created with email: {admin.email}")
        
        # Remove uploaded files
        upload_folder = app.config['UPLOAD_FOLDER']
        if os.path.exists(upload_folder):
            for file in os.listdir(upload_folder):
                file_path = os.path.join(upload_folder, file)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                        print(f"Deleted file: {file_path}")
                except Exception as e:
                    print(f"Error deleting {file_path}: {e}")
        
        print("Database reset complete.")

if __name__ == "__main__":
    reset_database()
