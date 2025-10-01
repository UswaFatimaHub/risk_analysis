from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class MongoDB:
    client: AsyncIOMotorClient = None
    database = None

mongo_db = MongoDB()

async def connect_to_mongo():
    """Create database connection with optimized settings"""
    try:
        # Configure connection with timeouts and connection pooling
        mongo_db.client = AsyncIOMotorClient(
            settings.mongodb_url,
            serverSelectionTimeoutMS=5000,  # 5 second timeout
            connectTimeoutMS=5000,          # 5 second connection timeout
            socketTimeoutMS=5000,           # 5 second socket timeout
            maxPoolSize=10,                 # Maximum connection pool size
            minPoolSize=1,                  # Minimum connection pool size
        )
        mongo_db.database = mongo_db.client[settings.database_name]
        
        # Test the connection with timeout
        await mongo_db.client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {settings.mongodb_url}")
        
        # Create indexes for better performance
        await mongo_db.database.questionnaires.create_index("questionnaire_id", unique=True)
        logger.info("Created database indexes")
        
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

async def close_mongo_connection():
    """Close database connection"""
    if mongo_db.client:
        mongo_db.client.close()
        logger.info("Disconnected from MongoDB")

def get_database():
    """Get database connection with connection check"""
    if mongo_db.database is None:
        raise Exception("Database not connected. Call connect_to_mongo() first.")
    return mongo_db.database
