import json
import random
from datetime import datetime
from typing import Dict, List, Optional
from utils.bias_detector import BiasDetector
from utils.knowledge_base import KnowledgeBase

class SimpleAsha:
    def __init__(self):
        # Hinglish to English mappings
        self.hinglish_map = {
            # Questions
            "kya": "what",
            "kaise": "how",
            "kab": "when",
            "kahan": "where",
            "kyun": "why",
            "kaun": "who",
            
            # Common words
            "hai": "is",
            "hain": "are",
            "karna": "do",
            "karna": "do",
            "chahiye": "want",
            "chaiye": "want",
            "lena": "take",
            "lun": "take",
            "lu": "take",
            "shi": "right",
            "sahi": "right",
            "rhega": "will be",
            "rahega": "will be",
            
            # Education related
            "course": "course",
            "kors": "course",
            "padhai": "study",
            "padhai": "study",
            "siksha": "education",
            "shiksha": "education",
            
            # Job related
            "naukri": "job",
            "job": "job",
            "kaam": "work",
            "salary": "salary",
            "paisa": "money",
            "paise": "money",
            
            # Common misspellings
            "cours": "course",
            "corse": "course",
            "kareer": "career",
            "carrer": "career",
            "carrier": "career",
            "website": "website",
            "site": "website",
            "portal": "website",
            "about": "about",
            "baare": "about",
            "bare": "about",
            "batao": "tell",
            "bolo": "tell",
            "jobsforher": "jobsforher",
            "foundation": "foundation",
            "company": "company",
            "platform": "platform"
        }
        self.responses = {
            'greeting': [
                "Hello! I'm Asha, your AI career companion. How can I help you today?",
                "Hi there! I'm Asha, here to assist with your career journey. What can I do for you?"
            ],
            'job_search': [
                "I can help you find relevant job opportunities. What kind of role are you looking for?",
                "Let's explore job openings together. What's your preferred job category?"
            ],
            'education': [
                "I can provide information about various educational programs and courses. What field interests you?",
                "There are many learning opportunities available. Which subject would you like to know more about?"
            ],
            'professional_development': [
                "Professional development is crucial for career growth. Would you like to explore mentorship programs or skill development courses?",
                "I can help you find resources for professional growth. Are you interested in mentorship or specific skill development?"
            ],
            'default': [
                "I'm here to help with your career journey. Could you please provide more details about what you're looking for?",
                "I want to assist you better. Could you elaborate on your question?"
            ]
        }
        
        # Initialize components
        self.bias_detector = BiasDetector()
        self.knowledge_base = KnowledgeBase()
        self.conversation_history = {}
        self.analytics = {}

    def translate_hinglish(self, text: str) -> str:
        """Convert Hinglish text to English"""
        words = text.split()
        translated = []
        
        for word in words:
            # Check if word exists in hinglish mapping
            if word in self.hinglish_map:
                translated.append(self.hinglish_map[word])
            else:
                translated.append(word)
        
        return " ".join(translated)

    def get_response(self, user_input: str, session_id: Optional[str] = None) -> Dict:
        try:
            # Initialize response dictionary
            response = {"text": "", "type": "text"}

            # Track analytics
            if session_id not in self.analytics:
                self.analytics[session_id] = {
                    "total_interactions": 0,
                    "biased_queries": 0,
                    "successful_responses": 0
                }
            self.analytics[session_id]["total_interactions"] += 1

            # Translate Hinglish to English
            processed_input = self.translate_hinglish(user_input.lower())

            # Check for bias
            has_bias, biases, suggestions = self.bias_detector.detect_bias(processed_input)
            if has_bias:
                self.analytics[session_id]["biased_queries"] += 1
                return {"text": f"I noticed some potential bias in your query. Here's a more inclusive way to phrase it: {suggestions[0]}"}

            # Check for greetings
            if any(word in processed_input for word in ['hi', 'hello', 'hey', 'namaste']):
                return {"text": "👋 Hello! I'm Asha, your AI career companion. I can help you with:\n\n" + \
                        "1. Finding job opportunities\n" + \
                        "2. Career guidance and mentorship\n" + \
                        "3. Professional development courses\n" + \
                        "4. Upcoming events and workshops\n" + \
                        "5. Women returnee programs\n\n" + \
                        "What would you like to explore?"}

            # Check for yes/no responses
            if processed_input in ['yes', 'yeah', 'sure', 'okay', 'ok', 'yep', 'yup', 'ha', 'haan']:
                return {"text": "Great! Let me help you explore your career options. Are you interested in:\n\n" + \
                        "1. Job Search & Opportunities\n" + \
                        "2. Skill Development & Training\n" + \
                        "3. Mentorship & Guidance\n" + \
                        "4. Events & Networking\n\n" + \
                        "Please choose a number or tell me what you're looking for! 🌟"}

            if processed_input in ['no', 'nah', 'nope', 'not', 'nahi']:
                return {"text": "No problem! Feel free to ask me about:\n\n" + \
                        "• Job opportunities\n" + \
                        "• Career development\n" + \
                        "• Professional courses\n" + \
                        "• Mentorship programs\n" + \
                        "• Upcoming events\n\n" + \
                        "I'm here to help! 😊"}

            # Check for help queries
            if 'help' in processed_input or 'what can you do' in processed_input:
                return {"text": "I'm here to help with your career journey! You can ask me about:\n\n" + \
                        "• Job opportunities & openings\n" + \
                        "• Career guidance & planning\n" + \
                        "• Professional development\n" + \
                        "• Mentorship programs\n" + \
                        "• Upcoming events 📅\n\n" + \
                        "What would you like to explore?"}

            # Check for job-related queries
            if any(word in processed_input for word in ['job', 'work', 'career', 'opportunity', 'position', 'opening', 'vacancy']):
                job_listings = self.knowledge_base.get_job_listings()
                if job_listings:
                    response["text"] = "💼 Here are some exciting job opportunities:\n\n"
                    for job in job_listings[:3]:
                        response["text"] += f"• {job['title']} at {job['company']}\n"
                        response["text"] += f"  📍 Location: {job['location']}\n"
                        response["text"] += f"  💵 {job['salary']}\n\n"
                    response["text"] += "Would you like to know more about any of these positions?"
                else:
                    response["text"] = "I'm currently updating our job listings. Please check back in a few minutes or tell me what kind of job you're looking for!"

            # Check for event-related queries
            elif any(word in processed_input for word in ['event', 'workshop', 'webinar', 'conference']):
                events = self.knowledge_base.get_events()
                if events:
                    response["text"] = "📅 Here are upcoming events you might be interested in:\n\n"
                    for event in events[:3]:
                        response["text"] += f"• {event['title']}\n"
                        response["text"] += f"  📆 Date: {event['date']}\n"
                        response["text"] += f"  📍 {event['location']}\n\n"
                    response["text"] += "Would you like to register for any of these events?"
                else:
                    response["text"] = "I'm currently updating our event calendar. Please check back soon for exciting events and workshops!"

            # Check for mentorship-related queries
            elif any(word in processed_input for word in ['mentor', 'guide', 'advice', 'guidance']):
                mentors = self.knowledge_base.get_mentors()
                if mentors:
                    response["text"] = "👩‍💻 Here are some mentorship opportunities:\n\n"
                    for mentor in mentors[:3]:
                        response["text"] += f"• {mentor['name']} - {mentor['expertise']}\n"
                        response["text"] += f"  💼 Experience: {mentor['experience']} years\n"
                        response["text"] += f"  🎓 {mentor['background']}\n\n"
                    response["text"] += "Would you like to connect with any of these mentors?"
                else:
                    response["text"] = "I'm currently updating our mentor database. In the meantime, would you like to tell me what kind of mentorship you're looking for?"

            # Check for education/course-related queries
            elif any(word in processed_input for word in ['course', 'training', 'learn', 'study', 'education']):
                courses = self.knowledge_base.get_courses()
                if courses:
                    response["text"] = "📚 Here are some recommended courses:\n\n"
                    for course in courses[:3]:
                        response["text"] += f"• {course['title']}\n"
                        response["text"] += f"  🕒 Duration: {course['duration']}\n"
                        response["text"] += f"  💰 Fee: {course['fee']}\n\n"
                    response["text"] += "Would you like more details about any of these courses?"
                else:
                    response["text"] = "I'm currently updating our course catalog. Please tell me what skills you'd like to develop!"

            # Default response if no specific intent is matched
            if not response["text"]:
                response["text"] = "I'm here to help with your career journey! You can ask me about:\n\n" + \
                                "• Job opportunities & openings\n" + \
                                "• Career guidance & planning\n" + \
                                "• Professional development\n" + \
                                "• Mentorship programs\n" + \
                                "• Upcoming events 📅\n\n" + \
                                "What would you like to explore?"

            # Track successful response
            self.analytics[session_id]["successful_responses"] += 1

            # Store conversation history
            if session_id not in self.conversation_history:
                self.conversation_history[session_id] = []
            self.conversation_history[session_id].append({
                "user_input": user_input,
                "response": response["text"] if response["text"] else "I'm here to help! Please let me know what you're looking for.",
                "timestamp": datetime.now().isoformat()
            })

            return response

        except Exception as e:
            print(f"Error processing request: {str(e)}")
            return {"text": "I apologize, but I encountered an error. Please try rephrasing your question or contact support if the issue persists."}

    def get_analytics(self, session_id: Optional[str] = None) -> Dict:
        """Get analytics data for a session or all sessions."""
        if session_id:
            return self.analytics.get(session_id, {})
        return {
            "total_sessions": len(self.analytics),
            "total_interactions": sum(s["total_interactions"] for s in self.analytics.values()),
            "total_biased_queries": sum(s["biased_queries"] for s in self.analytics.values()),
            "successful_responses": sum(s["successful_responses"] for s in self.analytics.values())
        }

    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for a session."""
        return self.conversation_history.get(session_id, [])

def main():
    asha = SimpleAsha()
    
    print("\nWelcome to JobsForHer! 👋")
    print("I'm Asha, your AI assistant for career guidance.")
    print("\nI can help you with:")
    print("1. Finding jobs and career opportunities")
    print("2. Career guidance and mentorship")
    print("3. Education and skill development")
    print("4. Professional development resources")
    print("\nYou can ask in English or Hinglish!")
    print("Examples:")
    print("- 'Tell me about JobsForHer'")
    print("- 'What jobs are available?'")
    print("- 'naukri ke liye kya karna hoga?'")
    print("- 'career guidance chahiye'")
    print("\nType 'exit' or 'quit' to end the conversation")
    print("-" * 50)

    while True:
        try:
            # Get user input
            user_input = input("\nYou: ").strip()
            
            # Check if user wants to exit
            if user_input.lower() in ['exit', 'quit', 'bye', 'goodbye']:
                print("\nAsha: Goodbye! Have a great day! 👋")
                break
            
            # Skip empty inputs
            if not user_input:
                continue
            
            # Get response from chatbot
            response = asha.get_response(user_input)
            print(f"\nAsha: {response['text']}")
            
        except KeyboardInterrupt:
            print("\n\nAsha: Goodbye! Have a great day! 👋")
            break
        except Exception as e:
            print(f"\nAsha: I apologize, but I encountered an error. Please try again.")

if __name__ == "__main__":
    main() 