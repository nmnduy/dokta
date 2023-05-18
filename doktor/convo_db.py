import hashlib
import os
import time
from datetime import timedelta
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .models import Base, ConversationEntry, Session


DB_NAME = "convo_db.sqlite"



def random_hash():

    # Generate a random salt using the OS-provided seed
    salt = os.urandom(16)

    # Generate a time-based message to hash
    msg = str(time.time()).encode('utf-8')

    # Concatenate the salt and message
    msg_salt = salt + msg

    # Generate the hash using SHA-256
    hash_obj = hashlib.sha256(msg_salt)
    hash_val = hash_obj.hexdigest()
    return hash_val


# Set up the database connection
def setup_database_connection(db_name):
    engine = create_engine(f"sqlite:///{db_name}.db")
    Base.metadata.create_all(engine)
    db_session = sessionmaker(bind=engine)
    return db_session


# Functions to interact with the database
def add_entry(db_session,
              role,
              content,
              session_id = None,   # Optional[int] = None
              ):
    entry = ConversationEntry(role=role,
                              content=content,
                              session_id=session_id)
    db_session.add(entry)
    db_session.commit()


def get_entries_past_week(db_session,
                          session_id = None, # Optional[int] = None
                          ):
    one_week_ago = datetime.utcnow() - timedelta(weeks=1)
    if session_id is not None:
        return db_session.query(ConversationEntry).filter(ConversationEntry.created_at >= one_week_ago).filter(ConversationEntry.session_id == session_id).all()
    return db_session.query(ConversationEntry).filter(ConversationEntry.created_at >= one_week_ago).all()


def delete_entry(db_session, entry_id):
    entry = db_session.query(ConversationEntry).get(entry_id)
    if entry:
        db_session.delete(entry)
        db_session.commit()



class Db:


    def __init__(self):
        self.db_session = setup_database_connection(DB_NAME)()


    def create_chat_session(self,
                            name = None, # Optiona[str] = None
                            ) -> int:
        if name is None:
            name = random_hash()
        session = Session(name=name)
        self.db_session.add(session)
        self.db_session.commit()
        return session.id


    def find_session(self, name: str): # Optional[int]:
        session = self.db_session.query(Session).filter(Session.name == name).first()
        return session


    def get_all_chat_sessions(self): # List[Session]:
        return self.db_session.query(Session).all()


    def rename_chat_session(self,
                            session_id: int,
                            new_name: str,
                            ) -> None:
        session = self.db_session.query(Session).get(session_id)
        session.name = new_name
        self.db_session.commit()


    def get_entries_past_week(self,
                              session_id = int,
                              ):
        session = self.db_session.query(Session).get(session_id)
        one_week_ago = datetime.utcnow() - timedelta(weeks=1)
        return self.db_session.query(ConversationEntry).filter(ConversationEntry.created_at >= one_week_ago).filter(ConversationEntry.session_id == session_id).all()
