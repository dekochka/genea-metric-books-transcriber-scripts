#!/usr/bin/env python3
"""
Script to refresh Google OAuth2 credentials for the transcription project.
Run this when you get "Token has been expired or revoked" errors.
"""

import json
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# The scopes required by the transcription script
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents", 
    "https://www.googleapis.com/auth/cloud-platform"
]

def _find_client_secret_path():
    """
    Return the client secret file path.
    Looks for client_secret.json in the project root.
    """
    candidates = [
        'client_secret.json'
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None


def refresh_credentials():
    """
    Generate new OAuth2 credentials using the client_secret.json file.
    This will open a browser window for authentication.
    """
    
    # Resolve client secret path
    client_secret_path = _find_client_secret_path()
    if not client_secret_path:
        print("ERROR: No client secret file found!")
        print("Expected client_secret.json in the project root")
        print("Please download it from Google Cloud Console > APIs & Services > Credentials")
        return False
    
    print("Starting OAuth2 authentication flow...")
    print("This will open a browser window for Google authentication.")
    
    try:
        # Create the flow using the resolved client secrets file
        print(f"Using client secrets: {client_secret_path}")
        flow = InstalledAppFlow.from_client_secrets_file(
            client_secret_path, SCOPES)
        
        # Run the OAuth flow and get credentials
        # This will open a browser window for authentication
        creds = flow.run_local_server(port=0)
        
        # Save the credentials in the format expected by the transcription script
        creds_data = {
            'type': 'authorized_user',
            'client_id': creds.client_id,
            'client_secret': creds.client_secret,
            'refresh_token': creds.refresh_token,
            'universe_domain': 'googleapis.com'
        }
        
        # Write the new credentials to application_default_credentials.json
        with open('application_default_credentials.json', 'w') as f:
            json.dump(creds_data, f, indent=2)
        
        print("\n✅ SUCCESS: New credentials saved to application_default_credentials.json")
        print("You can now run the transcription script again.")
        return True
        
    except Exception as e:
        print(f"❌ ERROR during authentication: {str(e)}")
        return False

if __name__ == '__main__':
    print("Google OAuth2 Credentials Refresh Tool")
    print("=" * 40)
    
    # Backup existing credentials if they exist
    if os.path.exists('application_default_credentials.json'):
        print("Backing up existing credentials...")
        os.rename('application_default_credentials.json', 'application_default_credentials.json.backup')
        print("Backup saved as: application_default_credentials.json.backup")
    
    success = refresh_credentials()
    
    if not success:
        print("\nTroubleshooting:")
        print("1. Make sure client_secret.json is in the current directory")
        print("2. Ensure your Google account has access to the Drive folder")
        print("3. Check that the Google Cloud project has the required APIs enabled:")
        print("   - Google Drive API")
        print("   - Google Docs API") 
        print("   - Vertex AI API") 