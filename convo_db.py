from datetime import timedelta
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Define the ConversationEntry class
Base = declarative_base()


class ConversationEntry(Base):
    __tablename__ = 'conversation_entries'

    id = Column(Integer, primary_key=True)
    role = Column(String)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)


# Set up the database connection
def setup_database_connection(db_name):
    engine = create_engine(f"sqlite:///{db_name}.db")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session


# Functions to interact with the database
def add_entry(session, role, content):
    entry = ConversationEntry(role=role, content=content)
    session.add(entry)
    session.commit()


# def get_all_entries(session):
#     return session.query(ConversationEntry).all()


def get_entries_past_week(session):
    one_week_ago = datetime.utcnow() - timedelta(weeks=1)
    return session.query(ConversationEntry).filter(ConversationEntry.created_at >= one_week_ago).all()


def delete_entry(session, entry_id):
    entry = session.query(ConversationEntry).get(entry_id)
    if entry:
        session.delete(entry)
        session.commit()
