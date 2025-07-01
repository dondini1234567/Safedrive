from app import create_app,socketio
import os
import sys

# Add external_libs to Python path if it exists
external_libs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'external_libs')
if os.path.exists(external_libs_path):
    sys.path.append(external_libs_path)
    print(f"Added {external_libs_path} to Python path")

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)
