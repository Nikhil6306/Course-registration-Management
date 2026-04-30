"""
Sample Data Script for Course Registration System
This script populates MongoDB with sample courses for testing.
Run this script to quickly add test data to the database.

Usage:
    python sample_data.py
"""

from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = 'course_registration'
COLLECTION_NAME = 'courses'

# Sample Courses Data
SAMPLE_COURSES = [
    {
        'courseCode': 'CS101',
        'courseName': 'Introduction to Computer Science',
        'instructor': 'Dr. John Doe',
        'credits': 3,
        'capacity': 30,
        'enrolledStudents': 25,
        'description': 'Fundamentals of computer science including algorithms, data structures, and problem-solving.',
        'schedule': 'Mon & Wed 10:00 AM - 11:30 AM'
    },
    {
        'courseCode': 'CS201',
        'courseName': 'Data Structures and Algorithms',
        'instructor': 'Prof. Jane Smith',
        'credits': 4,
        'capacity': 25,
        'enrolledStudents': 20,
        'description': 'Advanced data structures including trees, graphs, and sorting algorithms.',
        'schedule': 'Tue & Thu 2:00 PM - 3:30 PM'
    },
    {
        'courseCode': 'CS301',
        'courseName': 'Database Management Systems',
        'instructor': 'Dr. Robert Johnson',
        'credits': 3,
        'capacity': 20,
        'enrolledStudents': 18,
        'description': 'Design and implementation of relational and NoSQL databases.',
        'schedule': 'Mon & Wed 1:00 PM - 2:30 PM'
    },
    {
        'courseCode': 'CS302',
        'courseName': 'Web Development Fundamentals',
        'instructor': 'Ms. Sarah Williams',
        'credits': 3,
        'capacity': 35,
        'enrolledStudents': 32,
        'description': 'HTML, CSS, JavaScript, and web development best practices.',
        'schedule': 'Tue & Thu 10:00 AM - 11:30 AM'
    },
    {
        'courseCode': 'CS401',
        'courseName': 'Software Engineering',
        'instructor': 'Prof. Michael Brown',
        'credits': 4,
        'capacity': 25,
        'enrolledStudents': 22,
        'description': 'Software development lifecycle, design patterns, and project management.',
        'schedule': 'Mon & Wed 3:00 PM - 4:30 PM'
    },
    {
        'courseCode': 'CS402',
        'courseName': 'Artificial Intelligence',
        'instructor': 'Dr. Emily Davis',
        'credits': 4,
        'capacity': 20,
        'enrolledStudents': 19,
        'description': 'Machine learning, neural networks, and AI applications.',
        'schedule': 'Tue & Thu 11:00 AM - 12:30 PM'
    },
    {
        'courseCode': 'CS403',
        'courseName': 'Cybersecurity Fundamentals',
        'instructor': 'Prof. David Miller',
        'credits': 3,
        'capacity': 28,
        'enrolledStudents': 26,
        'description': 'Network security, cryptography, and threat analysis.',
        'schedule': 'Wed & Fri 2:00 PM - 3:30 PM'
    },
    {
        'courseCode': 'CS404',
        'courseName': 'Cloud Computing',
        'instructor': 'Ms. Jessica Taylor',
        'credits': 3,
        'capacity': 30,
        'enrolledStudents': 28,
        'description': 'AWS, Azure, and Google Cloud Platform fundamentals.',
        'schedule': 'Mon & Wed 11:00 AM - 12:30 PM'
    },
    {
        'courseCode': 'MATH101',
        'courseName': 'Discrete Mathematics',
        'instructor': 'Dr. Richard Anderson',
        'credits': 4,
        'capacity': 32,
        'enrolledStudents': 30,
        'description': 'Logic, set theory, combinatorics, and graph theory.',
        'schedule': 'Tue & Thu 1:00 PM - 2:30 PM'
    },
    {
        'courseCode': 'MATH201',
        'courseName': 'Calculus III',
        'instructor': 'Prof. Lisa Martin',
        'credits': 4,
        'capacity': 35,
        'enrolledStudents': 33,
        'description': 'Multivariable calculus and vector analysis.',
        'schedule': 'Mon & Wed 2:00 PM - 3:30 PM'
    }
]


def connect_to_database():
    """Connect to MongoDB and return the database object."""
    try:
        client = MongoClient(MONGO_URI)
        db = client[DB_NAME]
        print(f"✓ Connected to MongoDB successfully")
        print(f"✓ Database: {DB_NAME}")
        return db
    except Exception as e:
        print(f"✗ Error connecting to MongoDB: {e}")
        return None


def clear_collection(db):
    """Clear existing courses from the collection."""
    try:
        collection = db[COLLECTION_NAME]
        result = collection.delete_many({})
        print(f"✓ Cleared {result.deleted_count} existing courses from collection")
    except Exception as e:
        print(f"✗ Error clearing collection: {e}")


def insert_sample_data(db):
    """Insert sample courses into the database."""
    try:
        collection = db[COLLECTION_NAME]
        result = collection.insert_many(SAMPLE_COURSES)
        print(f"✓ Successfully inserted {len(result.inserted_ids)} sample courses")
        print(f"\nInserted Courses:")
        for i, course_id in enumerate(result.inserted_ids):
            course = SAMPLE_COURSES[i]
            print(f"  {i+1}. {course['courseCode']} - {course['courseName']}")
    except Exception as e:
        print(f"✗ Error inserting sample data: {e}")


def create_indexes(db):
    """Create database indexes for better query performance."""
    try:
        collection = db[COLLECTION_NAME]
        # Create unique index on courseCode
        collection.create_index('courseCode', unique=True)
        print(f"✓ Created indexes for optimal performance")
    except Exception as e:
        print(f"✗ Error creating indexes: {e}")


def display_summary(db):
    """Display a summary of the inserted data."""
    try:
        collection = db[COLLECTION_NAME]
        total_courses = collection.count_documents({})
        
        # Calculate statistics
        all_courses = list(collection.find())
        total_capacity = sum(c.get('capacity', 0) for c in all_courses)
        total_enrolled = sum(c.get('enrolledStudents', 0) for c in all_courses)
        
        print(f"\n{'='*50}")
        print(f"DATABASE SUMMARY")
        print(f"{'='*50}")
        print(f"Total Courses: {total_courses}")
        print(f"Total Capacity: {total_capacity} students")
        print(f"Total Enrolled: {total_enrolled} students")
        print(f"Average Enrollment Rate: {(total_enrolled/total_capacity)*100:.1f}%")
        print(f"{'='*50}\n")
        
    except Exception as e:
        print(f"✗ Error displaying summary: {e}")


def main():
    """Main function to run the sample data insertion."""
    print("\n" + "="*50)
    print("COURSE REGISTRATION SYSTEM - SAMPLE DATA INSERTION")
    print("="*50 + "\n")
    
    # Connect to database
    db = connect_to_database()
    if db is None:
        print("\nFailed to connect to MongoDB. Please ensure:")
        print("1. MongoDB is installed and running")
        print("2. MongoDB connection URI in .env is correct")
        print("3. Check your internet connection")
        return
    
    # Clear existing data
    print(f"\nPreparing database...")
    clear_collection(db)
    
    # Create indexes
    create_indexes(db)
    
    # Insert sample data
    print(f"\nInserting sample courses...")
    insert_sample_data(db)
    
    # Display summary
    display_summary(db)
    
    print("✓ Sample data insertion completed successfully!")
    print("\nYou can now:")
    print("1. Open index.html in your browser")
    print("2. Go to 'View Courses' tab to see all sample courses")
    print("3. Test CRUD operations with the sample data")


if __name__ == '__main__':
    main()
