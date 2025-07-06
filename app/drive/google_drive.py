"""
Google Drive integration for SafeDrive with real Google Drive API

This module provides functions for uploading and downloading files to/from
Google Drive, including the OAuth authentication flow.
"""

import os
import json
import uuid
from flask import current_app, redirect, url_for, session, request, flash
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.auth.transport.requests import Request
import io
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Scopes required for Google Drive access
SCOPES = ['https://www.googleapis.com/auth/drive']

def get_credentials():
    """
    Get valid user credentials from storage.
    
    Returns:
        Credentials, the obtained credentials or None if not available
    """
    if 'google_credentials' not in session:
        return None
    
    try:
        credentials_dict = json.loads(session['google_credentials'])
        credentials = Credentials.from_authorized_user_info(credentials_dict)
        
        # Check if credentials are expired and refresh if possible
        if credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
            save_credentials(credentials)
            
        return credentials
    except Exception as e:
        logger.error(f"Error getting credentials: {str(e)}")
        return None

def save_credentials(credentials):
    """
    Save credentials to session storage
    
    Args:
        credentials: The OAuth2 credentials to save
    """
    try:
        session['google_credentials'] = credentials.to_json()
        session['google_drive_auth'] = True
        logger.info("Credentials saved successfully")
    except Exception as e:
        logger.error(f"Error saving credentials: {str(e)}")

def is_authenticated():
    """
    Check if the user is authenticated with Google Drive
    
    Returns:
        bool: True if authenticated, False otherwise
    """
    if 'google_drive_auth' not in session or not session['google_drive_auth']:
        logger.info("Not authenticated with Google Drive")
        return False
    
    # Check if credentials are still valid
    credentials = get_credentials()
    if credentials is None:
        logger.info("No credentials found")
        return False
    
    # Test the credentials by making a simple API call
    try:
        service = build('drive', 'v3', credentials=credentials)
        # Make a simple API call to verify credentials
        service.files().list(pageSize=1).execute()
        logger.info("Successfully authenticated with Google Drive")
        return True
    except Exception as e:
        logger.error(f"Authentication test failed: {str(e)}")
        return False

def get_auth_url():
    """
    Get the URL for Google Drive authentication
    
    Returns:
        str: Authentication URL for Google OAuth
    """
    try:
        # Load client secrets
        client_secrets_file = os.path.join(current_app.root_path, 'client_secret.json')
        
        if not os.path.exists(client_secrets_file):
            logger.error(f"Client secrets file not found at {client_secrets_file}")
            raise FileNotFoundError(f"Client secrets file not found at {client_secrets_file}")
        
        # Create flow instance
        flow = Flow.from_client_secrets_file(
            client_secrets_file,
            scopes=SCOPES,
            redirect_uri=url_for('drive_routes.auth_callback', _external=True)
        )
        
        # Generate authorization URL
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent'
        )
        
        # Store the state in the session for verification
        session['google_drive_state'] = state
        
        logger.info(f"Generated auth URL: {authorization_url}")
        return authorization_url
    except Exception as e:
        logger.error(f"Error generating auth URL: {str(e)}")
        raise

def get_drive_service():
    """
    Build the Google Drive service
    
    Returns:
        Service object to interact with Google Drive API
    """
    credentials = get_credentials()
    if not credentials:
        logger.error("No credentials available for Drive service")
        return None
    
    try:
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Error building Drive service: {str(e)}")
        return None

def create_folder_if_not_exists(folder_name="SafeDrive"):
    """
    Create a SafeDrive folder in Google Drive if it doesn't exist
    
    Returns:
        str: Folder ID
    """
    service = get_drive_service()
    if not service:
        logger.error("No Drive service available to create folder")
        raise ValueError("Not authenticated with Google Drive")
    
    try:
        # Check if folder already exists
        results = service.files().list(
            q=f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false",
            spaces='drive',
            fields='files(id, name)'
        ).execute()
        
        items = results.get('files', [])
        
        # If folder exists, return its ID
        if items:
            logger.info(f"Found existing folder: {folder_name} with ID: {items[0]['id']}")
            return items[0]['id']
        
        # Create folder
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        folder = service.files().create(
            body=file_metadata,
            fields='id'
        ).execute()
        
        folder_id = folder.get('id')
        logger.info(f"Created new folder: {folder_name} with ID: {folder_id}")
        return folder_id
    except Exception as e:
        logger.error(f"Error creating folder: {str(e)}")
        raise

def upload_file(file_path, filename=None):
    """
    Upload a file to Google Drive
    
    Args:
        file_path: Path to the file to upload
        filename: Name to use for the file in Google Drive (default: basename of file_path)
        
    Returns:
        Google Drive file ID
    """
    if not is_authenticated():
        logger.error("Not authenticated with Google Drive")
        raise ValueError("Not authenticated with Google Drive")
    
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if filename is None:
        filename = os.path.basename(file_path)
    
    try:
        # Get Google Drive service
        service = get_drive_service()
        if not service:
            raise ValueError("Failed to get Drive service")
        
        # Get SafeDrive folder ID
        folder_id = create_folder_if_not_exists()
        
        # File metadata
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        # Get MIME type
        mime_type = None  # Let the API determine the MIME type
        
        # Upload file
        media = MediaFileUpload(
            file_path,
            mimetype=mime_type,
            resumable=True
        )
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,webViewLink'
        ).execute()
        
        file_id = file.get('id')
        web_link = file.get('webViewLink')
        
        logger.info(f"File uploaded to Google Drive with ID: {file_id}")
        logger.info(f"File can be viewed at: {web_link}")
        
        # Store the web link in the session for debugging
        if 'uploaded_files' not in session:
            session['uploaded_files'] = []
        
        session['uploaded_files'].append({
            'id': file_id,
            'name': filename,
            'link': web_link
        })
        
        return file_id
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise

def download_file(file_id, output_path):
    """
    Download a file from Google Drive
    
    Args:
        file_id: Google Drive file ID
        output_path: Path to save the downloaded file
        
    Returns:
        Path to the downloaded file
    """
    if not is_authenticated():
        logger.error("Not authenticated with Google Drive")
        raise ValueError("Not authenticated with Google Drive")
    
    try:
        # Get Google Drive service
        service = get_drive_service()
        if not service:
            raise ValueError("Failed to get Drive service")
        
        # Get file metadata to verify it exists
        try:
            file_metadata = service.files().get(fileId=file_id).execute()
            logger.info(f"Found file to download: {file_metadata.get('name')}")
        except Exception as e:
            logger.error(f"File with ID {file_id} not found: {str(e)}")
            raise ValueError(f"File with ID {file_id} not found in Google Drive")
        
        # Download file
        request = service.files().get_media(fileId=file_id)
        
        with open(output_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
                logger.info(f"Download progress: {int(status.progress() * 100)}%")
        
        logger.info(f"File downloaded from Google Drive to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise

def delete_from_drive(file_id):
    """
    Delete a file from Google Drive
    
    Args:
        file_id: Google Drive file ID
    """
    if not is_authenticated():
        logger.error("Not authenticated with Google Drive")
        raise ValueError("Not authenticated with Google Drive")
    
    try:
        # Get Google Drive service
        service = get_drive_service()
        if not service:
            raise ValueError("Failed to get Drive service")
        
        # Delete the file
        service.files().delete(fileId=file_id).execute()
        
        logger.info(f"File with ID {file_id} deleted from Google Drive")
        
        # Remove from session if present
        if 'uploaded_files' in session:
            session['uploaded_files'] = [f for f in session.get('uploaded_files', []) if f.get('id') != file_id]
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise

def get_drive_storage_info():
    """
    Get storage information from Google Drive
    
    Returns:
        dict: Storage information including total, used, and free space
    """
    if not is_authenticated():
        logger.error("Not authenticated with Google Drive")
        raise ValueError("Not authenticated with Google Drive")
    
    try:
        # Get Google Drive service
        service = get_drive_service()
        if not service:
            raise ValueError("Failed to get Drive service")
        
        # Get storage information
        about = service.about().get(fields="storageQuota").execute()
        quota = about.get("storageQuota", {})
        
        # Convert to MB for display
        limit = int(quota.get("limit", 0)) / (1024 * 1024)
        usage = int(quota.get("usage", 0)) / (1024 * 1024)
        usage_in_drive = int(quota.get("usageInDrive", 0)) / (1024 * 1024)
        
        storage_info = {
            "total": round(limit, 2),
            "used": round(usage, 2),
            "used_in_drive": round(usage_in_drive, 2),
            "free": round(limit - usage, 2) if limit > 0 else 0,
            "percent_used": round((usage / limit) * 100, 2) if limit > 0 else 0
        }
        
        logger.info(f"Drive storage info: {storage_info}")
        return storage_info
    except Exception as e:
        logger.error(f"Error getting storage info: {str(e)}")
        return {
            "total": 0,
            "used": 0,
            "used_in_drive": 0,
            "free": 0,
            "percent_used": 0
        }

def list_drive_files(folder_name="SafeDrive"):
    """
    List files in the SafeDrive folder
    
    Returns:
        list: List of files in the SafeDrive folder
    """
    if not is_authenticated():
        logger.error("Not authenticated with Google Drive")
        raise ValueError("Not authenticated with Google Drive")
    
    try:
        # Get Google Drive service
        service = get_drive_service()
        if not service:
            raise ValueError("Failed to get Drive service")
        
        # Get SafeDrive folder ID
        folder_id = create_folder_if_not_exists(folder_name)
        
        # List files in the folder
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            spaces='drive',
            fields='files(id, name, mimeType, size, createdTime, webViewLink)'
        ).execute()
        
        files = results.get('files', [])
        
        logger.info(f"Found {len(files)} files in {folder_name} folder")
        return files
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return []


def share_file_via_web_link(file_id):
    """Make a file publicly viewable via link."""
    try:
        permission = {
            'type': 'anyone',
            'role': 'reader',
        }

        drive_service = get_drive_service()
        drive_service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id',
        ).execute()

        file = drive_service.files().get(
            fileId=file_id,
            fields='webViewLink, webContentLink'
        ).execute()

        return file.get("webViewLink") or file.get("webContentLink")
    
    except Exception as e:
        logger.error(f"Error sharing file via web link: {e}")
        return None


def share_file_with_user(file_id, recipient_email):
    """
    Share a file in Google Drive with another user's email address
    
    Args:
        file_id (str): The Google Drive file ID
        recipient_email (str): The email address of the user to share with
    """
    try:
        service = get_drive_service()
        if not service:
            raise ValueError("Drive service not available")
        
        permission = {
            'type': 'user',
            'role': 'reader',  # or 'writer' if editing is allowed
            'emailAddress': recipient_email
        }
        
        service.permissions().create(
            fileId=file_id,
            body=permission,
            sendNotificationEmail=False
        ).execute()
        
        logger.info(f"File {file_id} shared with {recipient_email}")
    except Exception as e:
        logger.error(f"Error sharing file: {str(e)}")
        raise
