"""
Database models for EDU PARTY using SQLAlchemy.
"""
from sqlalchemy import Column, Integer, String
from .database import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    color = Column(String, default="#9B59B6")
    shape = Column(String, default="square")
