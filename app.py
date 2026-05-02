from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
import random
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

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

# ===== AUTHENTICATION =====
@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
            
        user = users_collection.find_one({'username': username, 'password': password})
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
            
        return jsonify({
            'message': 'Login successful',
            'user': {
                'username': user['username'],
                'role': user['role']
            }
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
        
        if not username or not password or not role:
            return jsonify({'error': 'Username, password, and role are required'}), 400
            
        if users_collection.find_one({'username': username}):
            return jsonify({'error': 'Username already exists'}), 400
            
        users_collection.insert_one({'username': username, 'password': password, 'role': role})
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
            
        otp = str(random.randint(100000, 999999))
        users_collection.update_one({'username': username}, {'$set': {'reset_otp': otp}})
        
        print(f"\n====================================")
        print(f"[{username}] PASSWORD RESET OTP: {otp}")
        print(f"====================================\n")
        
        return jsonify({'message': 'OTP generated. Check server console.', 'otp': otp}), 200
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
            
        user = users_collection.find_one({'username': username, 'reset_otp': otp})
        if not user:
            return jsonify({'error': 'Invalid OTP or User'}), 400
            
        users_collection.update_one(
            {'username': username},
            {'$set': {'password': new_password}, '$unset': {'reset_otp': ''}}
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
