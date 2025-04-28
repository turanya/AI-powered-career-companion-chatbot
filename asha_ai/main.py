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
        load_dotenv()
        self.context = ConversationContext()
        self.security = SecurityManager()
        self.knowledge_base = KnowledgeBase()
        self.current_menu = 'main'
        self.load_session_data()
        
    def load_session_data(self):
        """Load all data files"""
        with open('data/session_details.json', 'r') as f:
            self.session_data = json.load(f)
            
        with open('data/hershakti_courses.json', 'r') as f:
            self.course_data = json.load(f)
            
        with open('data/job_listings.json', 'r') as f:
            self.job_data = json.load(f)
            
        with open('data/professional_development.json', 'r') as f:
            self.pd_data = json.load(f)
            
    def get_main_menu(self) -> str:
        """Return the main menu options"""
        self.current_menu = 'main'
        menu = "Welcome to JobsForHer Foundation! 🌟\n\nHow can I assist you today?\n"
        for option in self.session_data['main_options']:
            menu += f"{option['id']}. {option['title']} - {option['description']}\n"
        menu += "\nPlease enter the number of your choice (1-5):"
        return menu
        
    def get_hershakti_menu(self) -> str:
        """Return herShakti program options"""
        menu = "herShakti Program - Upskilling in Emerging Technologies 💻\n\nAvailable Courses:\n"
        for course in self.session_data['hershakti_courses']:
            menu += f"{course['id']}. {course['title']} ({course['duration']}, {course['level']})\n - {course['description']}\n"
        menu += "\nEnter course ID (e.g., 'hs001') or 'back' to return to main menu:"
        return menu
        
    def get_divhersity_menu(self) -> str:
        """Return DivHERsity club information"""
        return """DivHERsity Club - Exclusive Community for DEI Leaders 🤝

Membership Options:
1. Individual Membership
2. Corporate Membership
3. View Upcoming Events
4. Request Information

Enter your choice (1-4) or 'back' to return:"""
        
    def get_career_menu(self) -> str:
        """Return career development options"""
        menu = "Career Development Resources 🎯\n\nAvailable Services:\n"
        for resource in self.session_data['career_resources']:
            menu += f"{resource['id']}. {resource['title']} ({resource['format']}, {resource['duration']})\n"
        menu += "\nEnter resource ID (e.g., 'cr001') or 'back' to return:"
        return menu
        
    def get_entrepreneurship_menu(self) -> str:
        """Return entrepreneurship support options"""
        return """Entrepreneurship Support Programs 🚀

1. Startup Saturday Workshops
2. NIPP Blockchain Challenge
3. Mentorship Program
4. Funding Resources

Enter your choice (1-4) or 'back' to return:"""
        
    def get_about_menu(self) -> str:
        """Return about us information"""
        return """About JobsForHer Foundation ℹ️

1. Our Vision and Mission
2. Team
3. Contact Information
4. Impact Stories

Enter your choice (1-4) or 'back' to return:"""
        
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
        
        # Store current input for context
        self.last_input = user_input.lower().strip()
        
        # Store last topic for context
        if hasattr(self, 'last_topic') and self.last_input in ['yes', 'y']:
            return self._handle_yes_response(response_id)
        
        # Clear last topic if user starts new query
        if self.last_input not in ['yes', 'y', 'no', 'n']:
            self.last_topic = None
        
        try:
            # Handle menu navigation
            if user_input.lower() in ['main menu', 'back', 'home']:
                self.current_menu = 'main'
                return {"text": self.get_main_menu(), "response_id": response_id}
                
            # Handle numeric menu selections
            if user_input.isdigit():
                choice = int(user_input)
                if self.current_menu == 'main':
                    if 1 <= choice <= len(self.session_data['main_options']):
                        menu_option = self.session_data['main_options'][choice - 1]
                        self.current_menu = menu_option['id']
                        if menu_option['id'] == 'jobs':
                            return self._handle_job_query(user_input)
                        elif menu_option['id'] == 'development':
                            return self._handle_pd_query(user_input)
                        elif menu_option['id'] == 'mentorship':
                            return self._handle_mentorship_query(user_input)
                        elif menu_option['id'] == 'events':
                            return self._handle_event_query(user_input)
                elif self.current_menu == 'jobs':
                    return self._handle_job_menu_choice(choice, response_id)
                elif self.current_menu == 'development':
                    return self._handle_development_menu_choice(choice, response_id)
                elif self.current_menu == 'mentorship':
                    return self._handle_mentorship_menu_choice(choice, response_id)
                elif self.current_menu == 'events':
                    return self._handle_event_menu_choice(choice, response_id)
            
            # Handle text-based queries
            if any(word in self.last_input for word in ['job', 'career', 'work', 'position']):
                self.last_topic = 'jobs'
                return self._handle_job_query(user_input)
            elif any(word in self.last_input for word in ['develop', 'learn', 'skill', 'training', 'workshop', 'professional']):
                self.last_topic = 'development'
                return self._handle_pd_query(user_input)
            elif any(word in self.last_input for word in ['mentor', 'guide', 'advice']):
                self.last_topic = 'mentorship'
                return self._handle_mentorship_query(user_input)
            elif any(word in self.last_input for word in ['event', 'webinar', 'conference']):
                self.last_topic = 'events'
                return self._handle_event_query(user_input)
                
            # Default response
            return {
                "text": "I'm here to help you with:\n1. Job Search & Career Opportunities\n2. Professional Development\n3. Mentorship Programs\n4. Upcoming Events\n\nWhat would you like to explore?",
                "response_id": response_id
            }
            
        except Exception as e:
            self.error_handler.report_error(f"Error processing message: {str(e)}")
            return {
                "text": "I apologize, but I encountered an error. Please try again or select from the main menu options.",
                "response_id": response_id
            }
                    
                    response += "\nCareer Opportunities:\n"
                    for career in course['career_paths']:
                        response += f"💼 {career}\n"
                    
                    response += "\nWhat would you like to do?\n"
                    response += "1. View detailed syllabus\n"
                    response += "2. Register for this course\n"
                    response += "3. Schedule a consultation\n"
                    response += "4. Download course brochure\n"
                    response += "5. Go back to course list"
                    
                    return {"text": response, "response_id": response_id}
                    
            elif user_input.isdigit():
                choice = int(user_input)
                if 1 <= choice <= 5:
                    responses = {
                        1: self._format_syllabus(self.current_course) if hasattr(self, 'current_course') else "Please select a course first.",
                        2: "Great! Please provide your details to register:\n1. Full Name\n2. Email\n3. Phone\n4. Current Professional Status",
                        3: "When would you like to schedule your consultation?\n1. Tomorrow\n2. This week\n3. Next week\n\nOur career counselor will help you choose the right path.",
                        4: "📥 Downloading course brochure...\n\nYou'll receive the detailed course information in your email shortly.",
                        5: self.get_hershakti_menu()
                    }
                    return {"text": responses[choice], "response_id": response_id}
        
        elif self.current_menu == 'divhersity' and user_input.isdigit():
            choice = int(user_input)
            if 1 <= choice <= 4:
                responses = {
                    1: "Individual membership includes:\n- Access to exclusive events\n- Networking opportunities\n- Resource library\n- Monthly mentorship sessions\n\nWould you like to apply for membership?",
                    2: "Corporate membership benefits:\n- Multiple user accounts\n- Custom DEI workshops\n- Recruitment support\n- Analytics dashboard\n\nWould you like to schedule a consultation?",
                    3: f"Upcoming DivHERsity events:\n\n{self._format_events(self.session_data['events'])}",
                    4: "Please provide your contact details and areas of interest. Our team will reach out within 24 hours."
                }
                return {"text": responses[choice], "response_id": response_id}
        
        elif self.current_menu == 'career':
            if user_input in [resource['id'] for resource in self.session_data['career_resources']]:
                resource = next(r for r in self.session_data['career_resources'] if r['id'] == user_input)
                return {
                    "text": f"Selected: {resource['title']}\n\n"
                            f"Format: {resource['format']}\n"
                            f"Duration: {resource['duration']}\n\n"
                            f"Would you like to:\n"
                            f"1. Schedule a session\n"
                            f"2. View more details\n"
                            f"3. Go back to resources",
                    "response_id": response_id
                }
        
        elif self.current_menu == 'entrepreneurship' and user_input.isdigit():
            choice = int(user_input)
            if 1 <= choice <= 4:
                responses = {
                    1: "Startup Saturday Workshops:\n- Monthly entrepreneurship workshops\n- Expert speakers\n- Networking opportunities\n- Pitch practice\n\nNext workshop date: May 15, 2025",
                    2: "NIPP Blockchain Challenge:\n- Innovation competition\n- Mentorship support\n- Funding opportunities\n- Technical resources\n\nRegistrations open until June 1, 2025",
                    3: "Entrepreneurship Mentoring:\n- 4-month program\n- Weekly mentoring sessions\n- Business plan development\n- Market research support\n\nNext cohort starts July 1, 2025",
                    4: "Funding Resources:\n- Government schemes\n- Angel investors\n- Venture capital\n- Crowdfunding platforms\n\nWould you like to schedule a consultation?"
                }
                return {"text": responses[choice], "response_id": response_id}
        
        elif self.current_menu == 'about' and user_input.isdigit():
            choice = int(user_input)
            if 1 <= choice <= 4:
                responses = {
                    1: "Our Vision:\nEnhancing the status of women in the workplace and beyond.\n\nOur Mission:\n- Promote gender equality\n- Enable career advancement\n- Foster skill development\n- Facilitate networking\n- Support entrepreneurship",
                    2: "Our Team:\n\nNeha Bagaria - Managing Trustee\n- Founder & CEO of HerKey\n- Wharton graduate\n- Featured in Forbes India's WPower Trailblazers\n\nAshok Pamidi - Project Head, herShakti\n- 30-year industry veteran\n- Former CEO of NASSCOM Foundation",
                    3: "Contact Information:\n\nAddress: 11 Kemwell House, Tumkur Road\nBengaluru – 560022\n\nPhone: +91 81473 78390\nWebsite: jobsforherfoundation.org",
                    4: "Impact Stories:\n- 10,000+ women upskilled\n- 500+ successful career transitions\n- 200+ entrepreneurs supported\n- 50+ corporate partnerships\n- Pan-India presence"
                }
                return {"text": responses[choice], "response_id": response_id}

        
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
        # Handle job-related queries
        if any(word in user_input.lower() for word in ['job', 'career', 'work', 'position', 'opportunity']):
            return self._handle_job_query(user_input)
            
        # Handle professional development queries
        elif any(word in user_input.lower() for word in ['develop', 'learn', 'skill', 'training', 'workshop']):
            return self._handle_pd_query(user_input)
            
        # Handle mentorship queries
        elif any(word in user_input.lower() for word in ['mentor', 'guide', 'advice', 'coach']):
            return self._handle_mentorship_query(user_input)
            
        # Handle event queries
        elif any(word in user_input.lower() for word in ['event', 'webinar', 'conference', 'meetup']):
            return self._handle_event_query(user_input)
            
        return {
            "text": "I'm here to help you with:
1. Job Search & Career Opportunities
2. Professional Development Programs
3. Mentorship Connections
4. Upcoming Events & Workshops

What would you like to explore?",
            "data": {}
        }
        
    def _handle_main_menu_choice(self, choice: int, response_id: str) -> Dict:
        """Handle main menu selections"""
        menu_actions = {
            1: ('jobs', self._handle_job_query),
            2: ('development', self._handle_pd_query),
            3: ('mentorship', self._handle_mentorship_query),
            4: ('events', self._handle_event_query)
        }
        
        if choice in menu_actions:
            self.current_menu = menu_actions[choice][0]
            return menu_actions[choice][1](self.last_input)
        
        return {"text": "Please select a valid option (1-4)", "response_id": response_id}
        
    def _handle_job_query(self, query: str) -> Dict:
        """Handle job-related queries"""
        self.current_menu = 'jobs'
        jobs = self.job_data['jobs']
        response = "📋 Here are some exciting opportunities:\n\n"
        
        for job in jobs[:3]:  # Show top 3 jobs
            response += f"🔹 {job['title']} at {job['company']}\n"
            response += f"   📍 {job['location']}\n"
            response += f"   💼 {job['experience']} experience\n"
            response += f"   💰 {job['salary_range']}\n"
            response += f"   ✨ Benefits: {', '.join(job['women_friendly_benefits'][:2])}\n\n"
            
        response += "\nWhat would you like to do?\n"
        response += "1. View more job details\n"
        response += "2. Filter by location\n"
        response += "3. Filter by experience\n"
        response += "4. Get application tips\n"
        response += "5. Schedule career counseling"
        
        return {"text": response, "data": {"jobs": jobs}}
        
    def _handle_job_menu_choice(self, choice: int, response_id: str) -> Dict:
        """Handle job menu selections"""
        actions = {
            1: self._show_detailed_jobs,
            2: self._filter_jobs_by_location,
            3: self._filter_jobs_by_experience,
            4: self._show_application_tips,
            5: lambda: {"text": "Please provide your preferred time for career counseling:\n1. Morning\n2. Afternoon\n3. Evening", "response_id": response_id}
        }
        return actions.get(choice, lambda: {"text": "Please select a valid option (1-5)", "response_id": response_id})()

    def _handle_development_menu_choice(self, choice: int, response_id: str) -> Dict:
        """Handle development menu selections"""
        if choice == 1:  # Leadership Program
            return self._show_program_details('leadership')
        elif choice == 2:  # Technical Skills
            return self._show_program_details('technical')
        elif choice == 3:  # Entrepreneurship
            return self._show_program_details('entrepreneurship')
        elif choice == 4:  # Workshops
            return self._show_all_workshops()
        elif choice == 5:  # Resources
            response = "📓 Learning Resources\n\n"
            response += "1. Online Course Library\n"
            response += "   • 500+ courses\n"
            response += "   • Industry expert instructors\n"
            response += "   • Self-paced learning\n\n"
            response += "2. Skill Assessment Tools\n"
            response += "   • Technical skills evaluation\n"
            response += "   • Leadership potential assessment\n"
            response += "   • Personalized learning paths\n\n"
            response += "3. Career Development Guides\n"
            response += "   • Resume templates\n"
            response += "   • Interview preparation\n"
            response += "   • Salary negotiation tips\n\n"
            response += "Would you like to:\n"
            response += "1. Access online courses\n"
            response += "2. Take a skill assessment\n"
            response += "3. Download career guides\n"
            response += "4. Schedule a learning consultation\n"
            response += "5. Back to main menu"
            return {"text": response}
        return {"text": "Please select a valid option (1-5)", "response_id": response_id}

    def _handle_mentorship_menu_choice(self, choice: int, response_id: str) -> Dict:
        """Handle mentorship menu selections"""
        actions = {
            1: self._show_mentorship_application,
            2: self._show_mentor_registration,
            3: self._show_mentor_profiles,
            4: self._show_group_sessions,
            5: lambda: {"text": "Please select your preferred time for a trial session:", "response_id": response_id}
        }
        return actions.get(choice, lambda: {"text": "Please select a valid option (1-5)", "response_id": response_id})()

    def _handle_event_menu_choice(self, choice: int, response_id: str) -> Dict:
        """Handle event menu selections"""
        actions = {
            1: self._show_event_registration,
            2: self._filter_events_by_date,
            3: self._filter_events_by_location,
            4: self._setup_event_reminders,
            5: self._show_past_events
        }
        return actions.get(choice, lambda: {"text": "Please select a valid option (1-5)", "response_id": response_id})()

    def _show_detailed_jobs(self) -> Dict:
        """Show detailed job information"""
        jobs = self.job_data['jobs']
        response = "📜 Detailed Job Information:\n\n"
        
        for job in jobs[:3]:
            response += f"🔹 {job['title']} at {job['company']}\n"
            response += f"Description: {job['description']}\n"
            response += f"Skills Required:\n"
            for skill in job['skills_required']:
                response += f"  • {skill}\n"
            response += f"\nBenefits:\n"
            for benefit in job['women_friendly_benefits']:
                response += f"  • {benefit}\n"
            response += "\n"
            
        return {"text": response}

    def _handle_yes_response(self, response_id: str) -> Dict:
        """Handle 'yes' responses based on last topic"""
        if self.last_topic == 'jobs':
            return self._show_detailed_jobs()
        elif self.last_topic == 'development':
            return self._show_detailed_pd_options()
        elif self.last_topic == 'mentorship':
            return self._show_detailed_mentorship()
        elif self.last_topic == 'events':
            return self._show_detailed_events()
        return {"text": "Please specify what you'd like to know more about.", "response_id": response_id}

    def _show_detailed_pd_options(self) -> Dict:
        """Show detailed professional development options"""
        response = "📒 Choose a program to explore:\n\n"
        response += "1. Leadership Excellence Program\n"
        response += "   • Executive coaching\n"
        response += "   • Strategic management\n"
        response += "   • Team leadership\n\n"
        
        response += "2. Technical Skills Advancement\n"
        response += "   • Cloud certifications\n"
        response += "   • Data science\n"
        response += "   • Full-stack development\n\n"
        
        response += "3. Women Entrepreneurs Program\n"
        response += "   • Business planning\n"
        response += "   • Funding guidance\n"
        response += "   • Market strategy\n\n"
        
        response += "4. Soft Skills Development\n"
        response += "   • Communication\n"
        response += "   • Negotiation\n"
        response += "   • Time management\n\n"
        
        response += "5. Career Transition Support\n"
        response += "   • Role transition\n"
        response += "   • Industry switch\n"
        response += "   • Upskilling guidance\n\n"
        
        response += "Enter a number (1-5) to learn more about any program."
        return {"text": response}

    def _show_detailed_mentorship(self) -> Dict:
        """Show detailed mentorship information"""
        response = "🤝 Mentorship Programs:\n\n"
        
        response += "1. One-on-One Mentoring\n"
        response += "   • 12-week program\n"
        response += "   • Weekly sessions\n"
        response += "   • Personalized guidance\n\n"
        
        response += "2. Group Mentoring Circles\n"
        response += "   • Monthly meetings\n"
        response += "   • Peer learning\n"
        response += "   • Industry insights\n\n"
        
        response += "3. Speed Mentoring\n"
        response += "   • Quick guidance\n"
        response += "   • Multiple mentors\n"
        response += "   • Focused sessions\n\n"
        
        response += "4. Leadership Shadowing\n"
        response += "   • Real-world exposure\n"
        response += "   • Leadership insights\n"
        response += "   • Network building\n\n"
        
        response += "Would you like to:\n"
        response += "1. Apply for mentorship\n"
        response += "2. View mentor profiles\n"
        response += "3. Schedule a trial session\n"
        response += "4. Join next group session\n"
        response += "5. Back to main menu"
        
        return {"text": response}

    def _show_detailed_events(self) -> Dict:
        """Show detailed events information"""
        response = "📅 Upcoming Events:\n\n"
        
        events = [
            {
                "title": "Women in Tech Summit 2025",
                "date": "May 15, 2025",
                "time": "9:00 AM - 5:00 PM IST",
                "location": "Bangalore",
                "speakers": ["Priya Sharma - CTO, TechCorp", "Meera Patel - VP Engineering"],
                "topics": ["AI/ML in Industry", "Leadership in Tech", "Career Growth"]
            },
            {
                "title": "Career Transition Workshop",
                "date": "May 20, 2025",
                "time": "2:00 PM - 6:00 PM IST",
                "location": "Virtual",
                "speakers": ["Career Coach Anjali", "HR Director Sneha"],
                "topics": ["Role Transition", "Interview Prep", "Resume Building"]
            },
            {
                "title": "Entrepreneurship Masterclass",
                "date": "May 25, 2025",
                "time": "10:00 AM - 4:00 PM IST",
                "location": "Mumbai",
                "speakers": ["Startup Founder Ritu", "VC Partner Neha"],
                "topics": ["Business Planning", "Funding", "Growth Strategy"]
            }
        ]
        
        for event in events:
            response += f"🎯 {event['title']}\n"
            response += f"   📆 Date: {event['date']}\n"
            response += f"   ⏰ Time: {event['time']}\n"
            response += f"   📍 Location: {event['location']}\n"
            response += f"   🎓 Speakers:\n"
            for speaker in event['speakers']:
                response += f"      • {speaker}\n"
            response += f"   📒 Topics:\n"
            for topic in event['topics']:
                response += f"      • {topic}\n"
            response += "\n"
        
        response += "What would you like to do?\n"
        response += "1. Register for an event\n"
        response += "2. Get event reminders\n"
        response += "3. View past recordings\n"
        response += "4. Filter by location\n"
        response += "5. Back to main menu"
        
        return {"text": response}

    def _handle_pd_query(self, query: str) -> Dict:
        """Handle professional development queries"""
        self.current_menu = 'development'
        self.last_topic = 'development'
        
        response = "🎯 Professional Development Opportunities:\n\n"
        
        # Leadership Program
        response += "💼 1. Leadership Excellence Program\n"
        response += "   ⏱️ 3-month intensive program\n"
        response += "   ✨ Executive coaching & networking\n\n"
        
        # Technical Skills
        response += "💻 2. Technical Skills Advancement\n"
        response += "   📈 Industry-recognized certifications\n"
        response += "   👩‍💻 Hands-on project experience\n\n"
        
        # Entrepreneurship
        response += "💰 3. Women Entrepreneurs Program\n"
        response += "   📋 Business planning & strategy\n"
        response += "   💱 Funding & networking opportunities\n\n"
        
        # Upcoming Workshops
        response += "📒 4. Upcoming Workshops & Events\n"
        for workshop in self.pd_data['workshops'][:2]:
            response += f"   • {workshop['title']} - {workshop['date']}\n"
        response += "\n"
        
        # Resources
        response += "📓 5. Learning Resources\n"
        response += "   • Online courses library\n"
        response += "   • Skill assessment tools\n"
        response += "   • Career development guides\n\n"
        
        response += "Select a number (1-5) to learn more about any program."
        return {"text": response}
        
        for key, program in programs.items():
            response += f"📚 {program['title']}\n"
            response += f"   ⏱️ Duration: {program['duration']}\n"
            response += f"   📍 Format: {program['format']}\n"
            response += f"   ✨ Key Benefits: {', '.join(program['benefits'][:2])}\n\n"
            
        response += "\nUpcoming Workshops:\n"
        for workshop in self.pd_data['workshops']:
            response += f"🗓️ {workshop['title']} - {workshop['date']}\n"
            
        response += "\nWhat interests you?\n"
        response += "1. Leadership Development\n"
        response += "2. Technical Skills\n"
        response += "3. Entrepreneurship\n"
        response += "4. View all workshops\n"
        response += "5. Download resource toolkit"
        
        return {"text": response, "data": {"programs": programs}}
        
    def _handle_mentorship_query(self, query: str) -> Dict:
        """Handle mentorship queries"""
        self.current_menu = 'mentorship'
        response = "🤝 Mentorship Programs:\n\n"
        
        response += "1. One-on-One Mentoring\n"
        response += "   - Personalized guidance\n"
        response += "   - Industry expert matching\n"
        response += "   - 3-month program\n\n"
        
        response += "2. Group Mentoring Circles\n"
        response += "   - Peer learning\n"
        response += "   - Weekly sessions\n"
        response += "   - Topic-based discussions\n\n"
        
        response += "3. Flash Mentoring\n"
        response += "   - Single session guidance\n"
        response += "   - Career specific advice\n"
        response += "   - Quick problem solving\n\n"
        
        response += "How would you like to proceed?\n"
        response += "1. Apply for mentorship\n"
        response += "2. Become a mentor\n"
        response += "3. View mentor profiles\n"
        response += "4. Join next group session\n"
        response += "5. Schedule a trial session"
        
        return {"text": response}
        
    def _handle_event_query(self, query: str) -> Dict:
        """Handle event queries"""
        self.current_menu = 'events'
        events = self.session_data['events']
        response = "📅 Upcoming Events:\n\n"
        
        for event in events:
            response += f"🎯 {event['title']}\n"
            response += f"   📅 {event['date']}\n"
            response += f"   📍 {event['location']}\n"
            response += f"   ℹ️ {event['description']}\n\n"
            
        response += "What would you like to do?\n"
        response += "1. Register for an event\n"
        response += "2. Filter by date\n"
        response += "3. Filter by location\n"
        response += "4. Get event reminders\n"
        response += "5. View past event recordings"
        
        return {"text": response, "data": {"events": events}}
        
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
        
    def _filter_jobs_by_location(self) -> Dict:
        """Filter jobs by location"""
        locations = list(set(job['location'] for job in self.job_data['jobs']))
        response = "📍 Select a location:\n\n"
        for i, loc in enumerate(locations, 1):
            response += f"{i}. {loc}\n"
        return {"text": response}

    def _filter_jobs_by_experience(self) -> Dict:
        """Filter jobs by experience level"""
        response = "Select experience range:\n\n"
        response += "1. 0-2 years\n"
        response += "2. 2-5 years\n"
        response += "3. 5-8 years\n"
        response += "4. 8+ years"
        return {"text": response}

    def _show_application_tips(self) -> Dict:
        """Show job application tips"""
        tips = [
            "📝 Customize your resume for each role",
            "💼 Highlight relevant achievements",
            "📈 Quantify your impact where possible",
            "👩‍💻 Show your technical skills through projects",
            "💬 Prepare STAR format answers",
            "🤝 Network with company employees"
        ]
        response = "✨ Job Application Tips:\n\n"
        for tip in tips:
            response += f"{tip}\n"
        return {"text": response}

    def _show_program_details(self, program_type: str) -> Dict:
        """Show detailed program information"""
        program = self.pd_data['programs'].get(program_type)
        if not program:
            return {"text": "Program details not found."}
            
        response = f"📚 {program['title']}\n\n"
        response += f"Duration: {program['duration']}\n"
        response += f"Format: {program['format']}\n\n"
        
        response += "Modules:\n"
        for module in program['modules']:
            response += f"\n{module['title']}:\n"
            for topic in module['topics']:
                response += f"  • {topic}\n"
                
        response += "\nBenefits:\n"
        for benefit in program['benefits']:
            response += f"  • {benefit}\n"
            
        return {"text": response}

    def _show_all_workshops(self) -> Dict:
        """Show all upcoming workshops"""
        workshops = self.pd_data['workshops']
        response = "📅 Upcoming Workshops:\n\n"
        
        for workshop in workshops:
            response += f"📒 {workshop['title']}\n"
            response += f"   ⏰ Duration: {workshop['duration']}\n"
            response += f"   📆 Date: {workshop['date']}\n"
            response += f"   📍 Format: {workshop['format']}\n\n"
            
        return {"text": response}

    def _format_events(self, events: List[Dict]) -> str:
        """Format events list for display."""
        if not events:
            return "No upcoming events scheduled."
            
        formatted = ""
        for event in events:
            formatted += f"📅 {event['title']}\n"
            formatted += f"   Date: {event['date']}\n"
            formatted += f"   Location: {event['location']}\n"
            formatted += f"   {event['description']}\n\n"
        return formatted
        
    def _show_mentorship_application(self) -> Dict:
        """Show mentorship application form"""
        response = "📝 Mentorship Application\n\n"
        response += "Please provide the following details:\n\n"
        response += "1. Your current role/experience\n"
        response += "2. Areas you'd like mentoring in\n"
        response += "3. Preferred mentoring format (1:1/Group)\n"
        response += "4. Time commitment (hours/week)\n"
        response += "5. Specific goals you want to achieve"
        return {"text": response}

    def _show_mentor_registration(self) -> Dict:
        """Show mentor registration form"""
        response = "👩‍💻 Become a Mentor\n\n"
        response += "Share your expertise! Please provide:\n\n"
        response += "1. Your area of expertise\n"
        response += "2. Years of experience\n"
        response += "3. Time you can commit (hours/week)\n"
        response += "4. Preferred mentoring format\n"
        response += "5. Brief bio for your profile"
        return {"text": response}

    def _show_mentor_profiles(self) -> Dict:
        """Show available mentor profiles"""
        response = "👨‍💻 Available Mentors:\n\n"
        
        mentors = [
            {
                "name": "Priya Sharma",
                "expertise": "Technology Leadership",
                "experience": "15 years",
                "company": "TechCorp India"
            },
            {
                "name": "Meera Patel",
                "expertise": "Product Management",
                "experience": "10 years",
                "company": "ProductFirst"
            },
            {
                "name": "Anjali Desai",
                "expertise": "Data Science",
                "experience": "8 years",
                "company": "AI Solutions"
            }
        ]
        
        for i, mentor in enumerate(mentors, 1):
            response += f"{i}. {mentor['name']}\n"
            response += f"   💼 {mentor['expertise']}\n"
            response += f"   ✨ {mentor['experience']} at {mentor['company']}\n\n"
            
        return {"text": response}

    def _show_group_sessions(self) -> Dict:
        """Show upcoming group mentoring sessions"""
        response = "👥 Upcoming Group Sessions:\n\n"
        
        sessions = [
            {
                "topic": "Leadership in Tech",
                "date": "2025-05-05",
                "time": "6:00 PM IST",
                "mentor": "Priya Sharma"
            },
            {
                "topic": "Product Strategy",
                "date": "2025-05-07",
                "time": "7:00 PM IST",
                "mentor": "Meera Patel"
            },
            {
                "topic": "Data Science Career Path",
                "date": "2025-05-09",
                "time": "6:30 PM IST",
                "mentor": "Anjali Desai"
            }
        ]
        
        for session in sessions:
            response += f"📒 {session['topic']}\n"
            response += f"   📅 {session['date']} at {session['time']}\n"
            response += f"   👩‍💻 Led by {session['mentor']}\n\n"
            
        return {"text": response}

    def _show_event_registration(self) -> Dict:
        """Show event registration form"""
        response = "📃 Event Registration\n\n"
        response += "Please provide:\n\n"
        response += "1. Your name\n"
        response += "2. Email\n"
        response += "3. Phone number\n"
        response += "4. Event(s) you want to attend\n"
        response += "5. Any specific requirements"
        return {"text": response}

    def _filter_events_by_date(self) -> Dict:
        """Filter events by date range"""
        response = "Select date range:\n\n"
        response += "1. This week\n"
        response += "2. Next week\n"
        response += "3. This month\n"
        response += "4. Next month\n"
        response += "5. Custom date range"
        return {"text": response}

    def _filter_events_by_location(self) -> Dict:
        """Filter events by location"""
        response = "Select location:\n\n"
        response += "1. Online\n"
        response += "2. Bangalore\n"
        response += "3. Mumbai\n"
        response += "4. Delhi\n"
        response += "5. Other cities"
        return {"text": response}

    def _setup_event_reminders(self) -> Dict:
        """Setup event reminders"""
        response = "⏰ Reminder Preferences:\n\n"
        response += "When would you like to be reminded?\n\n"
        response += "1. 1 day before\n"
        response += "2. 2 days before\n"
        response += "3. 1 week before\n"
        response += "4. Custom reminder\n"
        response += "5. All of the above"
        return {"text": response}

    def _show_past_events(self) -> Dict:
        """Show past events with recordings"""
        response = "📼 Past Event Recordings:\n\n"
        
        past_events = [
            {
                "title": "Women in Tech Summit 2025",
                "date": "2025-04-15",
                "recording": "https://example.com/recording1"
            },
            {
                "title": "Leadership Masterclass",
                "date": "2025-04-10",
                "recording": "https://example.com/recording2"
            },
            {
                "title": "Career Transition Workshop",
                "date": "2025-04-05",
                "recording": "https://example.com/recording3"
            }
        ]
        
        for event in past_events:
            response += f"🎥 {event['title']}\n"
            response += f"   📅 Held on: {event['date']}\n"
            response += f"   📹 Recording: {event['recording']}\n\n"
            
        return {"text": response}

    def _format_syllabus(self, course_id: str) -> str:
        """Format course syllabus for display."""
        if not course_id:
            return "Course not found."
            
        course_key = next((k for k, v in self.course_data['courses'].items() if v['id'] == course_id), None)
        if not course_key:
            return "Course syllabus not available."
            
        course = self.course_data['courses'][course_key]
        formatted = f"📚 Detailed Syllabus: {course['title']}\n\n"
        
        for week in course['syllabus']:
            formatted += f"Week {week['week']}: {week['topic']}\n"
            for content in week['content']:
                formatted += f"  • {content}\n"
            formatted += "\n"
            
        formatted += "\nReady to start your learning journey? Choose:\n"
        formatted += "1. Register Now\n"
        formatted += "2. Schedule Consultation\n"
        formatted += "3. Back to Course Details"
        
        return formatted

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