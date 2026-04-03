from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGO_URL", "mongodb://mongo:27017")
DB_NAME = os.getenv("DB_NAME", "school")

client = MongoClient(MONGO_URL)
db = client[DB_NAME]
students_collection = db["students"]
