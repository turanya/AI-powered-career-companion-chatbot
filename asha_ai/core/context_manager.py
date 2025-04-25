from typing import Dict, List, Optional
import json
from datetime import datetime

class ConversationContext:
    def __init__(self):
        self.conversation_history: List[Dict] = []
        self.session_start: datetime = datetime.now()
        self.context_variables: Dict = {}
        
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
    def get_context(self) -> Dict:
        """Get the current conversation context."""
        return {
            "history": self.conversation_history,
            "session_duration": (datetime.now() - self.session_start).seconds,
            "context_vars": self.context_variables
        }
    
    def update_context(self, key: str, value: any) -> None:
        """Update context variables."""
        self.context_variables[key] = value
        
    def clear_context(self) -> None:
        """Clear the conversation context."""
        self.conversation_history = []
        self.context_variables = {}
        self.session_start = datetime.now() 