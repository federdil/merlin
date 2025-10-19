from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
from pgvector.sqlalchemy import Vector
import datetime

Base = declarative_base()

class Note(Base):
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    tags = Column(JSON)
    embedding = Column(Vector(384))  # Adjust dimension as per your embedding size
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# New tables for learning-focused features

class KnowledgeGap(Base):
    __tablename__ = "knowledge_gaps"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    gap_type = Column(String(100), nullable=False)  # e.g., 'topic_gap', 'skill_gap', 'connection_gap'
    topic = Column(String(255), nullable=False)
    confidence_score = Column(Float, nullable=False)
    suggested_content = Column(ARRAY(String))  # Array of suggested content URLs or topics
    gap_description = Column(Text)  # Detailed description of the gap
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    resolved = Column(String(10), default='false')  # 'true' or 'false'

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    session_id = Column(String(255), nullable=False)
    query = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context = Column(JSON)  # Store conversation context as JSON
    agent_type = Column(String(100))  # Which agent handled this query
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class LearningPath(Base):
    __tablename__ = "learning_paths"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False)
    topic = Column(String(255), nullable=False)
    path_structure = Column(JSON)  # Store the learning path structure
    progress = Column(JSON)  # Store user progress through the path
    estimated_duration = Column(String(50))  # e.g., '2 weeks', '1 month'
    difficulty_level = Column(String(50))  # e.g., 'beginner', 'intermediate', 'advanced'
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

class UserKnowledgeProfile(Base):
    __tablename__ = "user_knowledge_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), nullable=False, unique=True)
    knowledge_topics = Column(JSON)  # Store topics with proficiency levels
    learning_preferences = Column(JSON)  # Store learning style preferences
    knowledge_strengths = Column(ARRAY(String))  # Areas of expertise
    knowledge_weaknesses = Column(ARRAY(String))  # Areas needing improvement
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
