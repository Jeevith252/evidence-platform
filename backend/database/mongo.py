# database/mongo.py
# This file handles the connection to our MongoDB database
# Think of this as the "phone line" between our app and the database

from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

# Load settings from .env file
load_dotenv()

# Get the MongoDB URL from our .env file
MONGO_URL = os.getenv("MONGO_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Create the database client (the actual connection)
client = AsyncIOMotorClient(MONGO_URL)

# Select our specific database
database = client[DATABASE_NAME]

# These are our "collections" — like tables in Excel
evidence_collection = database["evidence"]
accounts_collection = database["accounts"]
reports_collection = database["reports"]

# Function to check if connection works
async def check_connection():
    try:
        await client.admin.command('ping')
        print("SUCCESS: Connected to MongoDB successfully!")
        return True
    except Exception as e:
        print(f"ERROR: MongoDB connection failed: {e}")
        return False