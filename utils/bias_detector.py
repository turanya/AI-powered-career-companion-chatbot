import re
from typing import Dict, List, Tuple

class BiasDetector:
    def __init__(self):
        self.bias_patterns = {
            'gender_bias': [
                r'\b(only|just|better)\s+(men|women)\b',
                r'\b(male|female)\s+dominated\b',
                r'\b(he|she)\s+would\s+be\s+better\b'
            ],
            'stereotype_bias': [
                r'\b(typical|usually|always)\s+(male|female)\s+(job|role|position)\b',
                r'\b(men|women)\s+(can\'t|cannot|shouldn\'t)\b'
            ]
        }
        
        self.positive_alternatives = {
            'gender_bias': [
                "All qualified candidates are welcome",
                "Skills and experience are what matter",
                "We value diversity and inclusion"
            ],
            'stereotype_bias': [
                "Every individual brings unique value",
                "Success is based on merit and dedication",
                "Opportunities are open to all qualified professionals"
            ]
        }

    def detect_bias(self, text: str) -> Tuple[bool, Dict[str, List[str]], List[str]]:
        """
        Detect different types of bias in the given text.
        Returns: (has_bias, found_biases, suggestions)
        """
        found_biases = {}
        suggestions = []
        has_bias = False

        for bias_type, patterns in self.bias_patterns.items():
            matches = []
            for pattern in patterns:
                found = re.finditer(pattern, text.lower())
                matches.extend([match.group() for match in found])
            
            if matches:
                has_bias = True
                found_biases[bias_type] = matches
                suggestions.extend(self.positive_alternatives[bias_type])

        return has_bias, found_biases, list(set(suggestions))

    def get_corrected_text(self, text: str) -> str:
        """
        Return bias-corrected version of the text with suggestions.
        """
        has_bias, biases, suggestions = self.detect_bias(text)
        
        if not has_bias:
            return text

        corrected_text = text
        for bias_type, matches in biases.items():
            for match in matches:
                if suggestions:
                    corrected_text = corrected_text.replace(
                        match, 
                        f"{suggestions[0]} ({match} was flagged as potentially biased)"
                    )

        return corrected_text
