from cryptography.fernet import Fernet
from typing import Dict, Optional
import json
import os
from datetime import datetime, timedelta
import jwt
from enum import Enum

class SecurityLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class SecurityManager:
    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        self.jwt_secret = os.urandom(32).hex()
        
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        return self.fernet.encrypt(data.encode()).decode()
        
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt encrypted data."""
        return self.fernet.decrypt(encrypted_data.encode()).decode()
        
    def generate_token(self, user_data: Dict) -> str:
        """Generate JWT token for session."""
        expiration = datetime.utcnow() + timedelta(hours=1)
        return jwt.encode(
            {**user_data, "exp": expiration},
            self.jwt_secret,
            algorithm="HS256"
        )
        
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token."""
        try:
            return jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return None
            
    def sanitize_data(self, data: Dict) -> Dict:
        """Remove sensitive information from data."""
        sensitive_fields = ['password', 'ssn', 'credit_card']
        return {k: '***' if k in sensitive_fields else v for k, v in data.items()}
        
    def check_security_level(self, data: Dict) -> SecurityLevel:
        """Check required security level for data."""
        if any(field in data for field in ['ssn', 'credit_card']):
            return SecurityLevel.HIGH
        elif any(field in data for field in ['email', 'phone']):
            return SecurityLevel.MEDIUM
        return SecurityLevel.LOW 