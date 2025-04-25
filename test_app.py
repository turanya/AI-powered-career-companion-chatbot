import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def test_health():
    try:
        response = requests.get("http://127.0.0.1:8000/health")
        print("Health Check Response:", response.json())
        return response.status_code == 200
    except Exception as e:
        print("Health Check Failed:", str(e))
        return False

def test_auth():
    try:
        # Get token
        response = requests.post(
            "http://127.0.0.1:8000/token",
            data={"username": "test_user", "password": "test_password"}
        )
        print("Auth Response:", response.json())
        return "access_token" in response.json()
    except Exception as e:
        print("Auth Test Failed:", str(e))
        return False

def test_chat():
    try:
        # First get token
        auth_response = requests.post(
            "http://127.0.0.1:8000/token",
            data={"username": "test_user", "password": "test_password"}
        )
        token = auth_response.json()["access_token"]

        # Then test chat
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        chat_data = {
            "content": "Hello! How are you?",
            "session_id": "test-session"
        }
        response = requests.post(
            "http://127.0.0.1:8000/chat",
            headers=headers,
            json=chat_data
        )
        print("Chat Response:", response.json())
        return response.status_code == 200
    except Exception as e:
        print("Chat Test Failed:", str(e))
        return False

if __name__ == "__main__":
    print("\nRunning tests...")
    print("\n1. Testing Health Endpoint...")
    health_ok = test_health()
    print("Health Check:", "✅ Passed" if health_ok else "❌ Failed")

    print("\n2. Testing Authentication...")
    auth_ok = test_auth()
    print("Authentication:", "✅ Passed" if auth_ok else "❌ Failed")

    print("\n3. Testing Chat...")
    chat_ok = test_chat()
    print("Chat:", "✅ Passed" if chat_ok else "❌ Failed") 