from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from loguru import logger
from config import settings

# Import all models
from models.user import User
from models.query import Query
from models.document import GeneratedDocument
from models.session import Session
from models.feedback import Feedback

client: AsyncIOMotorClient = None


async def connect_db():
    global client
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URL)
        # Ping to confirm connection
        await client.admin.command("ping")
        logger.info("✅ Connected to MongoDB Atlas")

        # Init Beanie ODM with all document models
        await init_beanie(
            database=client[settings.DB_NAME],
            document_models=[
                User,
                Query,
                GeneratedDocument,
                Session,
                Feedback,
            ],
        )
        logger.info("✅ Beanie ODM initialized")
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise


async def disconnect_db():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")


def get_db():
    return client[settings.DB_NAME]
