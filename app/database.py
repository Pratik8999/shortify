from sqlalchemy import URL,create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from os import getenv
import logging

# Load .env file only if not running in Docker (where env vars are passed directly)
load_dotenv(override=False)

# Below method for creating db connection with most commonly used connection parameters
# rather than all things in single connection string.

db_url = getenv("DB_URL")

engine = create_engine(url=db_url)

db_connection = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    try:
        db = db_connection()
        yield db
        
    except Exception as ex:
        logger = logging.getLogger("app.main")
        logger.error(f"Database connection error: {str(ex)}", exc_info=True)
        raise
    
    finally:
        db.close()
