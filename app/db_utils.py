from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError


def safe_commit(db:Session, object:object) -> None:
    try:
        db.add(object)
        db.commit()

    except IntegrityError as ie:
        db.rollback()
        raise ie
    
    except Exception as e:
        db.rollback()
        raise e


def safe_commit_with_refresh(db:Session, object:object) -> object:
    try:
        db.add(object)
        db.commit()
        db.refresh(object)
        return object
    
    except IntegrityError as ie:
        db.rollback()
        raise ie
    
    except Exception as e:
        db.rollback()
        raise e
