import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DB_NAME = 'course_registration'
USERS_COLLECTION = 'users'

default_users = [
    {"username": "admin", "password": "password123", "role": "admin"},
    {"username": "teacher", "password": "password123", "role": "teacher"},
    {"username": "student", "password": "password123", "role": "student"},
    {"username": "hod", "password": "password123", "role": "hod"}
]

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    users_collection = db[USERS_COLLECTION]
    
    # Clear existing to prevent duplicates during testing
    users_collection.delete_many({})
    
    # Insert new
    users_collection.insert_many(default_users)
    print("Default users created successfully!")
    print("---------------------------------")
    for user in default_users:
        print(f"Username: {user['username']} | Role: {user['role']} | Password: {user['password']}")
        
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
