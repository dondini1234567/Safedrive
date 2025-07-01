from flask import render_template, redirect, url_for, flash, request, jsonify, send_file, current_app, session, make_response
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse

from app import db
from app.models.user import User
from app.models.file import File
from app.models.file_message import FileMessage
from app.text_message import TextMessage
from app.auth.otp import generate_otp, verify_otp, send_otp_email
from app.crypto.ntru_encryption import encrypt_file, decrypt_file
from app.drive.google_drive import upload_file, download_file, delete_from_drive, is_authenticated, list_drive_files
from app.drive.google_drive import share_file_with_user
import os
from datetime import datetime
import logging
from werkzeug.utils import secure_filename
import uuid
import shutil
from PIL import Image
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from flask import Blueprint
bp = Blueprint('main', __name__, template_folder='templates')


# Standard profile image size - smaller to match navigation bar
PROFILE_IMAGE_SIZE = (40, 40)

@bp.route('/')
@bp.route('/index')
def index():
    """Render the landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='Welcome to SafeDrive')

@bp.route('/dashboard')
@login_required
def dashboard():
    """Render the dashboard page"""
    # Get user's files
    files = File.query.filter_by(user_id=current_user.id).order_by(File.created_at.desc()).all()
    
    # Get statistics
    total_files = len(files)
    total_size = sum(file.size or 0 for file in files)
    recent_files = files[:5]  # Get 5 most recent files
    
    # Check if connected to Google Drive
    is_drive_connected = is_authenticated()
    
    # Get uploaded files from session for debugging
    uploaded_files = session.get('uploaded_files', [])
    
    return render_template('dashboard.html', 
                          title='Dashboard', 
                          files=files,
                          total_files=total_files,
                          total_size=total_size,
                          recent_files=recent_files,
                          is_drive_connected=is_drive_connected,
                          uploaded_files=uploaded_files)

@bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Handle file upload and encryption"""
    # Check if connected to Google Drive
    is_drive_connected = is_authenticated()
    
    if request.method == 'POST':
        # Only process POST if connected to Google Drive
        if not is_drive_connected:
            flash('Please connect to Google Drive first', 'info')
            return redirect(url_for('drive_routes.connect', next=url_for('main.upload')))
        
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file:
            # Get encryption password
            encryption_password = request.form.get('encryption_password')
            if not encryption_password:
                flash('Encryption password is required', 'error')
                return redirect(request.url)
            
            # Get optional encryption hint
            encryption_hint = request.form.get('encryption_hint', '')
            
            # Save file temporarily
            temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_' + file.filename)
            file.save(temp_path)
            
            try:
                # Encrypt the file
                encrypted_path = encrypt_file(temp_path, encryption_password)
                
                # Upload to Google Drive
                try:
                    drive_file_id = upload_file(encrypted_path, file.filename + '.encrypted')
                    logger.info(f"File uploaded to Google Drive with ID: {drive_file_id}")
                except Exception as e:
                    logger.error(f"Error uploading to Google Drive: {str(e)}")
                    flash(f'Error uploading to Google Drive: {str(e)}', 'error')
                    # Clean up temporary files
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    if os.path.exists(encrypted_path):
                        os.remove(encrypted_path)
                    return redirect(request.url)
                
                # Create file record in database
                new_file = File(
                    filename=os.path.basename(encrypted_path),
                    original_filename=file.filename,
                    drive_file_id=drive_file_id,
                    mime_type=file.content_type,
                    size=os.path.getsize(encrypted_path),
                    encrypted=True,
                    encryption_hint=encryption_hint,
                    user_id=current_user.id
                )
                
                db.session.add(new_file)
                db.session.commit()
                
                # Clean up temporary files
                os.remove(temp_path)
                os.remove(encrypted_path)
                
                # Add a link to view the file in Google Drive
                if 'uploaded_files' in session:
                    for uploaded_file in session['uploaded_files']:
                        if uploaded_file.get('id') == drive_file_id:
                            flash(f'File encrypted and uploaded successfully! <a href="{uploaded_file.get("link")}" target="_blank">View in Google Drive</a>', 'success')
                            break
                    else:
                        flash('File encrypted and uploaded successfully!', 'success')
                else:
                    flash('File encrypted and uploaded successfully!', 'success')
                
                return redirect(url_for('main.dashboard'))
                
            except Exception as e:
                logger.error(f"Error processing file: {str(e)}")
                flash(f'Error processing file: {str(e)}', 'error')
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return redirect(request.url)
    
    return render_template('upload.html', 
                          title='Upload File',
                          is_drive_connected=is_drive_connected)

@bp.route('/download/<int:file_id>', methods=['GET', 'POST'])
@login_required
def download(file_id):
    """Handle file download and decryption"""
    # Check if connected to Google Drive
    if not is_authenticated():
        # Store the current URL in the session
        session['google_drive_next'] = url_for('main.download', file_id=file_id)
        # Redirect to Google Drive connection
        flash('Please connect to Google Drive first', 'info')
        return redirect(url_for('drive_routes.connect'))
    
    file = File.query.filter_by(id=file_id).first_or_404()
    
    # Check if the file belongs to the current user or is shared with them
    if file.user_id != current_user.id and not file.is_shared_with(current_user.id):
        flash('You do not have permission to access this file', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        # Get decryption password
        decryption_password = request.form.get('decryption_password')
        if not decryption_password:
            flash('Decryption password is required', 'error')
            return redirect(request.url)
        
        try:
            # Download encrypted file from Google Drive
            encrypted_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
            download_file(file.drive_file_id, encrypted_path)
            
            # Decrypt the file
            decrypted_path = decrypt_file(encrypted_path, decryption_password)
            
            # Rename to original filename
            output_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.original_filename)
            os.rename(decrypted_path, output_path)
            
            # Clean up encrypted file
            os.remove(encrypted_path)
            
            # Send the file to the user
            import time
            time.sleep(0.5)  # Small delay to allow the loading animation to show progress
            return send_file(output_path, 
                            as_attachment=True, 
                            download_name=file.original_filename,
                            mimetype=file.mime_type)
            
        except Exception as e:
            logger.error(f"Error decrypting file: {str(e)}")
            flash(f'Error decrypting file: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('download.html', 
                          title='Download File', 
                          file=file)

@bp.route('/files')
@login_required
def files():
    """Render the files page"""
    files = File.query.filter_by(user_id=current_user.id).order_by(File.created_at.desc()).all()
    
    # Get Google Drive files for comparison
    drive_files = []
    if is_authenticated():
        try:
            drive_files = list_drive_files()
        except Exception as e:
            logger.error(f"Error listing Drive files: {str(e)}")
    
    return render_template('files.html', 
                          title='My Files', 
                          files=files,
                          drive_files=drive_files,
                          is_drive_connected=is_authenticated())

@bp.route('/files/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    """Delete a file"""
    # Check if connected to Google Drive
    if not is_authenticated():
        flash('Please connect to Google Drive first', 'info')
        return redirect(url_for('drive_routes.connect', next=request.referrer))
    
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    try:
        # Delete from Google Drive
        delete_from_drive(file.drive_file_id)
        
        # Delete from database
        db.session.delete(file)
        db.session.commit()
        
        flash('File deleted successfully', 'success')
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        flash(f'Error deleting file: {str(e)}', 'error')
    
    return redirect(url_for('main.files'))

@bp.route('/files/<int:file_id>/update_hint', methods=['POST'])
@login_required
def update_hint(file_id):
    """Update encryption hint for a file"""
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    new_hint = request.form.get('encryption_hint', '')
    file.encryption_hint = new_hint
    db.session.commit()
    
    flash('Encryption hint updated', 'success')
    return redirect(url_for('main.files'))

@bp.route('/chat')
def chat():
    return render_template('chat.html') 

@bp.route('/messages')
@login_required
def messages():
    all_users = User.query.filter(User.id != current_user.id).all()

    if not all_users:
        flash("No other users available to chat with.", "info")
        return render_template("message.html", users=[], history=[])

    # Default to first user if no recipient_id provided
    selected_user_id = request.args.get('recipient_id', type=int)
    if not selected_user_id:
        selected_user_id = all_users[0].id

    # Load both text and file messages between current_user and selected_user
    text_msgs = TextMessage.query.filter(
        ((TextMessage.sender_id == current_user.id) & (TextMessage.recipient_id == selected_user_id)) |
        ((TextMessage.sender_id == selected_user_id) & (TextMessage.recipient_id == current_user.id))
    ).all()

    file_msgs = FileMessage.query.filter(
        ((FileMessage.sender_id == current_user.id) & (FileMessage.recipient_id == selected_user_id)) |
        ((FileMessage.sender_id == selected_user_id) & (FileMessage.recipient_id == current_user.id))
    ).all()

    # Combine and sort by timestamp
    all_msgs = sorted(text_msgs + file_msgs, key=lambda m: m.timestamp)

    return render_template("message.html", users=all_users, history=all_msgs)

@bp.route('/settings')
@login_required
def settings():
    """Render the settings page"""
    return render_template('settings.html', 
                          title='Settings',
                          is_drive_connected=is_authenticated())

@bp.route('/profile')
@login_required
def profile():
    """Render the profile page"""
    try:
        # Get user activity data
        user_files = File.query.filter_by(user_id=current_user.id).order_by(File.created_at.desc()).limit(3).all()
        
        # Get shared files count safely
        shared_files_count = 0
        try:
            if hasattr(current_user, 'get_shared_files'):
                shared_files = current_user.get_shared_files()
                shared_files_count = len(shared_files) if shared_files else 0
        except Exception as e:
            logger.error(f"Error getting shared files: {str(e)}")
        
        # Format user data safely
        user_data = {
            'first_name': current_user.first_name or 'User',
            'last_name': current_user.last_name or '',
            'email': current_user.email,
            'created_at': current_user.created_at,
            'last_login': current_user.last_login,
            'is_verified': current_user.is_verified,
            'files_count': current_user.files.count(),
            'shared_files_count': shared_files_count,
            'profile_image': current_user.get_profile_image_url()
        }
        
        # Get recent activity
        recent_activity = []
        for file in user_files:
            recent_activity.append({
                'type': 'upload',
                'filename': file.original_filename,
                'timestamp': file.created_at
            })
        
        # Pass current time for relative time calculations
        now = datetime.utcnow()
        
        return render_template('profile.html', 
                              title='My Profile',
                              user_data=user_data,
                              recent_activity=recent_activity,
                              now=now)
    
    except Exception as e:
        logger.error(f"Error rendering profile page: {str(e)}")
        flash('An error occurred while loading your profile. Please try again later.', 'error')
        return redirect(url_for('main.dashboard'))

def resize_and_crop_image(image, size=PROFILE_IMAGE_SIZE):
    """
    Resize and crop an image to make it square with the specified dimensions
    while maintaining the aspect ratio from the center.
    """
    # Open the image
    img = Image.open(image)
    
    # Convert to RGB if image is in RGBA mode (e.g., PNG with transparency)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Get current dimensions
    width, height = img.size
    
    # Determine the crop box (to make it square)
    if width > height:
        # Landscape image
        left = (width - height) / 2
        top = 0
        right = (width + height) / 2
        bottom = height
    else:
        # Portrait image
        left = 0
        top = (height - width) / 2
        right = width
        bottom = (height + width) / 2
    
    # Crop to square
    img = img.crop((left, top, right, bottom))
    
    # Resize to desired dimensions
    img = img.resize(size, Image.LANCZOS)
    
    return img

@bp.route('/upload-profile-image', methods=['POST'])
@login_required
def upload_profile_image():
    """Handle profile image upload"""
    if 'profile_image' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('main.profile'))
    
    file = request.files['profile_image']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('main.profile'))
    
    # Check if the file is an allowed image type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF image.', 'error')
        return redirect(url_for('main.profile'))
    
    try:
        # Create profile images directory if it doesn't exist
        profile_images_dir = os.path.join(current_app.static_folder, 'uploads', 'profile_images')
        os.makedirs(profile_images_dir, exist_ok=True)
        
        # Resize and crop the image
        resized_img = resize_and_crop_image(file)
        
        # Save the file with a name based on the user's ID
        filename = f"user_{current_user.id}.png"
        file_path = os.path.join(profile_images_dir, filename)
        
        # Save the resized image
        resized_img.save(file_path, format='PNG', quality=95, optimize=True)
        
        # Set no-cache headers for the response
        response = make_response(redirect(url_for('main.profile')))
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        flash('Profile image updated successfully!', 'success')
        return response
    except Exception as e:
        logger.error(f"Error uploading profile image: {str(e)}")
        flash(f'Error uploading profile image: {str(e)}', 'error')
    
    return redirect(url_for('main.profile'))

@bp.route('/share/<int:file_id>', methods=['GET', 'POST'])
@login_required
def share_file(file_id):
    """Share a file with another user"""
    file = File.query.filter_by(id=file_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Email is required', 'error')
            return redirect(request.url)
        
        # Find the user
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('User not found', 'error')
            return redirect(request.url)
        
        # Check if already shared
        if file.is_shared_with(user.id):
            flash('File already shared with this user', 'warning')
            return redirect(request.url)
        
        # Share the file
        file.share_with(user.id)
        db.session.commit()
        
        try:
            if file.drive_file_id:
                share_file_with_user(file.drive_file_id, user.email)
        except Exception as e:
            flash(f'File shared in app, but Google Drive sharing failed: {str(e)}', 'warning')
        else:
            flash(f'File shared with {email}', 'success')
        
        return redirect(url_for('main.files'))
    
    
    return render_template('share.html', title='Share File', file=file)

@bp.route('/shared')
@login_required
def shared_files():
    """View files shared with the current user"""
    try:
        files = current_user.get_shared_files()
        return render_template('shared_files.html', 
                              title='Shared Files', 
                              files=files,
                              is_drive_connected=is_authenticated())
    except Exception as e:
        logger.error(f"Error rendering shared files page: {str(e)}")
        flash('An error occurred while loading shared files. Please try again later.', 'error')
        return redirect(url_for('main.dashboard'))

@bp.route('/debug')
@login_required
def debug():
    """Debug page for troubleshooting"""
    return redirect(url_for('drive_routes.debug'))

@bp.route('/encryption')
def encryption_details():
    """Render the encryption details page"""
    return render_template('encryption_details.html', 
                          title='Encryption Details',
                          page_specific_css='encryption.css')

@bp.route('/refresh-profile-image')
@login_required
def refresh_profile_image():
    """Force refresh of profile image by returning the current URL with cache busting"""
    return jsonify({
        'profile_image_url': current_user.get_profile_image_url()
    })
