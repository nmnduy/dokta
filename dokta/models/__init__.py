from datetime import datetime

# Define the ConversationEntry class
class ConversationEntry:
    def __init__(self, role, content, session_id=None, model=None):
        self.id = None
        self.role = role
        self.content = content
        self.model = model
        self.created_at = datetime.utcnow()
        self.session_id = session_id

class Session:
    def __init__(self, name=None):
        self.id = None
        self.name = name
        self.created_at = datetime.utcnow()
