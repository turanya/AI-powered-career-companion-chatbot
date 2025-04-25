from typing import Dict, Optional, Tuple
import logging
from enum import Enum
from datetime import datetime

class ErrorType(Enum):
    API_ERROR = "api_error"
    SECURITY_ERROR = "security_error"
    BIAS_ERROR = "bias_error"
    INPUT_ERROR = "input_error"
    SYSTEM_ERROR = "system_error"

class ErrorHandler:
    def __init__(self):
        self.logger = logging.getLogger("asha_ai")
        self.setup_logging()
        self.fallback_responses = {
            ErrorType.API_ERROR: "I'm having trouble connecting to our services. Let me provide you with cached information instead.",
            ErrorType.SECURITY_ERROR: "I encountered a security concern. Please try again with different parameters.",
            ErrorType.BIAS_ERROR: "I want to ensure our conversation remains inclusive and unbiased. Could you rephrase that?",
            ErrorType.INPUT_ERROR: "I didn't quite understand that. Could you please rephrase or provide more details?",
            ErrorType.SYSTEM_ERROR: "I'm experiencing a technical issue. Please try again in a moment."
        }
        
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler("asha_errors.log")
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)
        
    def handle_error(self, error: Exception, context: Dict = None) -> Tuple[str, ErrorType]:
        """Handle various types of errors and return appropriate response."""
        error_type = self._categorize_error(error)
        self._log_error(error, error_type, context)
        return self.get_fallback_response(error_type), error_type
        
    def get_fallback_response(self, error_type: ErrorType) -> str:
        """Get appropriate fallback response for error type."""
        return self.fallback_responses.get(
            error_type,
            "I encountered an unexpected issue. Please try again."
        )
        
    def _categorize_error(self, error: Exception) -> ErrorType:
        """Categorize the error type based on the exception."""
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorType.API_ERROR
        elif isinstance(error, (PermissionError, ValueError)):
            return ErrorType.SECURITY_ERROR
        elif isinstance(error, KeyError):
            return ErrorType.INPUT_ERROR
        return ErrorType.SYSTEM_ERROR
        
    def _log_error(self, error: Exception, error_type: ErrorType, context: Dict = None) -> None:
        """Log error details."""
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type.value,
            "error_message": str(error),
            "context": context or {}
        }
        self.logger.error(f"Error occurred: {error_data}")
        
    def report_error(self, message: str, severity: str = "error") -> None:
        """Report custom error message."""
        getattr(self.logger, severity)(message)
        
    def suggest_alternative(self, error_type: ErrorType, context: Dict = None) -> Optional[str]:
        """Suggest alternative actions based on error type."""
        if error_type == ErrorType.API_ERROR:
            return "You can try viewing cached job listings or saved resources while we restore the connection."
        elif error_type == ErrorType.INPUT_ERROR:
            return "Try using simpler terms or breaking down your request into smaller parts."
        return None 