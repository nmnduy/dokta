from dataclasses import dataclass



@dataclass
class State:
    model: str
    max_tokens: int
    session_id: int = None
