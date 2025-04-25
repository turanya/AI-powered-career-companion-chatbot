import os
import json
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64
import logging
from datetime import datetime, timedelta
import jwt
from functools import wraps
import re
from enum import Enum
import uuid
from fastapi import HTTPException, status
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EncryptionType(Enum):
    FERNET = "fernet"
    AES = "aes"
    RSA = "rsa"
    CUSTOM = "custom"
    BLOWFISH = "blowfish"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SecurityManager:
    def __init__(self):
        # Initialize encryption key
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            key = base64.urlsafe_b64encode(os.urandom(32))
        elif not isinstance(key, bytes):
            try:
                key = base64.urlsafe_b64decode(key.encode())
                key = base64.urlsafe_b64encode(key)
            except:
                key = base64.urlsafe_b64encode(os.urandom(32))
        
        self.encryption_key = key
        self.fernet = Fernet(self.encryption_key)
        
        # Initialize JWT secret key
        self.jwt_secret = os.getenv('JWT_SECRET_KEY', 'default-secret')
        self.jwt_algorithm = os.getenv('JWT_ALGORITHM', 'HS256')
        
        # Access control configuration
        self.access_controls = {
            'admin': ['read', 'write', 'delete', 'manage_users', 'audit_logs'],
            'user': ['read', 'write', 'self_delete'],
            'guest': ['read']
        }
        
        # Data anonymization rules
        self.anonymization_rules = {
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
            'phone': r'\b\d{10}\b',
            'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
            'credit_card': r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b',
            'bank_account': r'\b\d{8,17}\b'
        }
        
        # Security policies
        self.security_policies = {
            'password_policy': {
                'min_length': 12,
                'require_uppercase': True,
                'require_lowercase': True,
                'require_numbers': True,
                'require_special_chars': True,
                'max_age_days': 90
            },
            'session_policy': {
                'max_duration': 3600,  # 1 hour
                'inactivity_timeout': 900,  # 15 minutes
                'max_concurrent_sessions': 3
            },
            'rate_limiting': {
                'max_requests_per_minute': 60,
                'max_failed_attempts': 5,
                'lockout_duration': 1800  # 30 minutes
            }
        }
        
        # Initialize security monitoring
        self.failed_attempts = {}
        self.session_tracking = {}
        self.security_alerts = []

    def _generate_encryption_key(self) -> bytes:
        """Generate a secure encryption key with enhanced entropy."""
        try:
            # Try to load existing key from environment
            key = os.getenv('ENCRYPTION_KEY')
            if key:
                return base64.urlsafe_b64decode(key)
            
            # Generate new key with enhanced entropy
            key = Fernet.generate_key()
            salt = os.urandom(16)
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=default_backend()
            )
            derived_key = kdf.derive(key)
            
            # Store in environment for persistence
            os.environ['ENCRYPTION_KEY'] = base64.urlsafe_b64encode(derived_key).decode()
            return derived_key
        except Exception as e:
            logger.error(f"Error generating encryption key: {e}")
            raise

    def _generate_jwt_secret(self) -> str:
        """Generate a secure JWT secret key with enhanced entropy."""
        try:
            # Generate a random 64-byte key
            return base64.urlsafe_b64encode(os.urandom(64)).decode()
        except Exception as e:
            logger.error(f"Error generating JWT secret: {e}")
            raise

    def encrypt_data(self, data: Any, encryption_type: EncryptionType = EncryptionType.FERNET) -> str:
        """Enhanced encryption with multiple algorithms support."""
        try:
            if not isinstance(data, str):
                data = json.dumps(data)
            
            if encryption_type == EncryptionType.FERNET:
                encrypted_data = self.fernet.encrypt(data.encode())
            elif encryption_type == EncryptionType.AES:
                # Implement AES encryption
                pass
            elif encryption_type == EncryptionType.RSA:
                # Implement RSA encryption
                pass
            
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            raise

    def decrypt_data(self, encrypted_data: str, encryption_type: EncryptionType = EncryptionType.FERNET) -> Any:
        """Enhanced decryption with multiple algorithms support."""
        try:
            if encryption_type == EncryptionType.FERNET:
                decrypted_data = self.fernet.decrypt(
                    base64.urlsafe_b64decode(encrypted_data)
                )
            elif encryption_type == EncryptionType.AES:
                # Implement AES decryption
                pass
            elif encryption_type == EncryptionType.RSA:
                # Implement RSA decryption
                pass
            
            try:
                return json.loads(decrypted_data)
            except json.JSONDecodeError:
                return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            raise

    def anonymize_data(self, data: Dict[str, Any], level: str = 'high') -> Dict[str, Any]:
        """Enhanced data anonymization with multiple levels."""
        try:
            anonymized_data = data.copy()
            
            for field, pattern in self.anonymization_rules.items():
                if field in anonymized_data:
                    value = str(anonymized_data[field])
                    if level == 'high':
                        anonymized_data[field] = '*' * len(value)
                    elif level == 'medium':
                        anonymized_data[field] = re.sub(
                            pattern,
                            lambda m: m.group()[:2] + '*' * (len(m.group()) - 2),
                            value
                        )
            
            return anonymized_data
        except Exception as e:
            logger.error(f"Error anonymizing data: {e}")
            return data

    def generate_token(self, user_id: str, role: str, expires_in: int = 3600) -> str:
        """Enhanced token generation with additional security claims."""
        try:
            payload = {
                'user_id': user_id,
                'role': role,
                'exp': datetime.utcnow() + timedelta(seconds=expires_in),
                'iat': datetime.utcnow(),
                'jti': str(uuid.uuid4()),  # Unique token ID
                'aud': 'asha-ai',  # Audience
                'iss': 'asha-ai-security'  # Issuer
            }
            return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        except Exception as e:
            logger.error(f"Error generating token: {e}")
            raise

    @classmethod
    def require_auth(cls, required_role: Optional[str] = None):
        """Decorator to require authentication and optionally specific role."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                try:
                    # Get token from request headers
                    token = kwargs.get('token')
                    if not token:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Not authenticated"
                        )
                    
                    # Verify token
                    try:
                        payload = jwt.decode(
                            token,
                            os.getenv('JWT_SECRET_KEY', 'default-secret'),
                            algorithms=[os.getenv('JWT_ALGORITHM', 'HS256')]
                        )
                        kwargs['user_id'] = payload.get('sub')
                        
                        # Check role if required
                        if required_role and payload.get('role') != required_role:
                            raise HTTPException(
                                status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"Role {required_role} required"
                            )
                    except jwt.JWTError:
                        raise HTTPException(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token"
                        )
                    
                    return await func(*args, **kwargs)
                except Exception as e:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=str(e)
                    )
            return wrapper
        return decorator

    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.jwt_algorithm],
                audience='asha-ai',
                issuer='asha-ai-security'
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error"
            )

    def check_access(self, role: str, action: str) -> bool:
        """Enhanced access control with logging."""
        try:
            has_access = action in self.access_controls.get(role, [])
            if not has_access:
                logger.warning(f"Access denied: Role {role} attempted {action}")
            return has_access
        except Exception as e:
            logger.error(f"Error checking access: {e}")
            return False

    def hash_password(self, password: str) -> str:
        """Hash a password for storing."""
        import hashlib
        import os
        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        return salt.hex() + key.hex()

    def verify_password(self, stored_password: str, provided_password: str) -> bool:
        """Verify a stored password against one provided by user"""
        import hashlib
        salt = bytes.fromhex(stored_password[:64])
        stored_key = bytes.fromhex(stored_password[64:])
        key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt,
            100000
        )
        return stored_key == key

    def track_failed_attempt(self, user_id: str) -> None:
        """Track failed authentication attempts."""
        if user_id not in self.failed_attempts:
            self.failed_attempts[user_id] = {
                'count': 0,
                'last_attempt': datetime.now()
            }
        
        self.failed_attempts[user_id]['count'] += 1
        self.failed_attempts[user_id]['last_attempt'] = datetime.now()
        
        if self.failed_attempts[user_id]['count'] >= self.security_policies['rate_limiting']['max_failed_attempts']:
            self._lockout_user(user_id)
    
    def _lockout_user(self, user_id: str) -> None:
        """Lock out user after too many failed attempts."""
        lockout_duration = self.security_policies['rate_limiting']['lockout_duration']
        self.failed_attempts[user_id]['locked_until'] = datetime.now() + timedelta(seconds=lockout_duration)
        logger.warning(f"User {user_id} locked out for {lockout_duration} seconds")
    
    def is_user_locked(self, user_id: str) -> bool:
        """Check if user is currently locked out."""
        if user_id not in self.failed_attempts:
            return False
        
        if 'locked_until' in self.failed_attempts[user_id]:
            if datetime.now() < self.failed_attempts[user_id]['locked_until']:
                return True
            else:
                # Clear lockout if expired
                del self.failed_attempts[user_id]['locked_until']
                self.failed_attempts[user_id]['count'] = 0
        
        return False
    
    def track_session(self, user_id: str, session_id: str) -> None:
        """Track user sessions for security monitoring."""
        if user_id not in self.session_tracking:
            self.session_tracking[user_id] = []
        
        # Remove expired sessions
        self.session_tracking[user_id] = [
            s for s in self.session_tracking[user_id]
            if datetime.now() - s['last_activity'] < timedelta(seconds=self.security_policies['session_policy']['max_duration'])
        ]
        
        # Add new session
        self.session_tracking[user_id].append({
            'session_id': session_id,
            'start_time': datetime.now(),
            'last_activity': datetime.now()
        })
        
        # Check concurrent sessions
        if len(self.session_tracking[user_id]) > self.security_policies['session_policy']['max_concurrent_sessions']:
            self._handle_concurrent_sessions(user_id)
    
    def _handle_concurrent_sessions(self, user_id: str) -> None:
        """Handle excessive concurrent sessions."""
        # Sort sessions by last activity
        self.session_tracking[user_id].sort(key=lambda x: x['last_activity'])
        
        # Remove oldest sessions
        while len(self.session_tracking[user_id]) > self.security_policies['session_policy']['max_concurrent_sessions']:
            old_session = self.session_tracking[user_id].pop(0)
            logger.warning(f"Terminated old session {old_session['session_id']} for user {user_id}")
    
    def update_session_activity(self, user_id: str, session_id: str) -> None:
        """Update session activity timestamp."""
        if user_id in self.session_tracking:
            for session in self.session_tracking[user_id]:
                if session['session_id'] == session_id:
                    session['last_activity'] = datetime.now()
                    break
    
    def log_security_alert(self, alert_type: str, details: Dict[str, Any]) -> None:
        """Log security alerts for monitoring."""
        alert = {
            'timestamp': datetime.now(),
            'type': alert_type,
            'details': details,
            'severity': self._determine_alert_severity(alert_type)
        }
        self.security_alerts.append(alert)
        logger.warning(f"Security alert: {alert_type} - {details}")
    
    def _determine_alert_severity(self, alert_type: str) -> str:
        """Determine severity level for security alerts."""
        severity_levels = {
            'failed_login': 'high',
            'concurrent_sessions': 'medium',
            'token_expired': 'low',
            'access_denied': 'medium',
            'data_breach_attempt': 'critical'
        }
        return severity_levels.get(alert_type, 'medium')
    
    def get_security_alerts(self, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve security alerts, optionally filtered by severity."""
        if severity:
            return [alert for alert in self.security_alerts if alert['severity'] == severity]
        return self.security_alerts

    def create_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.jwt_secret, algorithm=self.jwt_algorithm)

    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Anonymize sensitive data before storing or transmitting"""
        # Implementation depends on specific data structure
        # This is a placeholder implementation
        if isinstance(data, dict):
            anonymized = {}
            for key, value in data.items():
                if key in ['email', 'phone', 'address']:
                    anonymized[key] = self._mask_data(value)
                else:
                    anonymized[key] = value
            return anonymized
        return data

    def _mask_data(self, value: str) -> str:
        """Mask sensitive data"""
        if not value:
            return value
        if '@' in value:  # Email
            username, domain = value.split('@')
            return f"{username[0]}{'*' * (len(username)-2)}{username[-1]}@{domain}"
        elif value.replace('+', '').replace('-', '').isdigit():  # Phone
            return f"{'*' * (len(value)-4)}{value[-4:]}"
        else:  # Other
            return f"{value[0]}{'*' * (len(value)-2)}{value[-1]}" 