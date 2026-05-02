from flask import Flask, request, jsonify
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
DB_NAME = 'course_registration'
COLLECTION_NAME = 'courses'
USERS_COLLECTION = 'users'

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    courses_collection = db[COLLECTION_NAME]
    users_collection = db[USERS_COLLECTION]
    print("Connected to MongoDB successfully")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# ===== SMTP EMAIL CONFIGURATION =====
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'your-email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

def send_verification_email(recipient_email, user_name, verification_code, verification_type='password_reset'):
    """
    Send verification email using SMTP (Simple Mail Transfer Protocol)
    
    Args:
        recipient_email: Email address to send to
        user_name: Full name of the user
        verification_code: OTP or verification code
        verification_type: 'password_reset', 'wrong_password', or 'welcome'
    """
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['Subject'] = f'Dev Sanskriti University - {"Password Reset" if verification_type == "password_reset" else "Security Verification"}'
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
        elif verification_type == 'welcome':
            html_body = f"""
            <html>
                <head>
                    <style>
                        body {{ font-family: 'Arial', sans-serif; background-color: #f5f5f5; }}
                        .container {{ max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        .header {{ text-align: center; border-bottom: 3px solid #667eea; padding-bottom: 20px; margin-bottom: 20px; }}
                        .header h2 {{ color: #667eea; margin: 0; }}
                        .content {{ color: #333; line-height: 1.6; }}
                        .button {{ display: inline-block; background-color: #667eea; color: white; padding: 12px 30px; border-radius: 5px; text-decoration: none; margin-top: 15px; }}
                        .footer {{ text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; color: #999; font-size: 12px; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="header">
                            <h2>✅ Welcome to Dev Sanskriti University</h2>
                        </div>
                        
                        <div class="content">
                            <p>Hello <strong>{user_name}</strong>,</p>
                            <p>Your account has been successfully created! You can now log in to the course registration system.</p>
                            <p><strong>Your Account Details:</strong></p>
                            <ul>
                                <li>Email: {recipient_email}</li>
                                <li>Account Created: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
                            </ul>
                            <p>If you did not create this account, please contact us immediately.</p>
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

        # Attach HTML part
        part = MIMEText(html_body, 'html')
        message.attach(part)

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
        print(f"\n[FALLBACK] Verification Code for {user_name}: {verification_code}\n")
        return False

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

@app.route('/api/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        email = data.get('email')
        name = data.get('name')
        
        if not username or not password or not role:
            return jsonify({'error': 'Username, password, and role are required'}), 400
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
            
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400
        
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user_data = {
            'username': username,
            'password': password,
            'role': role,
            'email': email,
            'name': name or username,
            'created_at': datetime.now()
        }
        
        result = users_collection.insert_one(user_data)
        
        # Send welcome email
        send_verification_email(
            email,
            name or username,
            '',
            'welcome'
        )
        
        return jsonify({
            'message': 'Registration successful',
            'user': {
                'username': username,
                'email': email,
                'name': name or username
            }
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
            'schedule': data.get('schedule', ''),
            'enrolledStudents': 0
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
        query = {'department': department_filter} if department_filter else {}
        
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
        allowed_fields = ['courseName', 'department', 'instructor', 'credits', 'capacity', 'description', 'schedule']
        
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
        
        courses_collection.update_one(
            query,
            {'$inc': {'enrolledStudents': 1}}
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

# ===== ROOT ENDPOINT =====
@app.route('/', methods=['GET'])
def home():
    return jsonify({'message': 'Course Registration System API is running'}), 200

# Error handler
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
