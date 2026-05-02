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

# ===== EMAIL CONFIGURATION =====
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'your-email@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', 'your-app-password')
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))

def send_email(recipient_email, subject, body, otp=None):
    """Send email with OTP or notification"""
    try:
        message = MIMEMultipart('alternative')
        message['Subject'] = subject
        message['From'] = EMAIL_SENDER
        message['To'] = recipient_email

        # HTML email template
        if otp:
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #333; text-align: center;">Dev Sanskriti University</h2>
                        <h3 style="color: #667eea; text-align: center;">Security Verification</h3>
                        <p style="color: #555; font-size: 16px;">
                            {body}
                        </p>
                        <div style="background-color: #f0f0f0; padding: 20px; border-radius: 8px; text-align: center; margin: 20px 0;">
                            <p style="margin: 0; color: #999; font-size: 12px;">Your OTP Code:</p>
                            <h1 style="color: #667eea; margin: 10px 0; letter-spacing: 5px;">{otp}</h1>
                            <p style="margin: 0; color: #999; font-size: 12px;">This code will expire in 15 minutes</p>
                        </div>
                        <p style="color: #777; font-size: 14px; margin-top: 20px;">
                            If you did not request this OTP, please ignore this email or contact support immediately.
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            Dev Sanskriti University - Course Registration System<br>
                            © 2024 All rights reserved
                        </p>
                    </div>
                </body>
            </html>
            """
        else:
            html_body = f"""
            <html>
                <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                    <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h2 style="color: #333; text-align: center;">Dev Sanskriti University</h2>
                        <p style="color: #555; font-size: 16px;">
                            {body}
                        </p>
                        <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                        <p style="color: #999; font-size: 12px; text-align: center;">
                            Dev Sanskriti University - Course Registration System<br>
                            © 2024 All rights reserved
                        </p>
                    </div>
                </body>
            </html>
            """

        part = MIMEText(html_body, 'html')
        message.attach(part)

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, recipient_email, message.as_string())
        
        print(f"✓ Email sent successfully to {recipient_email}")
        return True
    except Exception as e:
        print(f"✗ Failed to send email to {recipient_email}: {str(e)}")
        # Still print OTP to console as fallback
        if otp:
            print(f"\n====================================")
            print(f"FALLBACK OTP: {otp}")
            print(f"====================================\n")
        return False

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

def is_otp_valid(otp_data):
    """Check if OTP is still valid (within 15 minutes)"""
    if not otp_data or 'timestamp' not in otp_data:
        return False
    expiry_time = otp_data['timestamp'] + timedelta(minutes=15)
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
        
        # Check if password is correct
        if user['password'] != password:
            # Wrong password - generate OTP for verification
            otp = generate_otp()
            otp_timestamp = datetime.now()
            
            # Store OTP in user document
            users_collection.update_one(
                {'username': username},
                {
                    '$set': {
                        'wrong_password_otp': otp,
                        'wrong_password_otp_timestamp': otp_timestamp,
                        'wrong_password_attempts': user.get('wrong_password_attempts', 0) + 1
                    }
                }
            )
            
            # Send OTP to user's email
            user_email = user.get('email', '')
            if user_email:
                send_email(
                    user_email,
                    'Security Alert - Wrong Password Attempt',
                    f'We detected an incorrect password attempt on your account. Please use the following OTP to verify your identity and reset your password if needed.',
                    otp
                )
            
            return jsonify({
                'error': 'Invalid password',
                'requiresOTP': True,
                'message': f'Wrong password. An OTP has been sent to {user_email or "your email"}. Please verify with OTP.',
                'username': username
            }), 401
        
        # Password is correct - login successful
        return jsonify({
            'message': 'Login successful',
            'user': {
                'username': user['username'],
                'role': user['role']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/verify-login-otp', methods=['POST'])
def verify_login_otp():
    """Verify OTP sent after wrong password attempt"""
    try:
        data = request.json
        username = data.get('username')
        otp = data.get('otp')
        
        if not username or not otp:
            return jsonify({'error': 'Username and OTP required'}), 400
        
        user = users_collection.find_one({'username': username})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Check if OTP exists and is valid
        stored_otp = user.get('wrong_password_otp')
        otp_timestamp = user.get('wrong_password_otp_timestamp')
        
        if not stored_otp or not otp_timestamp:
            return jsonify({'error': 'No OTP request found. Please try logging in again.'}), 400
        
        # Check OTP expiry (15 minutes)
        expiry_time = otp_timestamp + timedelta(minutes=15)
        if datetime.now() > expiry_time:
            users_collection.update_one(
                {'username': username},
                {'$unset': {'wrong_password_otp': '', 'wrong_password_otp_timestamp': ''}}
            )
            return jsonify({'error': 'OTP has expired. Please try logging in again.'}), 400
        
        # Verify OTP
        if stored_otp != otp:
            return jsonify({'error': 'Invalid OTP'}), 401
        
        # OTP verified successfully - clear OTP and return verification token
        users_collection.update_one(
            {'username': username},
            {
                '$unset': {'wrong_password_otp': '', 'wrong_password_otp_timestamp': ''},
                '$set': {'last_verification': datetime.now()}
            }
        )
        
        return jsonify({
            'message': 'OTP verified successfully',
            'verified': True,
            'username': username,
            'email': user.get('email', '')
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
        
        if not username or not password or not role or not email:
            return jsonify({'error': 'Username, password, role, and email are required'}), 400
            
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400
        
        if users_collection.find_one({'email': email}):
            return jsonify({'error': 'Email already exists'}), 400
            
        user_data = {
            'username': username,
            'password': password,
            'role': role,
            'email': email,
            'created_at': datetime.now()
        }
        result = users_collection.insert_one(user_data)
        
        # Send welcome email
        send_email(
            email,
            'Welcome to Dev Sanskriti University Course Registration',
            f'Welcome {username}! Your account has been created successfully. You can now log in to the course registration system.'
        )
        
        return jsonify({'message': 'Registration successful'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/forgot-password', methods=['POST'])
def forgot_password():
    try:
        data = request.json
        username = data.get('username')
        
        if not username:
            return jsonify({'error': 'Username is required'}), 400
            
        user = users_collection.find_one({'username': username})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user_email = user.get('email', '')
        if not user_email:
            return jsonify({'error': 'Email not found for this user'}), 400
            
        otp = generate_otp()
        otp_timestamp = datetime.now()
        
        users_collection.update_one(
            {'username': username},
            {
                '$set': {
                    'reset_otp': otp,
                    'reset_otp_timestamp': otp_timestamp
                }
            }
        )
        
        # Send OTP email
        email_sent = send_email(
            user_email,
            'Password Reset Request - Dev Sanskriti University',
            'You requested a password reset. Please use the following OTP to reset your password:',
            otp
        )
        
        return jsonify({
            'message': f'OTP sent to {user_email}',
            'email': user_email,
            'emailSent': email_sent
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    try:
        data = request.json
        username = data.get('username')
        otp = data.get('otp')
        new_password = data.get('newPassword')
        
        if not username or not otp or not new_password:
            return jsonify({'error': 'Missing required fields'}), 400
            
        user = users_collection.find_one({'username': username})
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Verify OTP
        stored_otp = user.get('reset_otp')
        otp_timestamp = user.get('reset_otp_timestamp')
        
        if not stored_otp or stored_otp != otp:
            return jsonify({'error': 'Invalid OTP'}), 401
        
        # Check OTP expiry (15 minutes)
        if otp_timestamp:
            expiry_time = otp_timestamp + timedelta(minutes=15)
            if datetime.now() > expiry_time:
                users_collection.update_one(
                    {'username': username},
                    {'$unset': {'reset_otp': '', 'reset_otp_timestamp': ''}}
                )
                return jsonify({'error': 'OTP has expired'}), 400
        
        # Update password
        users_collection.update_one(
            {'username': username},
            {
                '$set': {'password': new_password, 'last_password_reset': datetime.now()},
                '$unset': {'reset_otp': '', 'reset_otp_timestamp': ''}
            }
        )
        
        # Send confirmation email
        user_email = user.get('email', '')
        if user_email:
            send_email(
                user_email,
                'Password Changed - Dev Sanskriti University',
                'Your password has been changed successfully. If you did not make this change, please contact support immediately.'
            )
        
        return jsonify({'message': 'Password reset successfully'}), 200
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
