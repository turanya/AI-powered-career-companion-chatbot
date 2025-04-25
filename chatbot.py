import json
import csv
import datetime
import hashlib
import re
import random
from typing import Dict, List, Optional, Tuple, Any, Set
import os
from dotenv import load_dotenv
from config import (
    CHATBOT_NAME,
    CHATBOT_TITLE,
    CHATBOT_ICON,
    CHATBOT_THEME,
    CHATBOT_UI,
    CHATBOT_ANIMATIONS,
    RESPONSE_DELAY,
    ORGANIZATION,
    PROGRAMS
)
from rag_engine import RAGEngine
from difflib import get_close_matches
from api_manager import APIManager
import logging
from security_manager import SecurityManager, EncryptionType
from update_manager import UpdateManager, DataUpdate
from performance_monitor import PerformanceMonitor, MetricType
import time
from context_manager import ContextManager, ConversationContext
from api_integrations import APIConfig, JobAPIAggregator
from bias_detector import BiasDetector, BiasIncident
from error_handler import ErrorHandler, ErrorType, error_handler
from spellchecker import SpellChecker
from nltk import WordNetLemmatizer
from nltk.corpus import stopwords
from fastapi import HTTPException, status
import jwt
from functools import wraps

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Women empowerment keywords
EMPOWERMENT_KEYWORDS = [
    "women", "female", "career", "leadership", "empowerment", "equality", 
    "diversity", "inclusion", "opportunity", "growth", "development", "mentorship"
]

class Chatbot:
    def __init__(self):
        self.session_manager = SessionManager()
        self.data_manager = DataManager()
        self.nlp = NaturalLanguageProcessor()
        self.bias_detector = BiasDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.hinglish_processor = HinglishProcessor()
        self.security_manager = SecurityManager()
        self.error_handler = ErrorHandler()
        
        # Load initial data
        self.data_manager.load_data()
    
    def process_message(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Process an incoming message and return a response."""
        try:
            # Create session if not exists
            if not session_id:
                session_id = self.session_manager.create_session("anonymous")
            
            # Check for Hinglish content
            if self.hinglish_processor.detect_hinglish(message):
                message, translations = self.hinglish_processor.translate_to_english(message)
            
            # Normalize and correct text
            message = self.nlp.normalize_text(message)
            corrected_message, corrections = self.nlp.correct_spelling(message)
            
            # Detect intent and entities
            intent, intent_data = self.nlp.detect_intent(corrected_message)
            
            # Check for bias
            bias_found = self.bias_detector.check_bias(corrected_message)
            if bias_found:
                for bias_type in bias_found:
                    response = self.bias_detector.get_inclusive_response(bias_type)
                    return {"text": response, "action": None}
            
            # Analyze sentiment
            sentiment = self.sentiment_analyzer.analyze_sentiment(corrected_message)
            
            # Get response based on intent
            response = self._get_response(intent, intent_data, session_id)
            
            # Add sentiment-based follow-up if needed
            if sentiment in ['negative', 'neutral']:
                response["text"] += "\n" + self.sentiment_analyzer.get_sentiment_response(sentiment)
            
            # Update session context
            self.session_manager.update_context(session_id, {
                "last_intent": intent,
                "last_sentiment": sentiment,
                "entities": intent_data.get("entities", {})
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
    
    def _get_response(self, intent: str, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Generate a response based on the detected intent."""
        try:
            if intent == "job_search":
                return self._handle_job_search(intent_data, session_id)
            elif intent == "career_help":
                return self._handle_career_help(intent_data, session_id)
            elif intent == "education":
                return self._handle_education_query(intent_data, session_id)
            elif intent == "mentorship":
                return self._handle_mentorship_query(intent_data, session_id)
            else:
                return {
                    "text": "I'm not sure I understand. Could you please rephrase your question?",
                    "action": None
                }
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error generating a response. Please try again.",
                "action": None
            }
    
    def _handle_job_search(self, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle job search related queries."""
        try:
            entities = intent_data.get("entities", {})
            jobs = self.data_manager.get_job_listings(entities)
            
            if not jobs:
                return {
                    "text": "I couldn't find any jobs matching your criteria. Would you like to broaden your search?",
                    "action": None
                }
            
            response = "Here are some jobs that might interest you:\n\n"
            for job in jobs[:3]:  # Show top 3 matches
                response += f"- {job['title']} at {job['company']}\n"
            
            response += "\nWould you like more details about any of these positions?"
            
            return {"text": response, "action": None}
        except Exception as e:
            logger.error(f"Error handling job search: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error with the job search. Please try again.",
                "action": None
            }
    
    def _handle_career_help(self, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle career guidance related queries."""
        try:
            entities = intent_data.get("entities", {})
            resources = self.data_manager.get_resources("career_development")
            
            if not resources:
                return {
                    "text": "I'd be happy to help with your career. What specific aspect would you like guidance on?",
                    "action": None
                }
            
            response = "Here are some resources that might help:\n\n"
            for resource in resources[:3]:  # Show top 3 matches
                response += f"- {resource['title']}: {resource['description']}\n"
            
            response += "\nWould you like more specific guidance in any area?"
            
            return {"text": response, "action": None}
        except Exception as e:
            logger.error(f"Error handling career help: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error providing career guidance. Please try again.",
                "action": None
            }
    
    def _handle_education_query(self, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle education related queries."""
        try:
            entities = intent_data.get("entities", {})
            resources = self.data_manager.get_resources("skill_development")
            
            if not resources:
                return {
                    "text": "I can help you find educational resources. What specific skills are you interested in developing?",
                    "action": None
                }
            
            response = "Here are some learning resources that might interest you:\n\n"
            for resource in resources[:3]:  # Show top 3 matches
                response += f"- {resource['title']}: {resource['description']}\n"
            
            response += "\nWould you like more information about any of these learning opportunities?"
            
            return {"text": response, "action": None}
        except Exception as e:
            logger.error(f"Error handling education query: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error finding educational resources. Please try again.",
                "action": None
            }
    
    def _handle_mentorship_query(self, intent_data: Dict[str, Any], session_id: str) -> Dict[str, Any]:
        """Handle mentorship related queries."""
        try:
            entities = intent_data.get("entities", {})
            opportunities = self.data_manager.get_mentorship_opportunities(entities)
            
            if not opportunities:
                return {
                    "text": "I can help you find a mentor. What specific area would you like mentorship in?",
                    "action": None
                }
            
            response = "Here are some mentorship opportunities that might interest you:\n\n"
            for opp in opportunities[:3]:  # Show top 3 matches
                response += f"- {opp['mentor_name']}: {opp['expertise']}\n"
            
            response += "\nWould you like to learn more about any of these mentorship opportunities?"
            
            return {"text": response, "action": None}
        except Exception as e:
            logger.error(f"Error handling mentorship query: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error finding mentorship opportunities. Please try again.",
                "action": None
            }

class SessionManager:
    def __init__(self):
        self.session_data = {}
        self.conversation_history = []
    
    def create_session(self, user_id: str) -> str:
        session_id = hashlib.sha256(f"{user_id}{datetime.datetime.now()}".encode()).hexdigest()
        self.session_data[session_id] = {
            'user_id': user_id,
            'created_at': datetime.datetime.now(),
            'context': {},
            'last_interaction': datetime.datetime.now(),
            'preferences': {},
            'interaction_count': 0,
            'career_goals': [],
            'skill_gaps': [],
            'interests': []
        }
        return session_id
    
    def update_context(self, session_id: str, context: Dict):
        if session_id in self.session_data:
            self.session_data[session_id]['context'].update(context)
            self.session_data[session_id]['last_interaction'] = datetime.datetime.now()
            self.session_data[session_id]['interaction_count'] += 1
    
    def get_context(self, session_id: str) -> Dict:
        return self.session_data.get(session_id, {}).get('context', {})
    
    def update_preferences(self, session_id: str, preferences: Dict):
        if session_id in self.session_data:
            self.session_data[session_id]['preferences'].update(preferences)
    
    def get_preferences(self, session_id: str) -> Dict:
        return self.session_data.get(session_id, {}).get('preferences', {})
    
    def update_career_goals(self, session_id: str, goals: List[str]):
        if session_id in self.session_data:
            self.session_data[session_id]['career_goals'] = goals
    
    def get_career_goals(self, session_id: str) -> List[str]:
        return self.session_data.get(session_id, {}).get('career_goals', [])
    
    def update_skill_gaps(self, session_id: str, skills: List[str]):
        if session_id in self.session_data:
            self.session_data[session_id]['skill_gaps'] = skills
    
    def get_skill_gaps(self, session_id: str) -> List[str]:
        return self.session_data.get(session_id, {}).get('skill_gaps', [])
    
    def update_interests(self, session_id: str, interests: List[str]):
        if session_id in self.session_data:
            self.session_data[session_id]['interests'] = interests
    
    def get_interests(self, session_id: str) -> List[str]:
        return self.session_data.get(session_id, {}).get('interests', [])
    
    def add_to_history(self, session_id: str, user_message: str, bot_response: str):
        if session_id in self.session_data:
            if 'conversation_history' not in self.session_data[session_id]:
                self.session_data[session_id]['conversation_history'] = []
            
            self.session_data[session_id]['conversation_history'].append({
                'timestamp': datetime.datetime.now(),
                'user_message': user_message,
                'bot_response': bot_response
            })
            
            # Keep only the last 10 messages for context
            if len(self.session_data[session_id]['conversation_history']) > 10:
                self.session_data[session_id]['conversation_history'] = self.session_data[session_id]['conversation_history'][-10:]

class DataManager:
    def __init__(self):
        self.job_listings = []
        self.events = []
        self.mentorship_opportunities = []
        self.last_update = None
        self.faqs = {}
        self.resources = {}
        self.success_stories = []
        self.career_paths = []
        self.skills_data = []
        self.api_manager = APIManager()
        self.security_manager = SecurityManager()
    
    def load_data(self):
        try:
            # Load job listings from API with security measures
            jobs_data = self.api_manager.get_jobs()
            self.job_listings = self.security_manager.anonymize_data(jobs_data)
            
            # Load events from API with security measures
            events_data = self.api_manager.get_events()
            self.events = self.security_manager.anonymize_data(events_data)
            
            # Load mentorship opportunities from API with security measures
            mentorship_data = self.api_manager.get_mentorship_opportunities()
            self.mentorship_opportunities = self.security_manager.anonymize_data(mentorship_data)
            
            # Load other data with security measures
            self.load_faqs()
            self.load_resources()
            self.load_success_stories()
            self.load_career_paths()
            self.load_skills_data()
            
            self.last_update = datetime.datetime.now()
            
            # Log rate limit status
            rate_status = self.api_manager.get_rate_limit_status()
            logger.info(f"Rate limit status after loading data: {rate_status}")
            
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            self._load_local_data()
    
    def _load_local_data(self):
        """Load data from local files as fallback."""
        try:
            # Load job listings from local file
            with open('data/job_listings.csv', 'r') as f:
                reader = csv.DictReader(f)
                self.job_listings = list(reader)
            
            # Load events from local file
            with open('data/events.json', 'r') as f:
                data = json.load(f)
                self.events = data.get('events', [])
            
            # Load mentorship opportunities from local file
            with open('data/mentorship.json', 'r') as f:
                data = json.load(f)
                self.mentorship_opportunities = data.get('mentorship_opportunities', [])
            
            logger.info("Successfully loaded data from local files")
        except Exception as e:
            logger.error(f"Error loading local data: {str(e)}")
    
    @SecurityManager.require_auth(required_role='admin')
    async def update_data(self, token: str):
        """Update data from external sources."""
        try:
            # Update job listings
            jobs_data = await self.api_manager.get_jobs()
            self.job_listings = self.security_manager.anonymize_data(jobs_data)
            
            # Update events
            events_data = await self.api_manager.get_events()
            self.events = self.security_manager.anonymize_data(events_data)
            
            # Update mentorship opportunities
            mentorship_data = await self.api_manager.get_mentorship_opportunities()
            self.mentorship_opportunities = self.security_manager.anonymize_data(mentorship_data)
            
            # Update other data
            self.load_faqs()
            self.load_resources()
            self.load_success_stories()
            self.load_career_paths()
            self.load_skills_data()
            
            self.last_update = datetime.datetime.now()
            return {"status": "success", "timestamp": self.last_update}
        except Exception as e:
            logger.error(f"Error updating data: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating data: {str(e)}"
            )
    
    def get_user_data(self, user_id: str, token: str) -> Dict:
        """Get user-specific data with authentication and access control."""
        try:
            # Verify token and get user info
            user_info = self.security_manager.verify_token(token)
            
            # Check if user has access to their own data
            if user_info['user_id'] != user_id:
                raise PermissionError("Access denied")
            
            # Get and anonymize user data
            user_data = {
                'profile': self._get_user_profile(user_id),
                'applications': self._get_user_applications(user_id),
                'preferences': self._get_user_preferences(user_id)
            }
            
            return self.security_manager.anonymize_data(user_data)
            
        except Exception as e:
            logger.error(f"Error getting user data: {str(e)}")
            raise
    
    def _get_user_profile(self, user_id: str) -> Dict:
        """Get user profile with security measures."""
        # Implementation would fetch from database
        pass
    
    def _get_user_applications(self, user_id: str) -> List[Dict]:
        """Get user applications with security measures."""
        # Implementation would fetch from database
        pass
    
    def _get_user_preferences(self, user_id: str) -> Dict:
        """Get user preferences with security measures."""
        # Implementation would fetch from database
        pass
    
    def load_faqs(self):
        # Define FAQs programmatically
        self.faqs = {
            "general": [
                {
                    "question": "How do I get started with JobsForHer?",
                    "answer": "You can start by creating an account using the signup feature. Once registered, you'll have access to all our features including job listings, events, and mentorship programs tailored for women professionals."
                },
                {
                    "question": "What features are available on JobsForHer?",
                    "answer": "We offer job listings from women-friendly companies, community events focused on women's career growth, training sessions, and mentorship programs with successful women leaders. Each feature is designed to support your professional journey."
                }
            ],
            "account": [
                {
                    "question": "How do I create an account?",
                    "answer": "You can create an account by using the signup feature. I'll guide you through the process, collecting your email, name, and career interests."
                },
                {
                    "question": "How do I update my profile?",
                    "answer": "You can update your profile at any time. Just let me know you want to update your profile, and I'll guide you through the process."
                }
            ],
            "jobs": [
                {
                    "question": "How do I apply for jobs?",
                    "answer": "You can browse job listings in the Careers section, click on any job you're interested in, and use the 'Apply Now' button to submit your application. Many of our partner companies are committed to gender diversity and inclusion."
                },
                {
                    "question": "Can I track my job applications?",
                    "answer": "Yes! Once you're logged in, you can track all your job applications in the 'My Applications' section."
                },
                {
                    "question": "Are there jobs specifically for women?",
                    "answer": "While we don't exclusively list jobs for women, we partner with companies that are committed to gender diversity and inclusion. These companies actively seek to hire and promote women professionals."
                }
            ],
            "events": [
                {
                    "question": "How do I register for events?",
                    "answer": "Browse the Events calendar, select an event you're interested in, and click the 'Register' button. You'll receive a confirmation email."
                },
                {
                    "question": "Are events free?",
                    "answer": "We offer both free and paid events. The pricing information is clearly displayed on each event's page."
                },
                {
                    "question": "What types of events do you offer?",
                    "answer": "We offer a variety of events including career fairs, networking meetups, skill-building workshops, leadership development programs, and industry-specific conferences. All events are designed to support women's professional growth."
                }
            ],
            "mentorship": [
                {
                    "question": "How does the mentorship program work?",
                    "answer": "Our mentorship program connects you with experienced women professionals in your field. You can browse mentor profiles, select one that matches your goals, and request a mentorship session."
                },
                {
                    "question": "How long does a mentorship session last?",
                    "answer": "Mentorship sessions typically last 30-60 minutes, depending on the mentor's availability and your needs."
                },
                {
                    "question": "Who are the mentors?",
                    "answer": "Our mentors are successful women professionals from various industries who have volunteered to share their knowledge and experience. They include CEOs, entrepreneurs, industry experts, and leaders who have broken glass ceilings."
                }
            ],
            "career_development": [
                {
                    "question": "How can I advance my career?",
                    "answer": "We offer various resources to help you advance your career, including mentorship programs, skill-building workshops, leadership development courses, and networking events. You can also explore different career paths and success stories of women who have achieved significant milestones."
                },
                {
                    "question": "How do I identify my career goals?",
                    "answer": "We can help you identify your career goals through guided conversations. I can ask you questions about your interests, skills, values, and aspirations to help you clarify your career direction."
                },
                {
                    "question": "How can I overcome career challenges as a woman?",
                    "answer": "Many women face unique challenges in their careers. We offer resources, mentorship, and community support to help you navigate these challenges. Our success stories and career guides provide insights from women who have overcome similar obstacles."
                }
            ]
        }
    
    def load_resources(self):
        # Define resources programmatically
        self.resources = {
            "career_development": [
                {
                    "title": "Resume Writing Guide for Women",
                    "url": "https://example.com/resume-guide-women",
                    "description": "Learn how to create a compelling resume that highlights your achievements and skills effectively."
                },
                {
                    "title": "Interview Preparation Tips",
                    "url": "https://example.com/interview-tips",
                    "description": "Prepare for your job interviews with these expert tips and strategies, including how to address gender-related questions professionally."
                },
                {
                    "title": "Salary Negotiation Guide",
                    "url": "https://example.com/salary-negotiation",
                    "description": "Learn effective strategies for negotiating your salary and benefits to ensure you receive fair compensation."
                }
            ],
            "skill_development": [
                {
                    "title": "Python for Beginners",
                    "url": "https://example.com/python-beginners",
                    "description": "Start your programming journey with this comprehensive Python course designed for beginners."
                },
                {
                    "title": "Data Science Fundamentals",
                    "url": "https://example.com/data-science",
                    "description": "Learn the basics of data science and analytics, a field with growing opportunities for women professionals."
                },
                {
                    "title": "Leadership Skills for Women",
                    "url": "https://example.com/leadership-skills",
                    "description": "Develop essential leadership skills to advance your career and make a greater impact in your organization."
                }
            ],
            "wellness": [
                {
                    "title": "Work-Life Balance Guide",
                    "url": "https://example.com/work-life-balance",
                    "description": "Tips for maintaining a healthy balance between work and personal life, especially important for women professionals."
                },
                {
                    "title": "Stress Management Techniques",
                    "url": "https://example.com/stress-management",
                    "description": "Learn effective techniques for managing stress in the workplace and maintaining your well-being."
                },
                {
                    "title": "Building Confidence in Professional Settings",
                    "url": "https://example.com/building-confidence",
                    "description": "Develop strategies to build and maintain confidence in professional settings, helping you overcome imposter syndrome and other confidence challenges."
                }
            ],
            "networking": [
                {
                    "title": "Effective Networking Strategies",
                    "url": "https://example.com/networking-strategies",
                    "description": "Learn how to build and leverage your professional network to advance your career."
                },
                {
                    "title": "Creating Your Personal Brand",
                    "url": "https://example.com/personal-branding",
                    "description": "Develop a strong personal brand that highlights your unique value and expertise."
                },
                {
                    "title": "LinkedIn Profile Optimization",
                    "url": "https://example.com/linkedin-optimization",
                    "description": "Learn how to optimize your LinkedIn profile to attract opportunities and showcase your professional achievements."
                }
            ]
        }
    
    def load_success_stories(self):
        # Define success stories programmatically
        self.success_stories = [
            {
                "id": "1",
                "name": "Priya Sharma",
                "title": "From Stay-at-Home Mom to Tech Entrepreneur",
                "industry": "Technology",
                "summary": "After a 5-year career break, Priya returned to the workforce and founded a successful tech startup.",
                "challenges": ["Career break", "Lack of recent experience", "Balancing family and business"],
                "strategies": ["Upskilling through online courses", "Networking with industry professionals", "Setting clear boundaries between work and family"],
                "quote": "JobsForHer's mentorship program gave me the confidence to start my own business. My mentor helped me navigate the challenges of returning to work after a break."
            },
            {
                "id": "2",
                "name": "Anita Patel",
                "title": "Breaking the Glass Ceiling in Finance",
                "industry": "Finance",
                "summary": "Anita became the first woman CFO at a major financial institution after overcoming gender bias and workplace challenges.",
                "challenges": ["Gender bias", "Work-life balance", "Lack of female role models"],
                "strategies": ["Building a strong support network", "Developing leadership skills", "Finding mentors who championed her career"],
                "quote": "The leadership development program at JobsForHer helped me develop the skills and confidence needed to take on senior leadership roles."
            },
            {
                "id": "3",
                "name": "Meera Reddy",
                "title": "Pivoting Careers in Mid-Life",
                "industry": "Healthcare",
                "summary": "Meera successfully transitioned from a career in marketing to healthcare administration at the age of 45.",
                "challenges": ["Age bias", "Lack of industry experience", "Financial constraints during transition"],
                "strategies": ["Volunteering to gain experience", "Taking certification courses", "Leveraging transferable skills"],
                "quote": "The career counseling services at JobsForHer helped me identify my transferable skills and find opportunities in a new industry."
            }
        ]
    
    def load_career_paths(self):
        # Define career paths programmatically
        self.career_paths = [
            {
                "id": "1",
                "title": "Technology Leadership",
                "description": "Career path for women aspiring to leadership roles in technology",
                "entry_level": ["Software Engineer", "Data Analyst", "Product Manager"],
                "mid_level": ["Senior Software Engineer", "Technical Lead", "Product Director"],
                "senior_level": ["CTO", "VP of Engineering", "Chief Product Officer"],
                "skills": ["Programming", "System Design", "Team Leadership", "Strategic Planning"],
                "certifications": ["AWS Certified Solutions Architect", "Google Cloud Professional", "PMP"],
                "resources": ["Women in Tech Leadership Program", "Tech Leadership Mentorship", "Coding Bootcamps"]
            },
            {
                "id": "2",
                "title": "Finance and Investment",
                "description": "Career path for women in finance, banking, and investment",
                "entry_level": ["Financial Analyst", "Investment Banking Analyst", "Accountant"],
                "mid_level": ["Senior Financial Analyst", "Portfolio Manager", "Financial Controller"],
                "senior_level": ["CFO", "Investment Director", "Managing Director"],
                "skills": ["Financial Modeling", "Risk Management", "Investment Analysis", "Strategic Planning"],
                "certifications": ["CFA", "CPA", "FRM"],
                "resources": ["Women in Finance Network", "Investment Management Mentorship", "Financial Modeling Courses"]
            },
            {
                "id": "3",
                "title": "Healthcare Administration",
                "description": "Career path for women in healthcare management and administration",
                "entry_level": ["Healthcare Administrator", "Medical Office Manager", "Health Information Specialist"],
                "mid_level": ["Department Manager", "Clinical Director", "Healthcare Consultant"],
                "senior_level": ["Hospital CEO", "Healthcare System Director", "Healthcare Policy Advisor"],
                "skills": ["Healthcare Operations", "Regulatory Compliance", "Patient Care Management", "Strategic Planning"],
                "certifications": ["FACHE", "CPHRM", "MHA"],
                "resources": ["Healthcare Leadership Program", "Administrative Mentorship", "Healthcare Management Courses"]
            }
        ]
    
    def load_skills_data(self):
        # Define skills data programmatically
        self.skills_data = [
            {
                "category": "Technical Skills",
                "skills": [
                    {"name": "Python", "demand": "High", "resources": ["Python for Beginners", "Data Science with Python"]},
                    {"name": "Data Analysis", "demand": "High", "resources": ["Data Science Fundamentals", "Advanced Analytics"]},
                    {"name": "Project Management", "demand": "High", "resources": ["PMP Certification", "Agile Methodologies"]},
                    {"name": "Digital Marketing", "demand": "Medium", "resources": ["SEO Fundamentals", "Social Media Marketing"]},
                    {"name": "Cloud Computing", "demand": "High", "resources": ["AWS Certified", "Cloud Architecture"]}
                ]
            },
            {
                "category": "Soft Skills",
                "skills": [
                    {"name": "Leadership", "demand": "High", "resources": ["Leadership Development Program", "Team Management"]},
                    {"name": "Communication", "demand": "High", "resources": ["Public Speaking", "Business Writing"]},
                    {"name": "Negotiation", "demand": "High", "resources": ["Salary Negotiation", "Conflict Resolution"]},
                    {"name": "Problem Solving", "demand": "High", "resources": ["Critical Thinking", "Decision Making"]},
                    {"name": "Time Management", "demand": "Medium", "resources": ["Productivity Techniques", "Work-Life Balance"]}
                ]
            },
            {
                "category": "Industry-Specific Skills",
                "skills": [
                    {"name": "Healthcare Administration", "demand": "Medium", "resources": ["Healthcare Management", "Medical Records"]},
                    {"name": "Financial Analysis", "demand": "High", "resources": ["Financial Modeling", "Investment Analysis"]},
                    {"name": "Human Resources", "demand": "Medium", "resources": ["HR Management", "Talent Acquisition"]},
                    {"name": "Education Technology", "demand": "Medium", "resources": ["EdTech Fundamentals", "Learning Management Systems"]},
                    {"name": "Environmental Sustainability", "demand": "Growing", "resources": ["Sustainability Management", "Green Business"]}
                ]
            }
        ]
    
    def get_job_listings(self, filters: Dict = None) -> List[Dict]:
        if filters:
            return [job for job in self.job_listings if all(job.get(k) == v for k, v in filters.items())]
        return self.job_listings
    
    def get_events(self, filters: Dict = None) -> List[Dict]:
        if filters:
            return [event for event in self.events if all(event.get(k) == v for k, v in filters.items())]
        return self.events
    
    def get_mentorship_opportunities(self, filters: Dict = None) -> List[Dict]:
        if filters:
            return [opp for opp in self.mentorship_opportunities if all(opp.get(k) == v for k, v in filters.items())]
        return self.mentorship_opportunities
    
    def get_faqs(self, category: str = None) -> List[Dict]:
        if category and category in self.faqs:
            return self.faqs[category]
        return [faq for category in self.faqs.values() for faq in category]
    
    def get_resources(self, category: str = None) -> List[Dict]:
        if category and category in self.resources:
            return self.resources[category]
        return [resource for category in self.resources.values() for resource in category]
    
    def get_success_stories(self, industry: str = None) -> List[Dict]:
        if industry:
            return [story for story in self.success_stories if story.get('industry') == industry]
        return self.success_stories
    
    def get_career_paths(self) -> List[Dict]:
        return self.career_paths
    
    def get_skills_data(self, category: str = None) -> List[Dict]:
        if category:
            return [skill_data for skill_data in self.skills_data if skill_data.get('category') == category]
        return self.skills_data
    
    def search_faqs(self, query: str) -> List[Dict]:
        query = query.lower()
        results = []
        
        for category, faqs in self.faqs.items():
            for faq in faqs:
                if query in faq["question"].lower() or query in faq["answer"].lower():
                    results.append(faq)
        
        return results
    
    def semantic_search(self, query: str, data_type: str) -> List[Dict]:
        """
        Perform semantic search on different data types.
        This is a simplified implementation - in a real system, you would use
        embeddings and vector similarity search.
        """
        query = query.lower()
        results = []
        
        if data_type == "jobs":
            for job in self.job_listings:
                # Check if query terms appear in job title, description, or requirements
                if (query in job.get('title', '').lower() or 
                    query in job.get('description', '').lower() or 
                    query in job.get('requirements', '').lower()):
                    results.append(job)
        
        elif data_type == "events":
            for event in self.events:
                # Check if query terms appear in event title, description, or topics
                if (query in event.get('title', '').lower() or 
                    query in event.get('description', '').lower() or 
                    any(query in topic.lower() for topic in event.get('topics', []))):
                    results.append(event)
        
        elif data_type == "mentorship":
            for mentor in self.mentorship_opportunities:
                # Check if query terms appear in mentor name, expertise, or description
                if (query in mentor.get('mentor_name', '').lower() or 
                    query in mentor.get('description', '').lower() or 
                    any(query in expertise.lower() for expertise in mentor.get('expertise', []))):
                    results.append(mentor)
        
        elif data_type == "success_stories":
            for story in self.success_stories:
                # Check if query terms appear in story title, summary, or challenges
                if (query in story.get('title', '').lower() or 
                    query in story.get('summary', '').lower() or 
                    any(query in challenge.lower() for challenge in story.get('challenges', []))):
                    results.append(story)
        
        return results

class BiasDetector:
    @staticmethod
    def check_bias(text: str) -> Dict:
        bias_found = {}
        text_lower = text.lower()
        
        # Ignore bias check for program names and legitimate uses
        if any(term in text_lower for term in ['divhersity', 'hershakti', 'jobsforher']):
            return bias_found
            
        for category, keywords in BIAS_KEYWORDS.items():
            found_keywords = []
            for kw in keywords:
                # Check for standalone words to avoid false positives in compound words
                if f" {kw} " in f" {text_lower} ":
                    found_keywords.append(kw)
            if found_keywords:
                bias_found[category] = found_keywords
        
        return bias_found
    
    @staticmethod
    def get_inclusive_response(bias_type: str) -> str:
        responses = {
            'gender': "I aim to provide gender-neutral information. Let me help you with that.",
            'age': "I focus on skills and qualifications rather than age. Let me help you find relevant opportunities.",
            'ethnicity': "I provide equal opportunities for all backgrounds. Let me assist you with that."
        }
        return responses.get(bias_type, "I'll help you find the most relevant information.")

class SentimentAnalyzer:
    @staticmethod
    def analyze_sentiment(text: str) -> str:
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'happy', 'love', 'like', 'enjoy', 'helpful']
        negative_words = ['bad', 'terrible', 'awful', 'horrible', 'sad', 'hate', 'dislike', 'annoying', 'useless', 'difficult']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    @staticmethod
    def get_sentiment_response(sentiment: str) -> str:
        responses = {
            'positive': "I'm glad you're having a positive experience! How else can I help you today?",
            'negative': "I'm sorry to hear that. Let me try to help you better. What specific issue are you facing?",
            'neutral': "I'm here to help. What would you like to know more about?"
        }
        return responses.get(sentiment, "How can I assist you today?")

class HinglishProcessor:
    """Handles Hinglish (Hindi-English mixed) language processing"""
    
    # Common Hinglish variations and their English equivalents
    HINGLISH_MAPPINGS = {
        'kaam': 'job',
        'naukri': 'job',
        'paisa': 'salary',
        'paise': 'money',
        'siksha': 'education',
        'padhai': 'study',
        'kaam karna': 'work',
        'interview dena': 'give interview',
        'apply karna': 'apply',
        'form bharna': 'fill form',
        'resume banana': 'create resume',
        'career banana': 'build career',
        'guidance chahiye': 'need guidance',
        'help chahiye': 'need help',
        'samajh nahi aa raha': "don't understand",
        'kya karu': 'what to do',
        'kaise karu': 'how to do',
        'kitna time': 'how much time',
        'kitna paisa': 'how much money',
        'kahan pe': 'where',
        'kab tak': 'until when',
        'acha': 'good',
        'theek hai': 'okay',
        'haan': 'yes',
        'nahi': 'no'
    }
    
    # Common Hinglish sentence patterns
    SENTENCE_PATTERNS = {
        'job_search': [
            r'.*job.*chahiye.*',
            r'.*naukri.*dhund.*',
            r'.*kaam.*mil.*',
            r'.*apply.*karna.*',
            r'.*vacancy.*hai.*'
        ],
        'career_guidance': [
            r'.*career.*advice.*',
            r'.*guidance.*chahiye.*',
            r'.*help.*karo.*',
            r'.*samajh.*nahi.*',
            r'.*kya.*karu.*'
        ],
        'education': [
            r'.*padhai.*karna.*',
            r'.*course.*join.*',
            r'.*siksha.*ke.*bare.*',
            r'.*study.*kaise.*',
            r'.*college.*admission.*'
        ],
        'salary': [
            r'.*salary.*kitni.*',
            r'.*paisa.*milega.*',
            r'.*package.*kya.*',
            r'.*paise.*kitne.*',
            r'.*income.*kya.*'
        ]
    }
    
    @staticmethod
    def translate_to_english(text: str) -> Tuple[str, Dict[str, str]]:
        """
        Translates Hinglish text to English while preserving context and intent.
        
        Args:
            text (str): Input Hinglish text
            
        Returns:
            Tuple[str, Dict[str, str]]: Translated English text and translation mapping
        """
        if not text:
            return "", {}
        
        translations = {}
        words = text.lower().split()
        translated_words = []
        
        # First pass: Direct word mappings
        for word in words:
            if word in HinglishProcessor.HINGLISH_MAPPINGS:
                translated = HinglishProcessor.HINGLISH_MAPPINGS[word]
                translations[word] = translated
                translated_words.append(translated)
            else:
                translated_words.append(word)
        
        translated_text = ' '.join(translated_words)
        
        # Second pass: Pattern matching for context
        for category, patterns in HinglishProcessor.SENTENCE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    translations['_context'] = category
                    break
        
        return translated_text, translations
    
    @staticmethod
    def detect_hinglish(text: str) -> bool:
        """
        Detects if the input text contains Hinglish content.
        
        Args:
            text (str): Input text to analyze
            
        Returns:
            bool: True if Hinglish content is detected, False otherwise
        """
        if not text:
            return False
        
        # Check for Hinglish words
        words = text.lower().split()
        for word in words:
            if word in HinglishProcessor.HINGLISH_MAPPINGS:
                return True
        
        # Check for Hinglish patterns
        for patterns in HinglishProcessor.SENTENCE_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return True
        
        return False
    
    @staticmethod
    def get_context(text: str) -> Optional[str]:
        """
        Extracts the context/category of the Hinglish text.
        
        Args:
            text (str): Input Hinglish text
            
        Returns:
            Optional[str]: Context category if detected, None otherwise
        """
        if not text:
            return None
        
        # Check patterns for context
        for category, patterns in HinglishProcessor.SENTENCE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return category
        
        return None
    
    @staticmethod
    def get_translation_confidence(text: str) -> float:
        """
        Calculates confidence score for Hinglish translation.
        
        Args:
            text (str): Input Hinglish text
            
        Returns:
            float: Confidence score between 0 and 1
        """
        if not text:
            return 0.0
        
        words = text.lower().split()
        matched_words = 0
        
        # Count matched words
        for word in words:
            if word in HinglishProcessor.HINGLISH_MAPPINGS:
                matched_words += 1
        
        # Calculate basic confidence
        confidence = matched_words / len(words) if words else 0.0
        
        # Boost confidence if patterns are matched
        for patterns in HinglishProcessor.SENTENCE_PATTERNS.values():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    confidence = min(1.0, confidence + 0.2)
                    break
        
        return confidence

class NaturalLanguageProcessor:
    """Advanced natural language processing with error detection and correction."""
    
    # Common word variations and misspellings
    COMMON_VARIATIONS = {
        'job': ['jab', 'jobb', 'jop', 'jov'],
        'career': ['carrier', 'carreer', 'carear'],
        'interview': ['intervew', 'interviw', 'intrview'],
        'salary': ['salery', 'sallary', 'salry'],
        'experience': ['expirience', 'experiance', 'expirence'],
        'skill': ['skil', 'sklil', 'skils'],
        'training': ['trainning', 'traning', 'trainig'],
        'education': ['eduction', 'educaton', 'educashun'],
        'degree': ['deegree', 'degre', 'deegre'],
        'certificate': ['certificat', 'certifcate', 'certifcat'],
        'course': ['corse', 'coarse', 'cours']
    }
    
    # Grammar patterns for incomplete sentences
    INCOMPLETE_PATTERNS = {
        'job_search': [
            r'job.*for',
            r'looking.*job',
            r'want.*work',
            r'need.*job',
            r'find.*job'
        ],
        'career_help': [
            r'help.*career',
            r'guidance.*needed',
            r'advice.*career',
            r'career.*path',
            r'future.*plan'
        ],
        'education': [
            r'course.*for',
            r'study.*options',
            r'education.*help',
            r'learn.*skills',
            r'training.*needed'
        ],
        'mentorship': [
            r'mentor.*needed',
            r'guide.*wanted',
            r'help.*mentor',
            r'find.*mentor',
            r'mentorship.*program'
        ]
    }
    
    # Common grammar mistakes and corrections
    GRAMMAR_CORRECTIONS = {
        'i': 'I',
        'im': 'I am',
        'ur': 'your',
        'u': 'you',
        'thx': 'thanks',
        'plz': 'please',
        'thru': 'through',
        'tho': 'though',
        'wanna': 'want to',
        'gonna': 'going to',
        'gotta': 'got to',
        'kinda': 'kind of',
        'sorta': 'sort of',
        'lemme': 'let me',
        'gimme': 'give me',
        'dunno': "don't know",
        'aint': "isn't",
        'wont': "won't",
        'cant': "can't",
        'dont': "don't"
    }
    
    def __init__(self):
        self.spell_checker = SpellChecker()
        self.lemmatizer = WordNetLemmatizer()
        self.stop_words = set(stopwords.words('english'))
        self.context_weights = {
            'job_search': 0.8,
            'career_help': 0.7,
            'education': 0.6,
            'mentorship': 0.5
        }
    
    @staticmethod
    def fuzzy_match(word: str, word_set: Set[str], threshold: float = 0.7) -> Optional[str]:
        """Enhanced fuzzy matching with context awareness."""
        if not word or not word_set:
            return None
            
        # Check exact match first
        if word in word_set:
            return word
            
        # Check common variations
        for correct_word, variations in NaturalLanguageProcessor.COMMON_VARIATIONS.items():
            if word in variations:
                return correct_word
                
        # Use difflib for fuzzy matching
        matches = get_close_matches(word, word_set, n=1, cutoff=threshold)
        return matches[0] if matches else None
    
    @staticmethod
    def normalize_text(text: str) -> str:
        """Enhanced text normalization with grammar correction."""
        if not text:
            return ""
            
        # Convert to lowercase
        text = text.lower()
        
        # Fix common grammar mistakes
        for mistake, correction in NaturalLanguageProcessor.GRAMMAR_CORRECTIONS.items():
            text = re.sub(r'\b' + mistake + r'\b', correction, text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text
    
    @staticmethod
    def correct_spelling(text: str) -> Tuple[str, Dict[str, str]]:
        """Enhanced spelling correction with context awareness."""
        corrections = {}
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Skip if word is a number or special character
            if word.isdigit() or not word.isalnum():
                corrected_words.append(word)
                continue
                
            # Check common variations first
            corrected = NaturalLanguageProcessor.fuzzy_match(
                word,
                set(NaturalLanguageProcessor.COMMON_VARIATIONS.keys())
            )
            
            if corrected:
                corrections[word] = corrected
                corrected_words.append(corrected)
                continue
                
            # Use spell checker as fallback
            correction = NaturalLanguageProcessor.spell_checker.correction(word)
            if correction and correction != word:
                corrections[word] = correction
                corrected_words.append(correction)
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words), corrections
    
    @staticmethod
    def detect_intent(text: str) -> Tuple[str, Optional[Dict[str, str]]]:
        """Enhanced intent detection with error tolerance."""
        # Normalize and correct text
        normalized_text = NaturalLanguageProcessor.normalize_text(text)
        corrected_text, spelling_corrections = NaturalLanguageProcessor.correct_spelling(normalized_text)
        
        # Check for incomplete sentences
        for intent, patterns in NaturalLanguageProcessor.INCOMPLETE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, corrected_text, re.IGNORECASE):
                    return intent, {
                        'original_text': text,
                        'corrected_text': corrected_text,
                        'spelling_corrections': spelling_corrections,
                        'confidence': 0.8
                    }
        
        # Extract entities with error tolerance
        entities = NaturalLanguageProcessor.extract_entities(corrected_text)
        
        # Determine intent based on entities and context
        intent = NaturalLanguageProcessor._determine_intent(corrected_text, entities)
        
        return intent, {
            'original_text': text,
            'corrected_text': corrected_text,
            'spelling_corrections': spelling_corrections,
            'entities': entities,
            'confidence': NaturalLanguageProcessor._calculate_confidence(corrected_text, intent)
        }
    
    @staticmethod
    def _determine_intent(text: str, entities: Dict[str, List[str]]) -> str:
        """Determine intent with context awareness."""
        # Check for job-related terms
        job_terms = {'job', 'career', 'work', 'employment', 'position'}
        if any(term in text.lower() for term in job_terms):
            return 'job_search'
            
        # Check for education-related terms
        edu_terms = {'study', 'learn', 'course', 'education', 'training'}
        if any(term in text.lower() for term in edu_terms):
            return 'education'
            
        # Check for mentorship-related terms
        mentor_terms = {'mentor', 'guide', 'advice', 'help', 'support'}
        if any(term in text.lower() for term in mentor_terms):
            return 'mentorship'
            
        # Default to career help
        return 'career_help'
    
    @staticmethod
    def _calculate_confidence(text: str, intent: str) -> float:
        """Calculate confidence score based on text and intent."""
        # Base confidence
        confidence = 0.5
        
        # Increase confidence based on keyword presence
        for term in NaturalLanguageProcessor.COMMON_VARIATIONS.keys():
            if term in text.lower():
                confidence += 0.1
                
        # Adjust based on intent-specific factors
        if intent in NaturalLanguageProcessor.context_weights:
            confidence *= NaturalLanguageProcessor.context_weights[intent]
            
        return min(confidence, 1.0)
    
    @staticmethod
    def extract_entities(text: str) -> Dict[str, List[str]]:
        """Enhanced entity extraction with error tolerance."""
        entities = {
            'skills': [],
            'industries': [],
            'locations': [],
            'education_levels': [],
            'experience_levels': []
        }
        
        # Normalize text
        text = NaturalLanguageProcessor.normalize_text(text)
        
        # Extract skills with fuzzy matching
        skills = NaturalLanguageProcessor._extract_skills(text)
        entities['skills'].extend(skills)
        
        # Extract industries with fuzzy matching
        industries = NaturalLanguageProcessor._extract_industries(text)
        entities['industries'].extend(industries)
        
        # Extract locations
        locations = NaturalLanguageProcessor._extract_locations(text)
        entities['locations'].extend(locations)
        
        # Extract education levels
        education_levels = NaturalLanguageProcessor._extract_education_levels(text)
        entities['education_levels'].extend(education_levels)
        
        # Extract experience levels
        experience_levels = NaturalLanguageProcessor._extract_experience_levels(text)
        entities['experience_levels'].extend(experience_levels)
        
        return entities
    
    @staticmethod
    def _extract_skills(text: str) -> List[str]:
        """Extract skills with fuzzy matching."""
        skills = []
        # Implementation would use a skills database and fuzzy matching
        return skills
    
    @staticmethod
    def _extract_industries(text: str) -> List[str]:
        """Extract industries with fuzzy matching."""
        industries = []
        # Implementation would use an industries database and fuzzy matching
        return industries
    
    @staticmethod
    def _extract_locations(text: str) -> List[str]:
        """Extract locations with fuzzy matching."""
        locations = []
        # Implementation would use a locations database and fuzzy matching
        return locations
    
    @staticmethod
    def _extract_education_levels(text: str) -> List[str]:
        """Extract education levels with fuzzy matching."""
        education_levels = []
        # Implementation would use education levels database and fuzzy matching
        return education_levels
    
    @staticmethod
    def _extract_experience_levels(text: str) -> List[str]:
        """Extract experience levels with fuzzy matching."""
        experience_levels = []
        # Implementation would use experience levels database and fuzzy matching
        return experience_levels

class AuditLogEntry:
    """Class for managing audit log entries."""
    
    def __init__(self, action: str, user_id: str, timestamp: datetime.datetime, details: Dict[str, Any]):
        self.action = action
        self.user_id = user_id
        self.timestamp = timestamp
        self.details = details
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the audit log entry to a dictionary."""
        return {
            'action': self.action,
            'user_id': self.user_id,
            'timestamp': self.timestamp.isoformat(),
            'details': self.details
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditLogEntry':
        """Create an audit log entry from a dictionary."""
        return cls(
            action=data['action'],
            user_id=data['user_id'],
            timestamp=datetime.datetime.fromisoformat(data['timestamp']),
            details=data['details']
        )

def handle_signup():
    """Handle user registration process."""
    print(f"\n{CHATBOT_NAME}: Let's create your account! I'll guide you through the process step by step.")
    
    while True:
        email = input("Email: ").strip()
        if '@' in email and '.' in email:
            break
        print("Please enter a valid email address.")
    
    while True:
        name = input("Name: ").strip()
        if name:
            break
        print("Please enter your name.")
    
    while True:
        interests = input("Interests (comma-separated): ").strip()
        if interests:
            break
        print("Please enter at least one interest.")
    
    interests_list = [interest.strip() for interest in interests.split(',')]
    print(f"\n{CHATBOT_NAME}: Account created successfully for {name}!")
    print(f"Email: {email}")
    print(f"Interests: {', '.join(interests_list)}")
    print("\nYou can now access all our features including:")
    print("- Job listings and applications")
    print("- Event registration")
    print("- Session booking")
    print("- Mentorship program")

def handle_profile_update():
    """Handle profile update process."""
    print(f"\n{CHATBOT_NAME}: Let's update your profile! I'll help you update your information.")
    
    while True:
        name = input("Name: ").strip()
        if name:
            break
        print("Please enter your name.")
    
    while True:
        email = input("Email: ").strip()
        if '@' in email and '.' in email:
            break
        print("Please enter a valid email address.")
    
    while True:
        interests = input("Interests (comma-separated): ").strip()
        if interests:
            break
        print("Please enter at least one interest.")
    
    interests_list = [interest.strip() for interest in interests.split(',')]
    print(f"\n{CHATBOT_NAME}: Profile updated successfully!")
    print(f"Name: {name}")
    print(f"Email: {email}")
    print(f"Interests: {', '.join(interests_list)}")
    print("\nYour profile is now up to date!")

def main():
    asha = AshaAI()
    print(f"Hola!! It's {CHATBOT_NAME} {CHATBOT_TITLE} 😉")
    print("I'm here to help you with:")
    print("1. Product Discovery - Explore jobs, events, sessions, and mentorship")
    print("2. User Signup - Create your account")
    print("3. FAQs - Get answers to common questions")
    print("4. Profile Updates - Keep your information current")
    print("\nType 'quit' or 'exit' to end our conversation.")
    
    session_id = None
    
    while True:
        user_input = input("\nYou: ").strip()
        
        if user_input.lower() in ['quit', 'exit']:
            print(f"{CHATBOT_NAME}: Goodbye! Have a great day!")
            break
        
        if not user_input:
            continue
        
        response = asha.process_message(user_input, session_id)
        print(f"\n{CHATBOT_NAME}: {response['text']}")
        
        if response['action'] == "signup":
            handle_signup()
        elif response['action'] == "profile":
            handle_profile_update()

if __name__ == "__main__":
    main() 