import json
from datetime import datetime

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

        # Simple response templates
        self.responses = {
            "greeting": [
                "Hello! 👋 I'm Asha, your friendly career companion! How can I brighten your career journey today?",
                "Hi there! ✨ I'm Asha, and I'm here to help you achieve your career dreams. What would you like to explore?",
                "Welcome! 🌟 I'm excited to help you on your professional journey. How may I assist you today?"
            ],
            "about_website": [
                "JobsForHer is India's largest platform dedicated to empowering women in their careers! 💪 Here's what makes us special:\n\n" +
                "1. Job Opportunities: Thousands of verified jobs from women-friendly companies that value diversity\n" +
                "2. Mentorship: Connect with inspiring women leaders who've walked the path\n" +
                "3. Resources: Access to skill-building webinars, workshops, and learning programs\n" +
                "4. Community: Join a supportive network of ambitious women professionals\n\n" +
                "I'd love to tell you more! Just type the number (1-4) you're interested in, or ask me anything! 😊"
            ],
            "job_search": [
                "Exciting opportunities await! 🚀 Here are the thriving sectors where we have amazing openings:\n\n" +
                "1. Technology & IT (Software, Data, Product roles)\n" +
                "2. HR & Recruitment (HR Manager, Talent Acquisition)\n" +
                "3. Sales & Marketing (Digital Marketing, Business Development)\n" +
                "4. Finance & Accounting (Financial Analyst, Accountant)\n" +
                "5. Operations & Project Management\n\n" +
                "Simply type a number (1-5) to explore jobs in that field, or tell me what you're looking for! 💼"
            ],
            "career_guidance": [
                "I'm here to help you shine! ✨ Here's how we can support your growth:\n\n" +
                "1. One-on-one mentorship with industry leaders\n" +
                "2. Professional resume review and optimization\n" +
                "3. Interview preparation and confidence building\n" +
                "4. Career transition strategy and planning\n\n" +
                "Type a number (1-4) to learn more about any option, or share what's on your mind! 🌟"
            ],
            "education": [
                "Let's invest in your growth! 📚 Here are our learning pathways:\n\n" +
                "1. Professional certification courses (Tech, Management, Finance)\n" +
                "2. Skill development workshops\n" +
                "3. Leadership development programs\n" +
                "4. Technical training\n\n" +
                "What skills would you like to develop?"
            ],
            "default": [
                "Could you please tell me more about that?",
                "I'm interested in hearing more details.",
                "Could you elaborate on that?"
            ]
        }

    def translate_hinglish(self, text):
        """Convert Hinglish text to English"""
        words = text.lower().split()
        translated = []
        
        for word in words:
            # Check if word exists in hinglish mapping
            if word in self.hinglish_map:
                translated.append(self.hinglish_map[word])
            else:
                translated.append(word)
        
        return " ".join(translated)

    def get_response(self, user_input):
        """Generate a response based on user input."""
        # First translate any Hinglish to English
        user_input = self.translate_hinglish(user_input.lower())

        # Initialize last_context if not exists
        if not hasattr(self, 'last_context'):
            self.last_context = None
            
        # Handle numerical inputs for different sections
        if user_input.isdigit():
            num = int(user_input)
            if self.last_context == "about_website":
                if num == 1:
                    return {"text": "✨ Our job opportunities are carefully curated from women-friendly companies that promote diversity and inclusion. You'll find flexible work options, return-to-work programs, and roles across experience levels. Would you like to explore current openings? (Type 'jobs' or '1' to see opportunities)"}
                elif num == 2:
                    return {"text": "🌟 Our mentorship program connects you with successful women leaders who can guide your career journey. They provide personalized advice, share their experiences, and help you overcome challenges. Would you like to know more about mentorship? (Type 'mentor' or '2' to learn more)"}
                elif num == 3:
                    return {"text": "📚 We offer a variety of learning resources to help you upskill and grow. From technical workshops to leadership programs, we've got your development covered. What skills are you looking to develop? (Type 'courses' or '3' to explore)"}
                elif num == 4:
                    return {"text": "👥 Our community is your support system! Connect with like-minded professionals, share experiences, and grow together. Join discussions, networking events, and success story sessions. Ready to connect? (Type 'community' or '4' to join)"}
            elif self.last_context == "education":
                edu_responses = {
                    1: "🎓 Our Professional Certification Courses include:\n- Cloud Computing & DevOps\n- Product Management\n- Digital Marketing\n- Financial Analysis\n- Data Science & AI\n\nWhich field interests you? Just tell me the area you'd like to explore!",
                    2: "💡 Our Skill Development Workshops cover:\n- Communication & Presentation\n- Time Management\n- Project Management\n- Negotiation Skills\n- Problem Solving\n\nWould you like to know the upcoming workshop schedule?",
                    3: "👑 Leadership Development Programs include:\n- Executive Leadership\n- Team Management\n- Strategic Thinking\n- Decision Making\n- Change Management\n\nReady to develop your leadership skills?",
                    4: "💻 Technical Training programs cover:\n- Programming Languages\n- Web Development\n- Database Management\n- Cybersecurity\n- Cloud Technologies\n\nWhich technical skills would you like to develop?"
                }
                return {"text": edu_responses.get(num, "Please select a number between 1-4 for learning pathways! 😊")}
            
            elif self.last_context == "career_guidance":
                guidance_responses = {
                    1: "🌟 Our mentorship program pairs you with experienced leaders who provide:\n- Career path guidance\n- Industry insights\n- Personal growth strategies\n- Network expansion\n\nWould you like to explore available mentors?",
                    2: "📝 Our resume review service includes:\n- Professional formatting\n- Content optimization\n- Keyword optimization\n- ATS compatibility check\n- Personal branding tips\n\nReady to make your resume stand out?",
                    3: "🎯 Interview preparation includes:\n- Mock interviews\n- Common questions practice\n- Body language tips\n- Salary negotiation skills\n- Industry-specific prep\n\nWould you like to schedule a practice session?",
                    4: "🔄 Career transition support offers:\n- Skills gap analysis\n- Industry research\n- Transition timeline planning\n- Networking strategies\n- Personal branding\n\nReady to plan your career transition?"
                }
                return {"text": guidance_responses.get(num, "Please select a number between 1-4 for guidance options! 😊")}
            
            elif self.last_context == "job_search":
                job_responses = {
                    1: "💻 In Technology & IT, we have exciting roles in:\n- Software Development\n- Data Science\n- Product Management\n- UI/UX Design\n\nWould you like me to show you the latest tech opportunities?",
                    2: "👥 Our HR & Recruitment positions include:\n- HR Business Partner\n- Talent Acquisition Specialist\n- Learning & Development Manager\n- Employee Relations\n\nShall I share some current HR openings with you?",
                    3: "📈 In Sales & Marketing, we offer roles in:\n- Digital Marketing\n- Content Strategy\n- Business Development\n- Brand Management\n\nWould you like to see our marketing opportunities?",
                    4: "💰 Finance & Accounting positions include:\n- Financial Analyst\n- Account Manager\n- Investment Advisory\n- Risk Management\n\nInterested in exploring these roles?",
                    5: "📋 Operations & Project Management roles:\n- Project Manager\n- Operations Lead\n- Process Improvement\n- Team Leadership\n\nWould you like to see current openings?"
                }
                return {"text": job_responses.get(num, "I'm sorry, please select a number between 1-5 for job categories! 😊")}

        # Check for website/about queries
        if any(word in user_input for word in ['about', 'website', 'platform', 'jobsforher', 'tell me', 'what is']):
            self.last_context = "about_website"
            return {"text": self.responses["about_website"][0]}

        # Check for job-related queries
        elif any(word in user_input for word in ['job', 'work', 'career', 'position', 'employment', 'salary', 'money']):
            self.last_context = "job_search"
            return {"text": self.responses["job_search"][0]}

        # Check for education/course related queries
        elif any(word in user_input for word in ['course', 'study', 'education', 'learn', 'training']):
            self.last_context = "education"
            return {"text": self.responses["education"][0]}

        # Check for career guidance
        elif any(word in user_input for word in ['guide', 'advice', 'mentor', 'guidance', 'help']):
            self.last_context = "career_guidance"
            return {"text": self.responses["career_guidance"][0]}

        # Check for greetings
        elif any(word in user_input for word in ['hello', 'hi', 'hey', 'greetings', 'namaste']):
            self.last_context = "greeting"
            return {"text": self.responses["greeting"][0]}

        # Default response
        return {"text": self.responses["default"][0]}

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