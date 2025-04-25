from cryptography.fernet import Fernet

def generate_fernet_key():
    """Generate a proper Fernet key."""
    return Fernet.generate_key().decode()

if __name__ == "__main__":
    key = generate_fernet_key()
    print("\nGenerated Fernet Key:")
    print("-------------------")
    print(f"ENCRYPTION_KEY={key}")
    print("\nAdd this to your .env file!") 