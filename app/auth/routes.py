from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, current_user, login_required
# Replace werkzeug.urls import with urllib.parse
from urllib.parse import urlparse
from app import db
from app.auth import bp
from app.models.user import User
from app.auth.otp import generate_otp, verify_otp, send_otp_email

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        return render_template('auth/login.html', title='Login')
    
    # Handle POST request (API login)
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid email or password'}), 401
    
    if not user.is_verified:
        # Generate and send new OTP for unverified users
        otp = generate_otp(user)
        send_otp_email(user, otp)
        return jsonify({
            'message': 'Email not verified. A new OTP has been sent.',
            'user_id': user.id
        }), 403
    
    login_user(user)
    user.last_login = db.func.now()
    db.session.commit()
    
    # Handle next parameter if present
    next_page = request.args.get('next')
    # Replace url_parse with urlparse
    if not next_page or urlparse(next_page).netloc != '':
        next_page = url_for('main.dashboard', _external=True)
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        },
        'redirect_url': next_page
    }), 200

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        return render_template('auth/register.html', title='Register')
    
    # Handle POST request (API registration)
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Missing email or password'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered'}), 400
    
    user = User(
        email=data['email'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', '')
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()
    
    # Generate and send OTP for email verification
    otp = generate_otp(user)
    send_otp_email(user, otp)
    
    return jsonify({
        'message': 'Registration successful. Please verify your email with the OTP sent.',
        'user_id': user.id
    }), 201

@bp.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    
    if not data or not data.get('user_id') or not data.get('otp'):
        return jsonify({'message': 'Missing user_id or OTP'}), 400
    
    user = User.query.get(data['user_id'])
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if verify_otp(user, data['otp']):
        user.is_verified = True
        db.session.commit()
        return jsonify({'message': 'Email verified successfully'}), 200
    else:
        return jsonify({'message': 'Invalid or expired OTP'}), 400

@bp.route('/logout', methods=['GET', 'POST'])
def logout():
    # No need for login_required as we'll handle non-authenticated users gracefully
    
    # Store username for flash message before logging out
    user_email = current_user.email if current_user.is_authenticated else "User"
    
    # Clear any drive-related session data if it exists
    for key in list(session.keys()):
        if key.startswith('drive_') or key == 'credentials':
            session.pop(key, None)
    
    # Log the user out
    if current_user.is_authenticated:
        logout_user()
    
    # Clear session cookie
    session.clear()
    
    # Handle API requests
    if request.headers.get('Content-Type') == 'application/json' or request.is_json:
        return jsonify({'message': 'Logged out successfully'}), 200
    
    # Handle browser requests
    flash(f'You have been logged out successfully.', 'success')
    return redirect(url_for('main.index'))

@bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'message': 'Missing email'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        return jsonify({'message': 'User not found'}), 404
    
    if user.is_verified:
        return jsonify({'message': 'Email already verified'}), 400
    
    otp = generate_otp(user)
    send_otp_email(user, otp)
    
    return jsonify({
        'message': 'OTP sent successfully',
        'user_id': user.id
    }), 200

@bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'GET':
        return render_template('auth/forgot_password.html', title='Forgot Password')
    
    # Handle POST request
    data = request.get_json()
    
    if not data or not data.get('email'):
        return jsonify({'message': 'Missing email'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user:
        # Don't reveal that the user doesn't exist
        return jsonify({'message': 'If your email is registered, you will receive a password reset link.'}), 200
    
    # Generate reset token
    token = user.get_reset_password_token()
    
    # TODO: Send password reset email
    
    return jsonify({'message': 'If your email is registered, you will receive a password reset link.'}), 200
