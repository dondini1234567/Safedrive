from app import create_app, socketio
from app.extensions import socketio  # socketio is created in extensions.py

app = create_app()

if __name__ == '__main__':
    socketio.run(app, debug=True)