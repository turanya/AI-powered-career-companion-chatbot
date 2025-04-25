from chatbot import Chatbot
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Initialize the chatbot
    asha = Chatbot()
    
    print("Welcome to Asha AI! 👋")
    print("I'm here to help you with:")
    print("1. Finding jobs and career opportunities")
    print("2. Career guidance and mentorship")
    print("3. Education and skill development")
    print("4. Professional development resources")
    print("\nType 'exit' or 'quit' to end the conversation")
    print("-" * 50)

    session_id = "terminal-session"
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check if user wants to exit
        if user_input.lower() in ['exit', 'quit']:
            print("\nAsha: Goodbye! Have a great day! 👋")
            break
        
        # Skip empty inputs
        if not user_input:
            continue
        
        try:
            # Get response from chatbot
            response = asha.process_message(user_input, session_id)
            print(f"\nAsha: {response['text']}")
        except Exception as e:
            print(f"\nAsha: I apologize, but I encountered an error. Please try again.")

if __name__ == "__main__":
    main() 