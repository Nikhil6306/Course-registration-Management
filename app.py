from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = 'course_registration'
COLLECTION_NAME = 'courses'

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    courses_collection = db[COLLECTION_NAME]
    print("Connected to MongoDB successfully")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")

# ===== CREATE OPERATION =====
@app.route('/api/courses', methods=['POST'])
def create_course():
    """Create a new course"""
    try:
        data = request.json
        
        # Validation
        required_fields = ['courseCode', 'courseName', 'instructor', 'credits', 'capacity']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        course = {
            'courseCode': data.get('courseCode'),
            'courseName': data.get('courseName'),
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
        for course in courses_collection.find():
            course['_id'] = str(course['_id'])
            courses.append(course)
        
        return jsonify({'courses': courses, 'total': len(courses)}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/courses/<course_id>', methods=['GET'])
def get_course_by_id(course_id):
    """Get a specific course by ID"""
    try:
        course = courses_collection.find_one({'_id': ObjectId(course_id)})
        
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
    """Update a course"""
    try:
        data = request.json
        
        # Build update document with only provided fields
        update_data = {}
        allowed_fields = ['courseName', 'instructor', 'credits', 'capacity', 'description', 'schedule']
        
        for field in allowed_fields:
            if field in data:
                if field in ['credits', 'capacity']:
                    update_data[field] = int(data[field])
                else:
                    update_data[field] = data[field]
        
        if not update_data:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        result = courses_collection.update_one(
            {'_id': ObjectId(course_id)},
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
    """Delete a course"""
    try:
        result = courses_collection.delete_one({'_id': ObjectId(course_id)})
        
        if result.deleted_count == 0:
            return jsonify({'error': 'Course not found'}), 404
        
        return jsonify({'message': 'Course deleted successfully'}), 200
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== UTILITY ENDPOINTS =====
@app.route('/api/courses/<course_id>/enroll', methods=['PUT'])
def enroll_student(course_id):
    """Enroll a student in a course"""
    try:
        course = courses_collection.find_one({'_id': ObjectId(course_id)})
        
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        if course.get('enrolledStudents', 0) >= course.get('capacity', 0):
            return jsonify({'error': 'Course is full'}), 400
        
        courses_collection.update_one(
            {'_id': ObjectId(course_id)},
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
