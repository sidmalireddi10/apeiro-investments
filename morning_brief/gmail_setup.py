"""
gmail_setup.py – One-time OAuth setup for the Gmail HTTP API.
Instructions:
1. Ensure 'credentials.json' is in this directory.
2. Run: python gmail_setup.py
3. Follow the browser link to authorize.
4. 'token.json' will be created automatically.
"""

import os.path
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes required to send emails
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def main():
    creds = None
    # token.json stores the user's access and refresh tokens
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("Error: 'credentials.json' not found.")
                print("Please download it from Google Cloud Console and place it in this folder.")
                return

            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        print("Success! 'token.json' has been created.")

if __name__ == '__main__':
    main()
