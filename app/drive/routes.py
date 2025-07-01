from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_required, current_user
import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
import logging

from app.drive.google_drive import (
    get_auth_url, save_credentials, is_authenticated, 
    get_drive_service, create_folder_if_not_exists,
    list_drive_files, get_drive_storage_info
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint
bp = Blueprint('drive_routes', __name__, url_prefix='/drive')

@bp.route('/connect')
@login_required
def connect():
    """Connect to Google Drive"""
    # Check if already authenticated
    if is_authenticated():
        flash('Already connected to Google Drive', 'info')
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        return redirect(url_for('main.dashboard'))
    
    # Check if client_secret.json exists
    client_secrets_file = os.path.join(current_app.root_path, 'client_secret.json')
    if not os.path.exists(client_secrets_file):
        flash('Google Drive API credentials not found. Please set up Google Drive first.', 'error')
        return redirect(url_for('drive_routes.setup'))
    
    try:
        # Get authorization URL
        auth_url = get_auth_url()
        
        # Store the next URL in the session
        next_url = request.args.get('next')
        if next_url:
            session['google_drive_next'] = next_url
        
        # Redirect to Google authorization page
        return redirect(auth_url)
    except Exception as e:
        logger.error(f"Error connecting to Google Drive: {str(e)}")
        flash(f'Error connecting to Google Drive: {str(e)}', 'error')
        return redirect(url_for('drive_routes.setup'))

@bp.route('/auth/callback')
@login_required
def auth_callback():
    """Handle Google Drive OAuth callback"""
    # Check if there was an error
    if 'error' in request.args:
        flash(f'Error authenticating with Google Drive: {request.args.get("error")}', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if state matches
    if 'state' not in request.args or 'google_drive_state' not in session or request.args.get('state') != session['google_drive_state']:
        flash('Invalid state parameter. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Check if code is present
    if 'code' not in request.args:
        flash('No authorization code received. Please try again.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        # Load client secrets
        client_secrets_file = os.path.join(current_app.root_path, 'client_secret.json')
        
        # Create flow instance
        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=['https://www.googleapis.com/auth/drive.file'],
            redirect_uri=url_for('drive_routes.auth_callback', _external=True)
        )
        
        # Exchange authorization code for credentials
        flow.fetch_token(code=request.args.get('code'))
        
        # Save credentials
        credentials = flow.credentials
        save_credentials(credentials)
        
        # Create SafeDrive folder if it doesn't exist
        create_folder_if_not_exists()
        
        flash('Successfully connected to Google Drive!', 'success')
        
        # Redirect to next URL if present
        next_url = session.pop('google_drive_next', None)
        if next_url:
            return redirect(next_url)
        
        return redirect(url_for('drive_routes.success'))
    except Exception as e:
        logger.error(f"Error in auth callback: {str(e)}")
        flash(f'Error authenticating with Google Drive: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@bp.route('/setup', methods=['GET', 'POST'])
@login_required
def setup():
    """Set up Google Drive API credentials"""
    if request.method == 'POST':
        # Check if file was uploaded
        if 'credentials_file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['credentials_file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        # Check if it's a JSON file
        if not file.filename.endswith('.json'):
            flash('File must be a JSON file', 'error')
            return redirect(request.url)
        
        try:
            # Read the file
            credentials_json = json.loads(file.read().decode('utf-8'))
            
            # Validate the JSON structure
            if 'web' not in credentials_json:
                flash('Invalid credentials file. Please download a valid client_secret.json file from Google Cloud Console.', 'error')
                return redirect(request.url)
            
            # Check if it has the required fields
            required_fields = ['client_id', 'client_secret', 'auth_uri', 'token_uri']
            for field in required_fields:
                if field not in credentials_json['web']:
                    flash(f'Invalid credentials file. Missing field: {field}', 'error')
                    return redirect(request.url)
            
            # Add the redirect URI if it's not already there
            redirect_uri = url_for('drive_routes.auth_callback', _external=True)
            if 'redirect_uris' not in credentials_json['web']:
                credentials_json['web']['redirect_uris'] = [redirect_uri]
            elif redirect_uri not in credentials_json['web']['redirect_uris']:
                credentials_json['web']['redirect_uris'].append(redirect_uri)
            
            # Save the credentials file
            client_secrets_file = os.path.join(current_app.root_path, 'client_secret.json')
            with open(client_secrets_file, 'w') as f:
                json.dump(credentials_json, f)
            
            flash('Google Drive API credentials saved successfully!', 'success')
            return redirect(url_for('drive_routes.connect'))
        except json.JSONDecodeError:
            flash('Invalid JSON file', 'error')
            return redirect(request.url)
        except Exception as e:
            logger.error(f"Error saving credentials file: {str(e)}")
            flash(f'Error saving credentials file: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('drive/setup_google_drive.html', title='Set Up Google Drive')

@bp.route('/success')
@login_required
def success():
    """Show success page after connecting to Google Drive"""
    if not is_authenticated():
        flash('Not connected to Google Drive', 'error')
        return redirect(url_for('drive_routes.connect'))
    
    # Get storage information
    try:
        storage_info = get_drive_storage_info()
    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        storage_info = {
            "total": 0,
            "used": 0,
            "free": 0,
            "percent_used": 0
        }
    
    # Get list of files in SafeDrive folder
    try:
        files = list_drive_files()
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        files = []
    
    return render_template('drive/auth_callback.html', 
                          title='Google Drive Connected',
                          storage_info=storage_info,
                          files=files)

@bp.route('/disconnect')
@login_required
def disconnect():
    """Disconnect from Google Drive"""
    # Clear Google Drive session data
    session.pop('google_credentials', None)
    session.pop('google_drive_auth', None)
    session.pop('google_drive_state', None)
    session.pop('google_drive_next', None)
    session.pop('uploaded_files', None)
    
    flash('Disconnected from Google Drive', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/files')
@login_required
def files():
    """List files in Google Drive"""
    if not is_authenticated():
        flash('Not connected to Google Drive', 'error')
        return redirect(url_for('drive_routes.connect'))
    
    try:
        files = list_drive_files()
        return render_template('drive/files.html', 
                              title='Google Drive Files',
                              files=files)
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        flash(f'Error listing files: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@bp.route('/storage')
@login_required
def storage():
    """Show Google Drive storage information"""
    if not is_authenticated():
        flash('Not connected to Google Drive', 'error')
        return redirect(url_for('drive_routes.connect'))
    
    try:
        storage_info = get_drive_storage_info()
        return render_template('drive/storage.html', 
                              title='Google Drive Storage',
                              storage_info=storage_info)
    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        flash(f'Error getting storage info: {str(e)}', 'error')
        return redirect(url_for('main.dashboard'))

@bp.route('/debug')
@login_required
def debug():
    """Debug Google Drive connection"""
    # Check if client_secret.json exists
    client_secrets_file = os.path.join(current_app.root_path, 'client_secret.json')
    client_secret_exists = os.path.exists(client_secrets_file)
    
    # Check if authenticated
    authenticated = is_authenticated()
    
    # Get credentials
    credentials = None
    if 'google_credentials' in session:
        try:
            credentials_dict = json.loads(session['google_credentials'])
            credentials = {
                'token': credentials_dict.get('token', 'Not available'),
                'refresh_token': 'Present' if credentials_dict.get('refresh_token') else 'Not available',
                'token_uri': credentials_dict.get('token_uri', 'Not available'),
                'client_id': credentials_dict.get('client_id', 'Not available'),
                'expiry': credentials_dict.get('expiry', 'Not available')
            }
        except:
            credentials = 'Error parsing credentials'
    
    # Get uploaded files
    uploaded_files = session.get('uploaded_files', [])
    
    debug_info = {
        'client_secret_exists': client_secret_exists,
        'authenticated': authenticated,
        'credentials': credentials,
        'uploaded_files': uploaded_files,
        'session_keys': list(session.keys())
    }
    
    return render_template('drive/debug.html', 
                          title='Debug Google Drive',
                          debug_info=debug_info)
