from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Hash the password
def hash_password(plain_password:str):
    return pwd_context.hash(plain_password)


def verify_password(plain_password:str, hashed_password:str):
    return pwd_context.verify(plain_password, hashed_password)