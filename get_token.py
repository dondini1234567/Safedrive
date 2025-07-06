from google_auth_oauthlib.flow import InstalledAppFlow

# Tell Google what you want to do (access Drive)
SCOPES = ['https://www.googleapis.com/auth/drive']

# Start login flow
flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
creds = flow.run_local_server(port=0)

# Save your login token to a file
with open('token_owner.json', 'w') as token:
    token.write(creds.to_json())

print("✅ Owner token saved to token_owner.json")
