import os
import json
import sys

def save_credentials():
    """
    Save Google API credentials to the correct location with the correct filename.
    
    This script looks for a client_secret_*.json file in the current directory
    and copies its contents to app/client_secret.json, adding the necessary
    redirect URI if it's not already present.
    """
    # Find client_secret_*.json file
    client_secret_files = [f for f in os.listdir('.') if f.startswith('client_secret_') and f.endswith('.json')]
    
    if not client_secret_files:
        print("Error: No client_secret_*.json file found in the current directory.")
        print("Please download your credentials file from the Google Cloud Console and place it in this directory.")
        return False
    
    # Use the first file found
    source_file = client_secret_files[0]
    print(f"Found credentials file: {source_file}")
    
    try:
        # Read the credentials
        with open(source_file, 'r') as f:
            credentials = json.load(f)
        
        # Check if it has the required structure
        if 'web' not in credentials:
            print("Error: Invalid credentials file. Missing 'web' section.")
            return False
        
        # Add the redirect URI if it's not already there
        redirect_uri = 'http://127.0.0.1:5000/drive/auth/callback'
        if 'redirect_uris' not in credentials['web']:
            credentials['web']['redirect_uris'] = [redirect_uri]
        elif redirect_uri not in credentials['web']['redirect_uris']:
            credentials['web']['redirect_uris'].append(redirect_uri)
        
        # Create app directory if it doesn't exist
        if not os.path.exists('app'):
            os.makedirs('app')
        
        # Save to the correct location
        target_file = 'app/client_secret.json'
        with open(target_file, 'w') as f:
            json.dump(credentials, f, indent=2)
        
        print(f"Credentials saved to {target_file}")
        print("Redirect URIs:")
        for uri in credentials['web']['redirect_uris']:
            print(f"  - {uri}")
        
        return True
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = save_credentials()
    if success:
        print("\nSuccess! You can now connect to Google Drive in your application.")
        print("Run 'flask run' to start your application and try connecting to Google Drive.")
    else:
        print("\nFailed to save credentials. Please check the error message above.")
        sys.exit(1)
