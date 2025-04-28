import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import os
import uuid
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class SessionManager:
    def __init__(self):
        self.sessions = {}
        self.history = {}
        self.context = {}
    
    def create_session(self, user_id: str) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = user_id
        self.history[session_id] = []
        self.context[session_id] = {}
        return session_id
    
    def get_context(self, session_id: str) -> Dict:
        return self.context.get(session_id, {})
    
    def update_context(self, session_id: str, updates: Dict):
        if session_id in self.context:
            self.context[session_id].update(updates)
    
    def add_to_history(self, session_id: str, user_message: str, bot_response: str):
        if session_id in self.history:
            self.history[session_id].append({
                'user': user_message,
                'bot': bot_response,
                'timestamp': datetime.now().isoformat()
            })

class NLPProcessor:
    def __init__(self):
        pass
    
    def normalize_text(self, text: str) -> str:
        return text.strip()
    
    def process_text(self, text: str) -> Dict:
        # Simple intent detection based on keywords
        text = text.lower()
        if any(word in text for word in ['event', 'workshop', 'conference']):
            return {"intent": "events", "entities": {}}
        elif any(word in text for word in ['course', 'training', 'program', 'development']):
            return {"intent": "professional_development", "entities": {}}
        elif any(word in text for word in ['mentor', 'mentorship', 'guidance']):
            return {"intent": "mentorship", "entities": {}}
        return {"intent": "general", "entities": {}}

class HinglishProcessor:
    def detect_hinglish(self, text: str) -> bool:
        return False
    
    def translate_to_english(self, text: str) -> Tuple[str, List[str]]:
        return text, []

class BiasDetector:
    def detect_bias(self, text: str) -> bool:
        return False

class SentimentAnalyzer:
    def analyze_sentiment(self, text: str) -> str:
        return "neutral"

class DataManager:
    def __init__(self):
        self.events = []
        self.professional_development = []
        self.data_path = os.path.join(os.path.dirname(__file__), 'data')
    
    def load_data(self):
        # Load events data
        events_path = os.path.join(self.data_path, 'events.json')
        if os.path.exists(events_path):
            with open(events_path, 'r') as f:
                self.events = json.load(f)
        
        # Load professional development data
        pd_path = os.path.join(self.data_path, 'professional_development.json')
        if os.path.exists(pd_path):
            with open(pd_path, 'r') as f:
                self.professional_development = json.load(f)
    
    def get_events(self, filters: Dict = None) -> List[Dict]:
        # Mock data for events
        return [
            {
                "title": "Women in Tech Conference 2025",
                "date": "2025-06-15",
                "description": "Annual conference featuring women leaders in technology"
            },
            {
                "title": "Career Development Workshop",
                "date": "2025-05-01",
                "description": "Interactive workshop on career growth and leadership"
            }
        ]
    
    def get_professional_development(self, filters: Dict = None) -> List[Dict]:
        # Mock data for professional development programs
        return [
            {
                "title": "Leadership Excellence Program",
                "type": "leadership",
                "description": "Comprehensive leadership training for aspiring managers"
            },
            {
                "title": "Technical Skills Bootcamp",
                "type": "technical",
                "description": "Intensive technical training in modern technologies"
            }
        ]
    
    def get_mentorship_programs(self, filters: Dict = None) -> List[Dict]:
        # Mock data for mentorship programs
        return [
            {
                "name": "Women in Leadership Mentorship",
                "description": "6-month program for aspiring women leaders",
                "duration": "6 months",
                "format": "Virtual sessions with industry leaders"
            },
            {
                "name": "Tech Career Acceleration",
                "description": "4-month tech mentorship program",
                "duration": "4 months",
                "format": "Weekly 1:1 sessions with tech leaders"
            }
        ]

class SecurityManager:
    def authenticate_user(self, username: str, password: str) -> bool:
        # Mock authentication
        return True
    
    def generate_token(self, username: str) -> str:
        # Mock token generation
        return "mock_token"

class ErrorHandler:
    def handle_error(self, error: Exception) -> Dict[str, Any]:
        return {
            "text": f"An error occurred: {str(error)}",
            "action": None
        }

class AshaAI:
    def __init__(self):
        self.session_manager = SessionManager()
        self.data_manager = DataManager()
        self.nlp = NLPProcessor()
        self.hinglish_processor = HinglishProcessor()
        self.bias_detector = BiasDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.security_manager = SecurityManager()
        self.error_handler = ErrorHandler()
    
    def process_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            # Create session if not exists
            if not session_id:
                session_id = self.session_manager.create_session("anonymous")
            
            # Check for Hinglish content
            if self.hinglish_processor.detect_hinglish(message):
                message, translations = self.hinglish_processor.translate_to_english(message)
            
            # Normalize and correct text
            message = self.nlp.normalize_text(message)
            
            # Detect intent and entities
            intent_data = self.nlp.process_text(message)
            intent = intent_data.get("intent")
            
            # Check for bias
            if self.bias_detector.detect_bias(message):
                return {
                    "text": "I noticed some potential bias in your message. Could you please rephrase it?",
                    "action": None
                }
            
            # Get sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(message)
            
            # Handle intent
            if intent == "events":
                # Add current date to intent data for event filtering
                intent_data["current_date"] = "2025-04-28"  # Using the provided current time
                response = self._handle_events(intent_data, session_id)
            elif intent == "professional_development":
                response = self._handle_professional_development(intent_data, session_id)
            elif intent == "mentorship":
                response = self._handle_mentorship_query(intent_data, session_id)
            else:
                response = self._handle_general_query(intent_data, session_id)
            
            # Update session context
            self.session_manager.update_context(session_id, {
                "last_intent": intent,
                "last_sentiment": sentiment
            })
            
            # Add to conversation history
            self.session_manager.add_to_history(session_id, message, response["text"])
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error processing your message. Please try again.",
                "action": None
            }
    
    def _handle_events(self, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        try:
            events = self.data_manager.get_events(intent_data)
            
            if not events:
                return {
                    "text": "I couldn't find any upcoming events. Would you like to explore professional development programs instead?",
                    "action": None
                }
            
            # Format response
            response = "Here are some upcoming events that might interest you:\n\n"
            for event in events:
                response += f"- {event['title']}\n"
                response += f"  Date: {event['date']}\n"
                response += f"  Description: {event['description']}\n\n"
            
            response += "\nWould you like more details about any of these events?"
            
            return {
                "text": response,
                "action": None
            }
            
        except Exception as e:
            logger.error(f"Error handling events: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error retrieving events. Please try again.",
                "action": None
            }
    
    def _handle_professional_development(self, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        try:
            programs = self.data_manager.get_professional_development(intent_data)
            
            if not programs:
                return {
                    "text": "I couldn't find any professional development programs matching your criteria. Would you like to explore other opportunities?",
                    "action": None
                }
            
            # Format response
            response = "Here are some professional development programs that might interest you:\n\n"
            for program in programs:
                response += f"- {program['title']}\n"
                response += f"  Type: {program['type']}\n"
                response += f"  Description: {program['description']}\n\n"
            
            response += "\nWould you like more details about any of these programs?"
            
            return {
                "text": response,
                "action": None
            }
            
        except Exception as e:
            logger.error(f"Error handling professional development: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error retrieving professional development programs. Please try again.",
                "action": None
            }
    
    def _handle_general_query(self, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        return {
            "text": "I can help you find events and professional development opportunities. What are you interested in?",
            "action": None
        }
    
    def _handle_mentorship_query(self, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle mentorship related queries."""
        try:
            entities = intent_data.get("entities", {})
            mentorship_programs = self.data_manager.get_mentorship_programs(entities)
            
            if not mentorship_programs:
                return {
                    "text": "I couldn't find any mentorship programs matching your criteria. Would you like to explore other professional development opportunities?",
                    "action": None
                }
            
            # Format response
            response = "Here are some mentorship programs that might interest you:\n\n"
            for program in mentorship_programs:
                response += f"- {program['name']}\n"
                response += f"  Duration: {program['duration']}\n"
                response += f"  Format: {program['format']}\n"
                response += f"  Description: {program['description']}\n\n"
            
            response += "\nWould you like more details about any of these programs?"
            
            return {
                "text": response,
                "action": None
            }
            
        except Exception as e:
            logger.error(f"Error handling mentorship query: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error retrieving mentorship programs. Please try again.",
                "action": None
            }

def main():
    try:
        # Initialize Asha AI
        asha = AshaAI()
        
        # Load data
        asha.data_manager.load_data()
        
        # Test events query
        print("\nTesting events query...")
        events_response = asha.process_message("Show me upcoming events and workshops")
        print(events_response["text"])
        
        # Test professional development query
        print("\nTesting professional development query...")
        pd_response = asha.process_message("What professional development programs are available?")
        print(pd_response["text"])
        
        # Test mentorship query
        print("\nTesting mentorship query...")
        mentorship_response = asha.process_message("I'm looking for a mentor")
        print(mentorship_response["text"])
    except Exception as e:
        print(f"Error: {str(e)}")
        logger.error(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
