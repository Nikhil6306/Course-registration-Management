import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = 'course_registration'
USERS_COLLECTION = 'users'

# Demo users with email addresses (required for OTP system)
default_users = [
    {
        "username": "admin",
        "password": "password123",
        "role": "admin",
        "email": "admin@devsanskritiuni.edu.in"
    },
    {
        "username": "teacher",
        "password": "password123",
        "role": "teacher",
        "email": "teacher@devsanskritiuni.edu.in"
    },
    {
        "username": "student",
        "password": "password123",
        "role": "student",
        "email": "student@devsanskritiuni.edu.in"
    },
    {
        "username": "hod",
        "password": "password123",
        "role": "hod",
        "email": "hod@devsanskritiuni.edu.in"
    }
]

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db[USERS_COLLECTION]
    
    # Clear existing to prevent duplicates during testing
    users_collection.delete_many({})
    
    # Insert new
    users_collection.insert_many(default_users)
    print("✓ Default users created successfully!")
    print("=" * 60)
    print("Demo Accounts (OTP System Enabled):")
    print("=" * 60)
    for user in default_users:
        print(f"Username:  {user['username']:<15} | Password: {user['password']:<15}")
        print(f"Role:      {user['role']:<15} | Email:    {user['email']:<20}")
        print("-" * 60)
    print("\nNote: OTP for wrong password and password reset will be sent to:")
    print("      These email addresses. Check your email inbox/spam folder.")
    print("=" * 60)
        
except Exception as e:
    print(f"✗ Error connecting to MongoDB: {e}")
