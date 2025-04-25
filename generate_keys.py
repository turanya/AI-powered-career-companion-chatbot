import secrets
import base64
import os

def generate_jwt_secret():
    """Generate a secure JWT secret key."""
    return secrets.token_urlsafe(32)

def generate_encryption_key():
    """Generate a secure encryption key."""
    return base64.urlsafe_b64encode(os.urandom(32)).decode()

if __name__ == "__main__":
    jwt_secret = generate_jwt_secret()
    encryption_key = generate_encryption_key()
    
    print("\nGenerated Keys:")
    print("--------------")
    print(f"JWT_SECRET_KEY={jwt_secret}")
    print(f"ENCRYPTION_KEY={encryption_key}")
    print("\nAdd these to your .env file!") 