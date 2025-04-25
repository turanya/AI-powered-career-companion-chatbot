import asyncio
from typing import Dict, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
import uuid

from core.context_manager import ConversationContext
from core.security_manager import SecurityManager
from core.bias_detector import BiasDetector
from core.knowledge_base import KnowledgeBase
from core.analytics_manager import AnalyticsManager
from core.error_handler import ErrorHandler, ErrorType
from core.feedback_manager import FeedbackManager, FeedbackType

class AshaAI:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize components
        self.context = ConversationContext()
        self.security = SecurityManager()
        self.bias_detector = BiasDetector()
        self.knowledge_base = KnowledgeBase()
        self.analytics = AnalyticsManager()
        self.error_handler = ErrorHandler()
        self.feedback_manager = FeedbackManager()
        
    async def initialize(self):
        """Initialize the bot with necessary data."""
        try:
            # Update knowledge base
            api_key = os.getenv("JOBSFORHER_API_KEY")
            await asyncio.gather(
                self.knowledge_base.update_job_listings(api_key),
                self.knowledge_base.update_events(),
                self.knowledge_base.update_mentorship_programs()
            )
            
        except Exception as e:
            self.error_handler.report_error(f"Initialization error: {str(e)}")
            
    async def process_message(self, user_input: str) -> Dict:
        """Process user message and generate response."""
        start_time = datetime.now()
        response_id = str(uuid.uuid4())
        
        try:
            # Check for bias in input
            bias_type, confidence, suggestion = self.bias_detector.detect_bias(user_input)
            if bias_type != "none" and confidence > 0.7:
                self.analytics.track_bias_incident(user_input, bias_type, confidence)
                self.feedback_manager.report_bias(user_input, "user_input")
                return {
                    "response": suggestion,
                    "response_id": response_id,
                    "requires_feedback": True
                }
                
            # Add message to context
            self.context.add_message("user", user_input)
            
            # Generate response based on context
            response = await self._generate_response(user_input)
            response["response_id"] = response_id
            
            # Check response for bias
            if self.bias_detector.check_response_bias(response["text"]):
                alternative = self.bias_detector.get_inclusive_alternative(response["text"])
                self.feedback_manager.report_bias(response["text"], "bot_response")
                response["text"] = alternative
                
            # Track analytics
            duration = (datetime.now() - start_time).total_seconds()
            self.analytics.track_interaction(user_input, response["text"], duration)
            
            # Add response to context
            self.context.add_message("assistant", response["text"])
            
            # Mark for feedback if needed
            response["requires_feedback"] = self._should_request_feedback()
            
            return response
            
        except Exception as e:
            # Handle errors and provide fallback
            fallback_response, error_type = self.error_handler.handle_error(e, {
                "user_input": user_input,
                "context": self.context.get_context()
            })
            
            # Track error
            self.analytics.track_error(str(error_type), str(e))
            
            # If it's a critical error, suggest human support
            if error_type in [ErrorType.SECURITY_ERROR, ErrorType.SYSTEM_ERROR]:
                return {
                    "response": self._get_human_support_message(fallback_response),
                    "response_id": response_id,
                    "requires_human_support": True
                }
                
            return {
                "response": fallback_response,
                "response_id": response_id,
                "requires_feedback": True
            }
            
    async def _generate_response(self, user_input: str) -> Dict:
        """Generate appropriate response based on user input."""
        # Get relevant information from knowledge base
        jobs = self.knowledge_base.get_relevant_jobs(user_input)
        events = self.knowledge_base.get_upcoming_events()
        mentorship = self.knowledge_base.get_mentorship_opportunities()
        
        # Generate contextual response
        response = {
            "text": "I understand you're asking about careers. ",
            "data": {}
        }
        
        if "job" in user_input.lower() or "career" in user_input.lower():
            if jobs:
                response["text"] += f"I found {len(jobs)} relevant job opportunities. "
                response["data"]["jobs"] = jobs
                
        if "event" in user_input.lower() or "workshop" in user_input.lower():
            if events:
                response["text"] += f"There are {len(events)} upcoming events that might interest you. "
                response["data"]["events"] = events
                
        if "mentor" in user_input.lower() or "guidance" in user_input.lower():
            if mentorship:
                response["text"] += f"I found {len(mentorship)} mentorship opportunities. "
                response["data"]["mentorship"] = mentorship
                
        return response
        
    def collect_feedback(self, response_id: str) -> None:
        """Collect user feedback for continuous improvement."""
        try:
            rating = input("Please rate this response (1-5): ")
            feedback_type = input("What type of feedback? (accuracy/relevance/bias/general): ")
            comments = input("Any additional comments? (optional): ")
            
            self.feedback_manager.collect_response_feedback(
                response_id,
                int(rating),
                FeedbackType[feedback_type.upper()],
                comments
            )
            
            # If rating is low, suggest improvement
            if int(rating) <= 2:
                suggestion = input("How could we improve? (optional): ")
                if suggestion:
                    self.feedback_manager.suggest_improvement(
                        feedback_type,
                        suggestion,
                        self.context.get_context()
                    )
                    
        except ValueError as e:
            print("Invalid input. Feedback not recorded.")
            
    def _should_request_feedback(self) -> bool:
        """Determine if we should request feedback for this interaction."""
        # Request feedback every 5 interactions or after potential issues
        interactions = len(self.context.conversation_history)
        return interactions % 5 == 0 or interactions <= 2
        
    def _get_human_support_message(self, fallback_msg: str) -> str:
        """Generate message for human support redirection."""
        support_email = os.getenv("SUPPORT_EMAIL", "support@jobsforher.com")
        return f"{fallback_msg}\n\nFor immediate assistance, please contact our support team at {support_email}"
        
    def save_analytics(self):
        """Save analytics and feedback data."""
        self.analytics.save_analytics()
        
    def get_performance_insights(self) -> Dict:
        """Get insights about bot performance."""
        analytics = self.analytics.get_performance_metrics()
        feedback = self.feedback_manager.get_feedback_summary()
        learning = self.feedback_manager.get_learning_insights()
        
        return {
            "analytics": analytics,
            "feedback": feedback,
            "learning_insights": learning
        }

async def main():
    # Initialize bot
    asha = AshaAI()
    await asha.initialize()
    
    print("\nWelcome to Asha AI! 👋")
    print("I'm here to help you with your career journey.")
    print("You can ask me about jobs, career guidance, or upcoming events.")
    print("Type 'exit' to end our conversation.\n")
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\nGoodbye! Have a great day! 👋")
                break
                
            if not user_input:
                continue
                
            response = await asha.process_message(user_input)
            print(f"\nAsha: {response['text']}")
            
            # Display additional data
            if 'data' in response:
                if 'jobs' in response['data']:
                    print("\nRelevant Jobs:")
                    for job in response['data']['jobs'][:3]:
                        print(f"- {job['title']} at {job['company']}")
                        if job.get('women_friendly'):
                            print("  ✨ Women-friendly workplace")
                        print(f"  💪 Flexibility Score: {job['flexibility_score']:.1f}")
                        
                if 'events' in response['data']:
                    print("\nUpcoming Events:")
                    for event in response['data']['events'][:3]:
                        print(f"- {event['title']} on {event['date']}")
                        
                if 'mentorship' in response['data']:
                    print("\nMentorship Opportunities:")
                    for program in response['data']['mentorship'][:3]:
                        print(f"- {program['title']} with {program['mentor']}")
                        
            # Collect feedback if needed
            if response.get('requires_feedback', False):
                asha.collect_feedback(response['response_id'])
                
            # Redirect to human support if needed
            if response.get('requires_human_support', False):
                print("\nℹ️ You will be connected with our support team shortly.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye! Have a great day! 👋")
            break
        except Exception as e:
            print(f"\nAsha: I apologize, but I encountered an error. Please try again.")
            
    # Save analytics before exit
    asha.save_analytics()

if __name__ == "__main__":
    asyncio.run(main()) 