import os
import base64
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room
from flask_login import current_user
from app import socketio, db
from app.models.user import User
from app.models.file_message import FileMessage
from app.text_message import TextMessage  # Ensure this is your text message model

UPLOAD_FOLDER = 'uploads'  # Make sure this folder exists!

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        room = f"user_{current_user.id}"
        join_room(room)
        print(f"✅ {current_user.email} connected to room {room}")
        emit('status', {'msg': f'{current_user.email} connected.'}, room=room)
    else:
        print("❌ Unauthorized connection attempt")
        return False

@socketio.on('private_message')
def handle_private_message(data):
    recipient_id = data.get('recipient_id')
    message = data.get('msg')

    if not recipient_id or not message:
        print("❌ Missing message or recipient_id")
        return

    # Save the message to the database
    text_msg = TextMessage(
        sender_id=current_user.id,
        recipient_id=int(recipient_id),
        content=message,
        timestamp=datetime.utcnow()
    )
    db.session.add(text_msg)
    db.session.commit()

    message_payload = {
        'sender_email': current_user.email,
        'sender_id': current_user.id,
        'username': current_user.email.split('@')[0],
        'msg': message,
        'timestamp': text_msg.timestamp.strftime('%Y-%m-%d %H:%M')
    }

    print(f"💬 Message from {current_user.email} to user {recipient_id}: {message}")

    sender_room = f"user_{current_user.id}"
    recipient_room = f"user_{recipient_id}"

    emit('private_message', message_payload, room=recipient_room)
    emit('private_message', message_payload, room=sender_room)

@socketio.on('private_file')
def handle_private_file(data):
    recipient_id = data.get('recipient_id')
    file_data = data.get('file_data')
    file_name = data.get('file_name')

    if not recipient_id or not file_data or not file_name:
        print("❌ Missing file info")
        return

    try:
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        safe_filename = f"{datetime.utcnow().timestamp()}_{file_name}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_filename)

        # Decode base64 content
        base64_data = file_data.split(',')[1]  # Remove "data:*/*;base64,"
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(base64_data))

        # Save metadata to DB
        file_msg = FileMessage(
            sender_id=current_user.id,
            recipient_id=int(recipient_id),
            filename=file_name,
            file_data=file_data,  # still keep this if you want to reuse it later
            filepath=file_path,
            is_file=True,
            timestamp=datetime.utcnow()
        )
        db.session.add(file_msg)
        db.session.commit()

        print(f"📁 File saved and recorded: {file_name} → {file_path}")

        file_payload = {
            'sender_email': current_user.email,
            'sender_id': current_user.id,
            'username': current_user.email.split('@')[0],
            'file_name': file_name,
            'file_data': file_data,
            'timestamp': file_msg.timestamp.strftime('%Y-%m-%d %H:%M')
        }

        recipient_room = f"user_{recipient_id}"
        sender_room = f"user_{current_user.id}"

        emit('private_file', file_payload, room=recipient_room)
        emit('private_file', file_payload, room=sender_room)

    except Exception as e:
        print(f"❌ Error saving file: {e}")
        emit('error', {'msg': 'File upload failed.'}, room=f"user_{current_user.id}")
