from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
import os
from app.admin import bp
from werkzeug.utils import secure_filename

@bp.route('/setup-google-drive', methods=['GET'])
@login_required
def setup_google_drive():
    """Setup page for Google Drive integration"""
    # Check if user is an admin
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Redirect URI for Google OAuth
    redirect_uri = url_for('drive_routes.auth_callback', _external=True)
    
    return render_template('create_client_secret.html', 
                           title='Set Up Google Drive API',
                           redirect_uri=redirect_uri)

@bp.route('/upload-client-secret', methods=['POST'])
@login_required
def upload_client_secret():
    """Handle client_secret.json upload"""
    # Check if user is an admin
    if not current_user.is_admin:
        flash('You do not have permission to access this page', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if the post request has the file part
    if 'client_secret' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('admin.setup_google_drive'))
    
    file = request.files['client_secret']
    
    # If user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('admin.setup_google_drive'))
    
    if file and file.filename.endswith('.json'):
        filename = 'client_secret.json'
        file_path = os.path.join(current_app.root_path, filename)
        file.save(file_path)
        flash('Client secret uploaded successfully', 'success')
        return redirect(url_for('main.dashboard'))
    else:
        flash('Invalid file. Please upload a valid client_secret.json file', 'error')
        return redirect(url_for('admin.setup_google_drive'))
