from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_engine(settings_instance=settings):
    try:
        engine = create_engine(
            settings_instance.DATABASE_URL,
            pool_pre_ping=True,  # Enable connection health checks
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False          # Disable SQL query logging
        )
        logger.info("Database engine created successfully")
        # Extract and log only the database engine and name
        db_url = settings_instance.DATABASE_URL
        db_engine = db_url.split('://')[0]
        db_name = db_url.split('/')[-1].split('?')[0]
        logger.info(f"Database: {db_engine}://{db_name}")
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {str(e)}")
        raise

# Create engine with default settings
engine = get_engine()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for all database models
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        db.close() 