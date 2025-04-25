from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass
import logging
from collections import deque

@dataclass
class ConversationContext:
    """Represents the context of a conversation"""
    session_id: str
    user_id: str
    current_topic: str
    previous_topics: List[str]
    entities: Dict[str, List[str]]
    preferences: Dict[str, Any]
    last_interaction: datetime
    conversation_history: List[Dict[str, str]]
    context_window: int = 10  # Number of messages to keep in memory

@dataclass
class MemoryItem:
    """Represents a long-term memory item"""
    key: str
    value: Any
    timestamp: datetime
    importance: float  # 0.0 to 1.0
    category: str
    metadata: Dict[str, Any]

class ContextManager:
    def __init__(self, max_memory_items: int = 1000, memory_retention_days: int = 30):
        self.contexts: Dict[str, ConversationContext] = {}
        self.long_term_memory: Dict[str, MemoryItem] = {}
        self.max_memory_items = max_memory_items
        self.memory_retention_days = memory_retention_days
        self.logger = logging.getLogger(__name__)
        
        # Load existing memory if available
        self._load_memory()
    
    def _load_memory(self):
        """Load long-term memory from file"""
        try:
            if os.path.exists('data/memory.json'):
                with open('data/memory.json', 'r') as f:
                    memory_data = json.load(f)
                    for key, item in memory_data.items():
                        self.long_term_memory[key] = MemoryItem(
                            key=key,
                            value=item['value'],
                            timestamp=datetime.fromisoformat(item['timestamp']),
                            importance=item['importance'],
                            category=item['category'],
                            metadata=item['metadata']
                        )
        except Exception as e:
            self.logger.error(f"Error loading memory: {str(e)}")
    
    def _save_memory(self):
        """Save long-term memory to file"""
        try:
            os.makedirs('data', exist_ok=True)
            memory_data = {
                key: {
                    'value': item.value,
                    'timestamp': item.timestamp.isoformat(),
                    'importance': item.importance,
                    'category': item.category,
                    'metadata': item.metadata
                }
                for key, item in self.long_term_memory.items()
            }
            with open('data/memory.json', 'w') as f:
                json.dump(memory_data, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving memory: {str(e)}")
    
    def create_context(self, session_id: str, user_id: str) -> ConversationContext:
        """Create a new conversation context"""
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id,
            current_topic='',
            previous_topics=[],
            entities={},
            preferences={},
            last_interaction=datetime.now(),
            conversation_history=[]
        )
        self.contexts[session_id] = context
        return context
    
    def get_context(self, session_id: str) -> Optional[ConversationContext]:
        """Get conversation context"""
        return self.contexts.get(session_id)
    
    def update_context(
        self,
        session_id: str,
        message: str,
        response: str,
        intent: str,
        entities: Dict[str, List[str]],
        sentiment: str
    ):
        """Update conversation context with new interaction"""
        if session_id not in self.contexts:
            return
        
        context = self.contexts[session_id]
        context.last_interaction = datetime.now()
        
        # Update current topic based on intent
        if intent != 'unknown':
            if context.current_topic != intent:
                context.previous_topics.append(context.current_topic)
                context.current_topic = intent
        
        # Update entities
        for entity_type, entity_values in entities.items():
            if entity_type not in context.entities:
                context.entities[entity_type] = []
            context.entities[entity_type].extend(
                [ev for ev in entity_values if ev not in context.entities[entity_type]]
            )
        
        # Update conversation history
        context.conversation_history.append({
            'timestamp': datetime.now().isoformat(),
            'user_message': message,
            'bot_response': response,
            'intent': intent,
            'sentiment': sentiment
        })
        
        # Keep only the most recent messages
        if len(context.conversation_history) > context.context_window:
            context.conversation_history = context.conversation_history[-context.context_window:]
    
    def store_memory(
        self,
        key: str,
        value: Any,
        importance: float = 0.5,
        category: str = 'general',
        metadata: Optional[Dict] = None
    ):
        """Store information in long-term memory"""
        memory_item = MemoryItem(
            key=key,
            value=value,
            timestamp=datetime.now(),
            importance=importance,
            category=category,
            metadata=metadata or {}
        )
        self.long_term_memory[key] = memory_item
        
        # Clean up old or low-importance memories if needed
        self._cleanup_memory()
        
        # Save memory to file
        self._save_memory()
    
    def _cleanup_memory(self):
        """Clean up old or low-importance memories"""
        current_time = datetime.now()
        
        # Remove memories older than retention period
        self.long_term_memory = {
            k: v for k, v in self.long_term_memory.items()
            if (current_time - v.timestamp).days <= self.memory_retention_days
        }
        
        # If still too many items, remove lowest importance ones
        if len(self.long_term_memory) > self.max_memory_items:
            sorted_memories = sorted(
                self.long_term_memory.items(),
                key=lambda x: x[1].importance
            )
            self.long_term_memory = dict(sorted_memories[-self.max_memory_items:])
    
    def retrieve_memory(
        self,
        query: str,
        category: Optional[str] = None,
        min_importance: float = 0.0
    ) -> List[MemoryItem]:
        """Retrieve relevant memories based on query"""
        relevant_memories = []
        
        for memory in self.long_term_memory.values():
            if memory.importance < min_importance:
                continue
            
            if category and memory.category != category:
                continue
            
            # Simple text matching for now - could be enhanced with semantic search
            if query.lower() in str(memory.value).lower():
                relevant_memories.append(memory)
        
        return sorted(relevant_memories, key=lambda x: x.importance, reverse=True)
    
    def get_conversation_summary(self, session_id: str) -> Dict:
        """Get a summary of the conversation"""
        if session_id not in self.contexts:
            return {}
        
        context = self.contexts[session_id]
        return {
            'current_topic': context.current_topic,
            'previous_topics': context.previous_topics,
            'entities': context.entities,
            'preferences': context.preferences,
            'last_interaction': context.last_interaction.isoformat(),
            'message_count': len(context.conversation_history)
        }
    
    def clear_context(self, session_id: str):
        """Clear conversation context"""
        if session_id in self.contexts:
            del self.contexts[session_id]
    
    def clear_all_contexts(self):
        """Clear all conversation contexts"""
        self.contexts.clear() 