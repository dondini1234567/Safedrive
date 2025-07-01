import os
import sqlite3
from flask import Flask
from app import create_app

def update_database():
    """Update the database schema to support profile images without migrations"""
    app = create_app()
    
    # Get the database path from the app config
    db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
    
    # Create the uploads directory if it doesn't exist
    os.makedirs('app/static/uploads/profile_images', exist_ok=True)
    
    print(f"Connecting to database at {db_path}")
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the profile_image column already exists
        cursor.execute("PRAGMA table_info(user)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'profile_image' not in column_names:
            print("Adding profile_image column to user table...")
            cursor.execute("ALTER TABLE user ADD COLUMN profile_image TEXT")
            conn.commit()
            print("Column added successfully!")
        else:
            print("profile_image column already exists.")
        
        conn.close()
        print("Database update completed successfully!")
        return True
    except Exception as e:
        print(f"Error updating database: {str(e)}")
        return False

if __name__ == "__main__":
    update_database()
