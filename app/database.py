from sqlalchemy import URL,create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
from os import getenv

load_dotenv()

# Below method for creating db connection with most commonly used connection parameters
# rather than all things in single connection string.
url_object = URL.create(
    drivername="postgresql",
    host=getenv('DB_HOST'),
    username=getenv('DB_USER'),
    password=getenv('DB_PASSWORD'),
    database=getenv('DB_NAME'),
    port=getenv('DB_PORT')
)

engine = create_engine(url=url_object)

db_connection = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_db():
    try:
        db = db_connection()
        yield db
        
    except Exception as ex:
        print(f"Database Connection error:{ex}")
        raise
    
    finally:
        db.close()
