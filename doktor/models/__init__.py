from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship




# Define the ConversationEntry class
Base = declarative_base()



class Session(Base):
    __tablename__ = 'session'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), default=None)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)



class ConversationEntry(Base):
    __tablename__ = 'conversation_entries'

    id = Column(Integer, primary_key=True)
    role = Column(String)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    session_id = Column(Integer, default=None, index=True)
