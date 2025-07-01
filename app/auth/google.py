from flask import request, redirect, url_for, current_app, jsonify, session
from flask_login import login_user, current_user
from app import db
from app.auth import bp
from app.models.user import User
from oauthlib.oauth2 import WebApplicationClient
import requests
import json
from datetime import datetime
from urllib.parse import urlparse

# Instead of initializing the client at module level, create a function to get it
def get_google_client():
    return WebApplicationClient(current_app.config['GOOGLE_CLIENT_ID'])

def get_google_provider_cfg():
    return requests.get(current_app.config['GOOGLE_DISCOVERY_URL']).json()

@bp.route('/login/google')
def login_google():
    # Get the client inside the route function where we have an application context
    client = get_google_client()
    
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@bp.route('/login/google/callback')
def callback():
    # Get the client inside the route function
    client = get_google_client()
    
    # Get authorization code Google sent back
    code = request.args.get("code")
    
    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    
    # Prepare and send a request to get tokens
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(current_app.config['GOOGLE_CLIENT_ID'], current_app.config['GOOGLE_CLIENT_SECRET']),
    )
    
    # Parse the tokens
    client.parse_request_body_response(json.dumps(token_response.json()))
    
    # Now that you have tokens, let's find and hit the URL
    # from Google that gives you the user's profile information
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)
    
    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        google_id = userinfo_response.json()["sub"]
        email = userinfo_response.json()["email"]
        first_name = userinfo_response.json().get("given_name", "")
        last_name = userinfo_response.json().get("family_name", "")
    else:
        return jsonify({"error": "User email not available or not verified by Google."}), 400
    
    # Create a user in your db with the information provided by Google
    user = User.query.filter_by(email=email).first()
    
    # If user doesn't exist, create a new one
    if not user:
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            google_id=google_id,
            is_verified=True  # Google already verified the email
        )
        db.session.add(user)
        db.session.commit()
    # If user exists but doesn't have Google ID, update it
    elif not user.google_id:
        user.google_id = google_id
        user.is_verified = True
        db.session.commit()
    
    # Begin user session by logging the user in
    login_user(user)
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    # Send user back to homepage or requested page
    next_page = session.get('next', '/')
    session.pop('next', None)
    
    # Check if next_page is safe
    if next_page and urlparse(next_page).netloc == '':
        return redirect(next_page)
    else:
        return redirect(url_for('main.dashboard'))
