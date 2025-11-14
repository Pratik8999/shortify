from sqlalchemy import Column,Integer,VARCHAR,Text,DateTime,Boolean,BigInteger,ForeignKey
from sqlalchemy.orm import declarative_base,relationship
from datetime import datetime, timezone


ORM_BASE_MODEL = declarative_base()

class TimeStamp(ORM_BASE_MODEL):
    __abstract__ = True
    createdon = Column(DateTime(timezone=True), nullable=False, default=lambda:datetime.now(timezone.utc))
    updatedon = Column(DateTime(timezone=True), nullable=False, default=lambda:datetime.now(timezone.utc), 
                        onupdate=lambda:datetime.now(timezone.utc))



class User(TimeStamp):
    __tablename__ = "user"
    id = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    name = Column(VARCHAR(45), nullable=False)
    email = Column(VARCHAR(50), nullable=False, unique=True, index=True)
    password = Column(VARCHAR(120), nullable=False)
    country = Column(VARCHAR(50), nullable=False)
    isactive = Column(Boolean, default=True, nullable=False)

    urls = relationship("Url", back_populates="user_ref", cascade="all, delete")



class Url(TimeStamp):
    __tablename__ = "url"
    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True)
    url = Column(Text, nullable=False)
    code = Column(VARCHAR(20), index=True, nullable=True)
    user = Column(Integer,ForeignKey("user.id",onupdate="CASCADE",ondelete="CASCADE"), nullable=True, index=True)
    click_count = Column(Integer, nullable=True, default=0)   
    expires_at = Column(DateTime(timezone=True), nullable=True)

    user_ref = relationship("User", back_populates="urls")
    analytics = relationship("UrlAnalytics", back_populates="url_ref", cascade="all, delete")



class UrlAnalytics(TimeStamp):
    __tablename__ = "url_analytics"

    id = Column(BigInteger, nullable=False, primary_key=True, autoincrement=True)
    url = Column(Integer,ForeignKey("url.id",onupdate="CASCADE",ondelete="CASCADE"), nullable=False, index=True)
    
    ip_address = Column(VARCHAR(64), nullable=True)
    country = Column(VARCHAR(50), nullable=True)
    referrer = Column(Text, nullable=True)
    device = Column(VARCHAR(30), nullable=True)
    browser = Column(VARCHAR(30), nullable=True)
    os = Column(VARCHAR(30), nullable=True)
    user_agent = Column(Text, nullable=True)

    url_ref = relationship("Url", back_populates="analytics")



class BlacklistedToken(ORM_BASE_MODEL):
    __tablename__ = "blacklisted_tokens"
    
    jti = Column(VARCHAR(120), primary_key=True, nullable=False)