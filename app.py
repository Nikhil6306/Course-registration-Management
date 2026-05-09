from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
CORS(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 # 5MB

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = 'course-registration'
COLLECTION_NAME = 'courses'
USERS_COLLECTION = 'users'

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    courses_collection = db[COLLECTION_NAME]
    users_collection = db[USERS_COLLECTION]
    profile_requests_collection = db['profile_requests']
    
    # SEPARATE CONNECTION FOR OTP LOGGING
    otp_client = MongoClient(MONGO_URI)
    otp_db = otp_client['otp-logs']
    otp_collection = otp_db['verifications']
    
    print("Connected to MongoDB successfully (Primary & OTP Connections)")
    
    # Create demo accounts if not exists
    demo_accounts = [
        {
            'username': 'admin',
            'password': 'adminpassword',
            'role': 'admin',
            'email': 'admin@example.com',
            'name': 'System Administrator'
        },
        {
            'username': 'teacher',
            'password': 'teacherpassword',
            'role': 'teacher',
            'email': 'teacher@example.com',
            'name': 'Dr. Sarah Wilson'
        },
        {
            'username': 'hod',
            'password': 'hodpassword',
            'role': 'hod',
            'email': 'hod@example.com',
            'name': 'Prof. Robert Miller'
        },
        {
            'username': 'student',
            'password': 'studentpassword',
            'role': 'student',
            'email': 'student@example.com',
            'name': 'James Harrison'
        }
    ]

    for acc in demo_accounts:
        if not users_collection.find_one({'username': acc['username']}):
            acc['created_at'] = datetime.now()
            users_collection.insert_one(acc)
            print(f"✓ Demo account created: {acc['username']} / {acc['password']}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# ===== SMTP EMAIL CONFIGURATION =====
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'your-email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

def send_verification_email(recipient_email, user_name, verification_code, verification_type='password_reset', extra_data=None):
    """
    Send verification email using SMTP (Simple Mail Transfer Protocol)
    
    Args:
        recipient_email: Email address to send to
        user_name: Full name of the user
        verification_code: OTP or verification code
        verification_type: 'password_reset', 'wrong_password', 'email_verification', or 'welcome'
    """
    try:
        # Create message
        message = MIMEMultipart('alternative')
        
        # Set subject based on verification type
        if verification_type == 'email_verification':
            message['Subject'] = f'Dev Sanskriti University - Email Verification Code'
        elif verification_type == 'password_reset':
            message['Subject'] = f'Dev Sanskriti University - Password Reset'
        else:
            message['Subject'] = f'Dev Sanskriti University - Security Verification'
        
        message['From'] = EMAIL_SENDER
        message['To'] = recipient_email

        # HTML email template with user name and verification details
        if verification_type in ['password_reset', 'wrong_password']:
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ text-align: center; border-bottom: 3px solid #667eea; padding-bottom: 20px; margin-bottom: 20px; }}
                        .header h2 {{ color: #667eea; margin: 0; }}
                        .content {{ color: #333; line-height: 1.6; }}
                        .verification-box {{ background-color: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0; border-left: 4px solid #667eea; }}
                        .code {{ font-size: 36px; color: #667eea; letter-spacing: 5px; font-weight: bold; margin: 15px 0; }}
                        .user-info {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; font-size: 14px; }}
                        .user-info p {{ margin: 5px 0; }}
                        .warning {{ color: #ff6b6b; font-size: 12px; margin-top: 10px; }}
                        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>🔐 Dev Sanskriti University</h2>
                            <p>Security Verification</p>
                        </div>
                        
                        <div class="content">
                            <p>Dear <strong>{user_name}</strong>,</p>
                            
                            <p>We received a request to reset your password. Please use the verification code below to proceed:</p>
                            
                            <div class="verification-box">
                                <p style="color: #666; margin: 0;">Your Verification Code:</p>
                                <div class="code">{verification_code}</div>
                                <p class="warning">⏱️ This code will expire in 15 minutes</p>
                            </div>
                            
                            <div class="user-info">
                                <p><strong>Account Information:</strong></p>
                                <p>👤 Name: {user_name}</p>
                                <p>📧 Email: {recipient_email}</p>
                                <p>⏰ Request Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                            </div>
                            
                            <p><strong>Important Security Notice:</strong></p>
                            <ul>
                                <li>Never share this code with anyone</li>
                                <li>Dev Sanskriti University staff will never ask for your verification code</li>
                                <li>If you did not request this, please ignore this email and change your password immediately</li>
                                <li>Your account may have been compromised - contact support if needed</li>
                            </ul>
                        </div>
                        
                        <div class="footer">
                            <p>Dev Sanskriti University - Course Registration System</p>
                            <p>© 2024 All rights reserved | <a href="#" style="color: #667eea; text-decoration: none;">Support Center</a></p>
                        </div>
                    </div>
                </body>
            </html>
            """
        elif verification_type == 'email_verification':
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ text-align: center; border-bottom: 3px solid #667eea; padding-bottom: 20px; margin-bottom: 20px; }}
                        .header h2 {{ color: #667eea; margin: 0; }}
                        .header p {{ margin: 5px 0; color: #666; }}
                        .content {{ color: #333; line-height: 1.6; }}
                        .verification-box {{ background: linear-gradient(135deg, #667eea, #764ba2); padding: 25px; border-radius: 8px; text-align: center; margin: 20px 0; color: white; }}
                        .code {{ font-size: 40px; letter-spacing: 8px; font-weight: bold; margin: 15px 0; font-family: 'Courier New', monospace; }}
                        .user-info {{ background-color: #f9f9f9; padding: 15px; border-radius: 5px; margin: 15px 0; font-size: 14px; border-left: 4px solid #667eea; }}
                        .user-info p {{ margin: 5px 0; }}
                        .warning {{ color: #ff6b6b; font-size: 12px; margin-top: 10px; }}
                        .success-icon {{ font-size: 48px; margin: 10px 0; }}
                        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>✅ Email Verification</h2>
                            <p>Dev Sanskriti University</p>
                        </div>
                        
                        <div class="content">
                            <p>Dear <strong>{user_name}</strong>,</p>
                            
                            <p>Your email verification code has been generated. Use the code below to verify your email address:</p>
                            
                            <div class="verification-box">
                                <div class="success-icon">🔑</div>
                                <p style="color: rgba(255,255,255,0.9); margin: 0;">Your Verification Code:</p>
                                <div class="code">{verification_code}</div>
                                <p class="warning" style="color: rgba(255,255,255,0.9);">⏱️ This code will expire in 15 minutes</p>
                            </div>
                            
                            <div class="user-info">
                                <p><strong>📋 Verification Details:</strong></p>
                                <p>👤 User: {user_name}</p>
                                <p>📧 Email: {recipient_email}</p>
                                <p>⏰ Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                            </div>
                            
                            <p><strong>⚠️ Security Tips:</strong></p>
                            <ul>
                                <li>Never share this code with anyone</li>
                                <li>Staff will never ask for your verification code</li>
                                <li>If you didn't request this, please ignore this email</li>
                                <li>Report suspicious activity immediately</li>
                            </ul>
                        </div>
                        
                        <div class="footer">
                            <p>Dev Sanskriti University - Course Registration System</p>
                            <p>© 2024 All rights reserved</p>
                        </div>
                    </div>
                </body>
            </html>
            """
        elif verification_type == 'account_created':
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ text-align: center; border-bottom: 3px solid #667eea; padding-bottom: 20px; margin-bottom: 20px; }}
                        .header h2 {{ color: #667eea; margin: 0; }}
                        .content {{ color: #333; line-height: 1.6; }}
                        .credentials-box {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; margin: 20px 0; }}
                        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }}
                        .login-btn {{ display: inline-block; background-color: #667eea; color: white; padding: 12px 25px; border-radius: 5px; text-decoration: none; font-weight: bold; margin-top: 15px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>🎓 Welcome to Dev Sanskriti University</h2>
                            <p>Account Successfully Created</p>
                        </div>
                        
                        <div class="content">
                            <p>Dear <strong>{user_name}</strong>,</p>
                            <p>An account has been created for you in the Course Registration System by the administrator. You can now log in using the credentials below:</p>
                            
                            <div class="credentials-box">
                                <p><strong>👤 Username:</strong> {extra_data.get('username')}</p>
                                <p><strong>🔑 Password:</strong> {extra_data.get('password')}</p>
                                <p><strong>🛡️ Role:</strong> {extra_data.get('role', '').upper()}</p>
                            </div>
                            
                            <p>Please change your password after your first login for security purposes.</p>
                            
                            <div style="text-align: center;">
                                <a href="http://localhost:5000/login.html" class="login-btn">Login to Dashboard</a>
                            </div>
                        </div>
                        
                        <div class="footer">
                            <p>Dev Sanskriti University - Course Registration System</p>
                            <p>© 2024 All rights reserved</p>
                        </div>
                    </div>
                </body>
            </html>
            """
        else:
            html_body = f"<p>Hello {user_name},<br>Your verification code is: {verification_code}</p>"

        # Check if email is configured (Dev Mode Bypass)
        if EMAIL_SENDER == 'your-email@gmail.com' or not EMAIL_PASSWORD or EMAIL_PASSWORD == 'your-app-password':
            print(f"ℹ️ [DEV MODE] Email not configured. Printing to console for: {user_name}")
            if verification_type == 'account_created' and extra_data:
                print(f"\n[CREDENTIALS] Account Created for {user_name}:")
                print(f"Username: {extra_data.get('username')}")
                print(f"Password: {extra_data.get('password')}")
                print(f"Role: {extra_data.get('role')}\n")
            else:
                print(f"\n[CODE] Verification Code for {user_name}: {verification_code}\n")
            return True

        # Send email via SMTP
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()  # Start TLS encryption
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipient_email, message.as_string())
        
        print(f"✓ [SMTP] Email sent successfully to {recipient_email} for {user_name}")
        return True
        
    except Exception as e:
        print(f"✗ [SMTP] Failed to send email to {recipient_email}: {str(e)}")
        # Fallback: Print to console for testing
        if verification_type == 'account_created' and extra_data:
            print(f"\n[FALLBACK] Account Created for {user_name}:")
            print(f"Username: {extra_data.get('username')}")
            print(f"Password: {extra_data.get('password')}")
            print(f"Role: {extra_data.get('role')}\n")
        else:
            print(f"\n[FALLBACK] Verification Code for {user_name}: {verification_code}\n")
        return True

def log_otp(username, email, code, purpose):
    """Log OTP to separate connection and user profile"""
    try:
        # 1. Log to separate connection
        otp_entry = {
            'username': username,
            'email': email,
            'code': code,
            'purpose': purpose,
            'timestamp': datetime.now()
        }
        otp_collection.insert_one(otp_entry)
        
        # 2. Update user profile with latest OTP
        users_collection.update_one(
            {'username': username},
            {
                '$set': {
                    'last_otp': {
                        'code': code,
                        'purpose': purpose,
                        'timestamp': datetime.now()
                    }
                }
            }
        )
        print(f"✓ OTP logged and profile updated for {username} ({purpose})")
    except Exception as e:
        print(f"Error logging OTP: {e}")

def generate_verification_code():
    """Generate a 6-digit verification code"""
    return ''.join(random.choices(string.digits, k=6))

def is_code_valid(timestamp):
    """Check if verification code is still valid (15 minutes)"""
    if not timestamp:
        return False
    expiry_time = timestamp + timedelta(minutes=15)
    return datetime.now() < expiry_time

# ===== AUTHENTICATION =====
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
            
        user = users_collection.find_one({'username': username})
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Verify password
        if user.get('password') != password:
            # Wrong password - generate verification code and send email
            verification_code = generate_verification_code()
            timestamp = datetime.now()
            
            # Log OTP to separate connection and profile
            log_otp(username, user.get('email'), verification_code, 'wrong_password')
            
            users_collection.update_one(
                {'username': username},
                {
                    '$set': {
                        'wrong_password_code': verification_code,
                        'wrong_password_timestamp': timestamp,
                        'wrong_password_attempts': user.get('wrong_password_attempts', 0) + 1
                    }
                }
            )
            
            # Send verification email
            user_email = user.get('email', '')
            user_name = user.get('name', username)
            
            if user_email:
                send_verification_email(
                    user_email,
                    user_name,
                    verification_code,
                    'wrong_password'
                )
            
            return jsonify({
                'error': 'Invalid password',
                'requiresVerification': True,
                'message': f'Wrong password. A verification code has been sent to {user_email}',
                'username': username,
                'email': user_email
            }), 401
        
        # Password correct - login successful
        return jsonify({
            'message': 'Login successful',
            'user': {
                'username': user['username'],
                'role': user['role'],
                'name': user.get('name', ''),
                'email': user.get('email', '')
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-password-code', methods=['POST'])
def verify_password_code():
    """Verify code sent after wrong password attempt"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        verification_code = data.get('code')
        
        if not username or not email or not verification_code:
            return jsonify({'error': 'Username, email, and verification code required'}), 400
        
        user = users_collection.find_one({'username': username, 'email': email})
        
        if not user:
            return jsonify({'error': 'User not found or email mismatch'}), 404
        
        # Check if code exists and is valid
        stored_code = user.get('wrong_password_code')
        code_timestamp = user.get('wrong_password_timestamp')
        
        if not stored_code:
            return jsonify({'error': 'No verification request found. Please try logging in again.'}), 400
        
        # Check code expiry
        if not is_code_valid(code_timestamp):
            users_collection.update_one(
                {'username': username},
                {'$unset': {'wrong_password_code': '', 'wrong_password_timestamp': ''}}
            )
            return jsonify({'error': 'Verification code has expired. Please try logging in again.'}), 400
        
        # Verify code
        if stored_code != verification_code:
            return jsonify({'error': 'Invalid verification code'}), 401
        
        # Code verified - clear and mark verified
        users_collection.update_one(
            {'username': username},
            {
                '$unset': {'wrong_password_code': '', 'wrong_password_timestamp': ''},
                '$set': {'verified': True, 'verified_at': datetime.now()}
            }
        )
        
        return jsonify({
            'message': 'Verification successful',
            'verified': True,
            'username': username,
            'name': user.get('name', ''),
            'email': email
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-email-verification', methods=['POST'])
def send_email_verification():
    """Send email verification code to user's email"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        
        if not username or not email:
            return jsonify({'error': 'Username and email required'}), 400
        
        user = users_collection.find_one({'username': username})
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Generate verification code
        verification_code = generate_verification_code()
        
        # Log OTP to separate connection and profile
        log_otp(username, email, verification_code, 'email_verification')
        
        # Store code in user document
        users_collection.update_one(
            {'username': username},
            {
                '$set': {
                    'email_verification_code': verification_code,
                    'email_verification_timestamp': datetime.now()
                }
            }
        )
        
        # Send verification email
        try:
            email_sent = send_verification_email(
                recipient_email=email,
                user_name=user.get('name', username),
                verification_code=verification_code,
                verification_type='email_verification'
            )
            
            if email_sent:
                return jsonify({
                    'message': f'Verification code sent successfully to {email}',
                    'email': email
                }), 200
            else:
                return jsonify({
                    'error': 'Failed to send OTP email. Please check SMTP configuration in .env file.',
                    'details': 'Ensure EMAIL_SENDER and EMAIL_PASSWORD are correct.'
                }), 500
        except Exception as email_error:
            # Clear the code if email fails to send
            users_collection.update_one(
                {'username': username},
                {'$unset': {'email_verification_code': '', 'email_verification_timestamp': ''}}
            )
            return jsonify({'error': f'Failed to send email: {str(email_error)}'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# SELF-REGISTRATION DISABLED - USE ADMIN PANEL INSTEAD
# @app.route('/api/register', methods=['POST'])
# def register():
#     ...

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    """Request password reset with email verification"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        
        if not username or not email:
            return jsonify({'error': 'Username and email are required'}), 400
        
        user = users_collection.find_one({'username': username, 'email': email})
        
        if not user:
            return jsonify({'error': 'Username and email do not match any account'}), 404
        
        # Generate verification code
        verification_code = generate_verification_code()
        timestamp = datetime.now()
        
        # Log OTP to separate connection and profile
        log_otp(username, email, verification_code, 'password_reset')
        
        users_collection.update_one(
            {'username': username},
            {
                '$set': {
                    'reset_code': verification_code,
                    'reset_code_timestamp': timestamp
                }
            }
        )
        
        # Send verification email with name and email
        user_name = user.get('name', username)
        email_sent = send_verification_email(
            email,
            user_name,
            verification_code,
            'password_reset'
        )
        
        return jsonify({
            'message': f'Verification code sent to {email}',
            'email': email,
            'name': user_name,
            'emailSent': email_sent
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    """Reset password after verification"""
    try:
        data = request.json
        username = data.get('username')
        email = data.get('email')
        verification_code = data.get('code')
        new_password = data.get('newPassword')
        
        if not username or not email or not verification_code or not new_password:
            return jsonify({'error': 'All fields (username, email, code, newPassword) are required'}), 400
        
        user = users_collection.find_one({'username': username, 'email': email})
        
        if not user:
            return jsonify({'error': 'User not found or email mismatch'}), 404
        
        # Verify code
        stored_code = user.get('reset_code')
        code_timestamp = user.get('reset_code_timestamp')
        
        if not stored_code or stored_code != verification_code:
            return jsonify({'error': 'Invalid verification code'}), 401
        
        # Check code expiry
        if not is_code_valid(code_timestamp):
            users_collection.update_one(
                {'username': username},
                {'$unset': {'reset_code': '', 'reset_code_timestamp': ''}}
            )
            return jsonify({'error': 'Verification code has expired'}), 400
        
        # Update password
        user_name = user.get('name', username)
        users_collection.update_one(
            {'username': username},
            {
                '$set': {
                    'password': new_password,
                    'last_password_change': datetime.now()
                },
                '$unset': {'reset_code': '', 'reset_code_timestamp': ''}
            }
        )
        
        # Send confirmation email
        send_verification_email(
            email,
            user_name,
            '',
            'password_changed'
        )
        
        return jsonify({
            'message': 'Password reset successfully',
            'email': email,
            'username': username
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== USER PROFILE =====
@app.route('/api/profile/<username>', methods=['GET'])
def get_profile(username):
    try:
        user = users_collection.find_one({'username': username})
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        profile = {
            'username': user.get('username'),
            'role': user.get('role'),
            'name': user.get('name', ''),
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'department': user.get('department', ''),
            'profile_image': user.get('profile_image', '')
        }
        return jsonify({'profile': profile}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['PUT'])
def update_profile():
    try:
        username = request.form.get('username')
        if not username:
            return jsonify({'error': 'Username is required'}), 400
            
        update_data = {
            'name': request.form.get('name', ''),
            'email': request.form.get('email', ''),
            'phone': request.form.get('phone', '')
        }
        
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '':
                if not allowed_file(file.filename):
                    return jsonify({'error': 'Invalid file type. Only PNG, JPG, JPEG, GIF allowed.'}), 400
                filename = secure_filename(f"{username}_{file.filename}")
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                update_data['profile_image'] = f"/{file_path}".replace("\\", "/")

        users_collection.update_one({'username': username}, {'$set': update_data})
        
        user = users_collection.find_one({'username': username})
        profile = {
            'username': user.get('username'),
            'role': user.get('role'),
            'name': user.get('name', ''),
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'profile_image': user.get('profile_image', '')
        }
        return jsonify({'message': 'Profile updated successfully', 'profile': profile}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== PROFILE CHANGE REQUESTS =====

def notify_admin_profile_request(request_data):
    """Notify all admins about a new profile change request"""
    try:
        admins = users_collection.find({'role': 'admin'})
        for admin in admins:
            admin_email = admin.get('email')
            if not admin_email: continue
            
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = f'🔔 New Profile Change Request: {request_data["username"]}'
            message['From'] = EMAIL_SENDER
            message['To'] = admin_email
            
            changes_html = "".join([f"<tr><td style='padding:8px;border:1px solid #ddd;'><b>{k}</b></td><td style='padding:8px;border:1px solid #ddd;'>{v}</td></tr>" for k, v in request_data['changes'].items()])
            
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; color: #333;">
                    <div style="max-width: 600px; margin: 20px auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
                        <h2 style="color: #667eea; border-bottom: 2px solid #667eea; padding-bottom: 10px;">Profile Update Request</h2>
                        <p>User <strong>{request_data['username']}</strong> (Role: {request_data['role']}) has requested the following changes to their profile:</p>
                        <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                            <tr style="background-color: #f8f9fa;"><th style="padding: 8px; border: 1px solid #ddd; text-align: left;">Field</th><th style="padding: 8px; border: 1px solid #ddd; text-align: left;">New Requested Value</th></tr>
                            {changes_html}
                        </table>
                        <p>Please log in to the <strong>Admin Dashboard</strong> to approve or reject this request.</p>
                        <div style="margin-top: 30px; padding-top: 10px; border-top: 1px solid #eee; font-size: 12px; color: #777;">
                            Course Registration System | Admin Notification
                        </div>
                    </div>
                </body>
            </html>
            """
            message.attach(MIMEText(html_body, 'html'))
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_SENDER, admin_email, message.as_string())
    except Exception as e:
        print(f"Error notifying admin: {e}")

@app.route('/api/profile-requests', methods=['POST'])
def submit_profile_request():
    """Submit a request to change profile details (for Students and Teachers)"""
    try:
        data = request.json
        username = data.get('username')
        role = data.get('role')
        changes = data.get('changes')
        
        if not username or not changes:
            return jsonify({'error': 'Invalid request data'}), 400
            
        # Check if there is already a pending request
        existing = profile_requests_collection.find_one({'username': username, 'status': 'pending'})
        if existing:
            return jsonify({'error': 'You already have a pending profile update request. Please wait for admin approval.'}), 400
            
        request_doc = {
            'username': username,
            'role': role,
            'changes': changes,
            'status': 'pending',
            'submitted_at': datetime.now()
        }
        
        profile_requests_collection.insert_one(request_doc)
        
        # Notify admins via email
        notify_admin_profile_request(request_doc)
        
        return jsonify({'message': 'Your change request has been submitted to the admin for approval. You will be notified once handled.'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile-requests', methods=['GET'])
def get_profile_requests():
    """Get all pending profile requests (Admin only)"""
    try:
        requests = []
        for req in profile_requests_collection.find({'status': 'pending'}):
            req['_id'] = str(req['_id'])
            requests.append(req)
        return jsonify({'requests': requests, 'total': len(requests)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile-requests/<request_id>/action', methods=['POST'])
def handle_profile_request(request_id):
    """Approve or Reject a profile change request (Admin only)"""
    try:
        data = request.json
        action = data.get('action') # 'approve' or 'reject'
        
        if not action or action not in ['approve', 'reject']:
            return jsonify({'error': 'Action must be approve or reject'}), 400
            
        req = profile_requests_collection.find_one({'_id': ObjectId(request_id)})
        if not req:
            return jsonify({'error': 'Request not found'}), 404
            
        if action == 'approve':
            # Apply changes to user document
            users_collection.update_one(
                {'username': req['username']},
                {'$set': req['changes']}
            )
            profile_requests_collection.update_one(
                {'_id': ObjectId(request_id)},
                {'$set': {'status': 'approved', 'handled_at': datetime.now()}}
            )
            return jsonify({'message': 'Request approved. User profile has been updated.'}), 200
        else:
            profile_requests_collection.update_one(
                {'_id': ObjectId(request_id)},
                {'$set': {'status': 'rejected', 'handled_at': datetime.now()}}
            )
            return jsonify({'message': 'Profile update request has been rejected.'}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({'error': 'File too large. Maximum size is 5MB.'}), 413

# ===== CREATE OPERATION =====
@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create a new course"""
    try:
        data = request.json
        
        # Validation
        required_fields = ['courseCode', 'courseName', 'department', 'instructor', 'credits', 'capacity']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        course = {
            'courseCode': data.get('courseCode'),
            'courseName': data.get('courseName'),
            'department': data.get('department'),
            'instructor': data.get('instructor'),
            'credits': int(data.get('credits')),
            'capacity': int(data.get('capacity')),
            'description': data.get('description', ''),
            'syllabus': data.get('syllabus', ''), # Added syllabus field
            'schedule': data.get('schedule', ''),
            'enrolledStudents': 0,
            'updatedBy': data.get('updatedBy', 'System Admin')
        }
        
        # Check for duplicate course code
        existing = courses_collection.find_one({'courseCode': course['courseCode']})
        if existing:
            return jsonify({'error': 'Course code already exists'}), 400
        
        result = courses_collection.insert_one(course)
        course['_id'] = str(result.inserted_id)
        
        return jsonify({'message': 'Course created successfully', 'course': course}), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== READ OPERATIONS =====
@app.route('/api/courses', methods=['GET'])
def get_all_courses():
    """Get all courses"""
    try:
        courses = []
        department_filter = request.args.get('department')
        student_username = request.args.get('student_username')
        
        query = {}
        if department_filter:
            query['department'] = department_filter
        
        if student_username:
            student = users_collection.find_one({'username': student_username})
            if student and student.get('role') == 'student' and student.get('department'):
                query['department'] = student.get('department')
        
        for course in courses_collection.find(query):
            course['_id'] = str(course['_id'])
            courses.append(course)
        
        return jsonify({'courses': courses, 'total': len(courses)}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<course_id>', methods=['GET'])
def get_course_by_id(course_id):
    """Get a specific course by ID or Course Code"""
    try:
        # Check if it's a valid ObjectId
        if len(course_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in course_id):
            course = courses_collection.find_one({'_id': ObjectId(course_id)})
        else:
            # If not a valid ID, try searching by course code as a fallback
            course = courses_collection.find_one({'courseCode': course_id})
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        course['_id'] = str(course['_id'])
        return jsonify({'course': course}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/search/<course_code>', methods=['GET'])
def search_course_by_code(course_code):
    """Search course by course code"""
    try:
        course = courses_collection.find_one({'courseCode': course_code})
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        course['_id'] = str(course['_id'])
        return jsonify({'course': course}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== UPDATE OPERATION =====
@app.route('/api/courses/<course_id>', methods=['PUT'])
def update_course(course_id):
    """Update a course by ID or Course Code"""
    try:
        # Determine the query filter
        if len(course_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in course_id):
            query = {'_id': ObjectId(course_id)}
        else:
            query = {'courseCode': course_id}
            
        data = request.json
        
        # Build update document with only provided fields
        update_data = {}
        allowed_fields = ['courseName', 'department', 'instructor', 'credits', 'capacity', 'description', 'schedule', 'updatedBy']
        
        for field in allowed_fields:
            if field in data:
                if field in ['credits', 'capacity']:
                    update_data[field] = int(data[field])
                else:
                    update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        result = courses_collection.update_one(
            query,
            {'$set': update_data}
        )
        
        if result.matched_count == 0:
            return jsonify({'error': 'Course not found'}), 404
        
        # Fetch updated course
        updated_course = courses_collection.find_one({'_id': ObjectId(course_id)})
        updated_course['_id'] = str(updated_course['_id'])
        
        return jsonify({'message': 'Course updated successfully', 'course': updated_course}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== DELETE OPERATION =====
@app.route('/api/courses/<course_id>', methods=['DELETE'])
def delete_course(course_id):
    """Delete a course by ID or Course Code"""
    try:
        # Determine the query filter
        if len(course_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in course_id):
            query = {'_id': ObjectId(course_id)}
        else:
            query = {'courseCode': course_id}
            
        result = courses_collection.delete_one(query)
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify({'message': 'Course deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/student/<username>/courses', methods=['GET'])
def get_student_courses(username):
    """Get all courses a student is enrolled in"""
    try:
        courses = []
        for course in courses_collection.find({'enrolledUsernames': username}):
            course['_id'] = str(course['_id'])
            courses.append(course)
        return jsonify({'courses': courses, 'total': len(courses)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== UTILITY ENDPOINTS =====
@app.route('/api/courses/<course_id>/enroll', methods=['PUT'])
def enroll_student(course_id):
    """Enroll a student in a course by ID or Course Code"""
    try:
        # Determine the query filter
        if len(course_id) == 24 and all(c in '0123456789abcdefABCDEF' for c in course_id):
            query = {'_id': ObjectId(course_id)}
        else:
            query = {'courseCode': course_id}
            
        course = courses_collection.find_one(query)
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        if course.get('enrolledStudents', 0) >= course.get('capacity', 0):
            return jsonify({'error': 'Course is full'}), 400
        
        username = request.json.get('username')
        if not username:
            return jsonify({'error': 'Username required for enrollment'}), 400
            
        # Check if already enrolled
        if username in course.get('enrolledUsernames', []):
            return jsonify({'error': 'Student is already enrolled in this course'}), 400
            
        courses_collection.update_one(
            query,
            {
                '$inc': {'enrolledStudents': 1},
                '$push': {'enrolledUsernames': username}
            }
        )
        
        return jsonify({'message': 'Student enrolled successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/stats', methods=['GET'])
def get_stats():
    """Get statistics about courses"""
    try:
        total_courses = courses_collection.count_documents({})
        stats = {
            'totalCourses': total_courses,
            'totalCapacity': sum([c.get('capacity', 0) for c in courses_collection.find()]),
            'totalEnrolled': sum([c.get('enrolledStudents', 0) for c in courses_collection.find()])
        }
        return jsonify(stats), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== USER MANAGEMENT (ADMIN ONLY) =====
@app.route('/api/users', methods=['GET'])
def get_all_users():
    """Get all users"""
    try:
        users = []
        for user in users_collection.find():
            user_data = {
                'username': user.get('username'),
                'password': user.get('password', 'N/A'),
                'role': user.get('role'),
                'name': user.get('name', ''),
                'email': user.get('email', ''),
                'phone': user.get('phone', ''),
                'department': user.get('department', ''),
                'profile_image': user.get('profile_image', ''),
                'created_at': user.get('created_at', '')
            }
            users.append(user_data)
        return jsonify({'users': users, 'total': len(users)}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
def admin_create_user():
    """Admin endpoint to create a new user and send welcome email"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        email = data.get('email')
        name = data.get('name')
        department = data.get('department', '')
        
        if not username or not password or not role or not email:
            return jsonify({'error': 'Username, password, role, and email are required'}), 400
            
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400
            
        user_data = {
            'username': username,
            'password': password,
            'role': role,
            'email': email,
            'name': name or username,
            'department': department,
            'created_at': datetime.now()
        }
        
        users_collection.insert_one(user_data)
        
        # Send welcome email with credentials
        try:
            send_verification_email(
                recipient_email=email,
                user_name=name or username,
                verification_code='',
                verification_type='account_created',
                extra_data={
                    'username': username,
                    'password': password,
                    'role': role
                }
            )
        except Exception as e:
            print(f"Failed to send welcome email: {e}")
            # We still return success as the user was created in DB
            
        return jsonify({'message': f'User {username} created successfully and notification sent to {email}'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<username>', methods=['PUT'])
def admin_update_user(username):
    """Admin endpoint to update a user"""
    try:
        data = request.json
        update_data = {}
        
        allowed_fields = ['name', 'email', 'role', 'phone', 'password', 'department']
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
                
        if not update_data:
            return jsonify({'error': 'No fields provided for update'}), 400
            
        result = users_collection.update_one({'username': username}, {'$set': update_data})
        
        if result.matched_count == 0:
            return jsonify({'error': 'User not found'}), 404
            
        return jsonify({'message': 'User updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-email-code', methods=['POST'])
def verify_email_code():
    """Verify the 6-digit code sent to the user's email"""
    try:
        data = request.json
        username = data.get('username')
        code = data.get('code')
        
        if not username or not code:
            return jsonify({'error': 'Username and code are required'}), 400
            
        user = users_collection.find_one({'username': username})
        if not user:
            return jsonify({'error': 'User not found'}), 404
            
        stored_code = user.get('email_verification_code')
        timestamp = user.get('email_verification_timestamp')
        
        if not stored_code or stored_code != code:
            return jsonify({'error': 'Invalid verification code'}), 400
            
        # Check if code is expired (e.g., 10 minutes)
        if timestamp:
            current_time = datetime.now()
            if (current_time - timestamp).total_seconds() > 600:
                return jsonify({'error': 'Verification code expired'}), 400
            
        # Mark email as verified
        users_collection.update_one(
            {'username': username},
            {
                '$set': {'email_verified': True},
                '$unset': {'email_verification_code': '', 'email_verification_timestamp': ''}
            }
        )
        
        return jsonify({'message': 'Email verified successfully!'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users/<username>', methods=['DELETE'])
def admin_delete_user(username):
    """Admin endpoint to delete a user"""
    try:
        result = users_collection.delete_one({'username': username})
        if result.deleted_count == 0:
            return jsonify({'error': 'User not found'}), 404
        return jsonify({'message': 'User deleted successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== ROOT ENDPOINT =====
@app.route('/', methods=['GET'])
def home():
    return redirect('login.html')

# Error handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
