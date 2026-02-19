from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.core.config import settings
from app.models.schemas import VideoAnalysisReport

async def init_db():
    """
    Initializes the database connection and registers Beanie ODM documents.
    """
    # Create Motor client
    client = AsyncIOMotorClient(settings.MONGO_URI)
    
    # Initialize Beanie with the db instance and the document models
    # It will automatically create the database if it doesn't exist
    await init_beanie(
        database=client.get_default_database(),
        document_models=[
            VideoAnalysisReport
        ]
    )
    
    print("MongoDB successfully connected and Beanie initialized!")
