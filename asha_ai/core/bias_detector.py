from typing import Dict, List, Tuple
import re
from enum import Enum

class BiasType(Enum):
    GENDER = "gender"
    AGE = "age"
    RACIAL = "racial"
    NONE = "none"

class BiasDetector:
    def __init__(self):
        # Initialize bias detection patterns
        self.gender_bias_patterns = [
            r"only (men|women) can",
            r"(men|women) are better at",
            r"typical (male|female) job",
            r"(he|she) would be better"
        ]
        
        self.age_bias_patterns = [
            r"too (young|old) for",
            r"age requirement",
            r"(young|old) people can't"
        ]
        
        self.inclusive_alternatives = {
            "chairman": "chairperson",
            "businessman": "business person",
            "policeman": "police officer",
            "stewardess": "flight attendant",
            "mankind": "humanity"
        }
        
    def detect_bias(self, text: str) -> Tuple[BiasType, float, str]:
        """
        Detect bias in text and return bias type, confidence score, and suggestion.
        """
        # Check for gender bias
        for pattern in self.gender_bias_patterns:
            if re.search(pattern, text.lower()):
                return (BiasType.GENDER, 0.8, self._get_inclusive_suggestion(text))
                
        # Check for age bias
        for pattern in self.age_bias_patterns:
            if re.search(pattern, text.lower()):
                return (BiasType.AGE, 0.7, "Consider focusing on skills and experience rather than age")
                
        return (BiasType.NONE, 0.0, "")
        
    def _get_inclusive_suggestion(self, text: str) -> str:
        """Generate inclusive language suggestions."""
        text_lower = text.lower()
        for biased, inclusive in self.inclusive_alternatives.items():
            if biased in text_lower:
                return f"Consider using '{inclusive}' instead of '{biased}'"
        return "Consider using more inclusive language"
        
    def check_response_bias(self, response: str) -> bool:
        """Check if a response contains biased language."""
        bias_type, confidence, _ = self.detect_bias(response)
        return bias_type != BiasType.NONE and confidence > 0.6
        
    def get_inclusive_alternative(self, text: str) -> str:
        """Get inclusive alternative for potentially biased text."""
        bias_type, _, suggestion = self.detect_bias(text)
        if bias_type != BiasType.NONE:
            return suggestion
        return text 