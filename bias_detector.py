from typing import Dict, List, Optional
import logging
from enum import Enum
import re
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BiasType(Enum):
    GENDER = "gender"
    RACE = "race"
    AGE = "age"
    RELIGION = "religion"
    DISABILITY = "disability"
    CULTURAL = "cultural"
    SOCIOECONOMIC = "socioeconomic"
    OTHER = "other"

class BiasSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class BiasIncident:
    def __init__(self, bias_type: BiasType, severity: BiasSeverity, text: str, context: Dict):
        self.bias_type = bias_type
        self.severity = severity
        self.text = text
        self.context = context
        self.timestamp = datetime.now()
        self.mitigation_actions = []

    def add_mitigation_action(self, action: str):
        self.mitigation_actions.append(action)

    def to_dict(self) -> Dict:
        return {
            "bias_type": self.bias_type.value,
            "severity": self.severity.value,
            "text": self.text,
            "context": self.context,
            "timestamp": self.timestamp.isoformat(),
            "mitigation_actions": self.mitigation_actions
        }

class BiasDetector:
    def __init__(self):
        # Initialize bias detection patterns
        self.bias_patterns = {
            BiasType.GENDER: [
                r'\b(he|she|him|her|his|hers)\b',
                r'\b(man|woman|boy|girl)\b',
                r'\b(male|female)\b',
                r'\b(gentleman|lady)\b'
            ],
            BiasType.AGE: [
                r'\b(old|young|elderly|senior|junior)\b',
                r'\b(age|aged)\b',
                r'\b(millennial|gen z|boomer)\b'
            ],
            BiasType.RACE: [
                r'\b(black|white|asian|hispanic)\b',
                r'\b(race|racial)\b',
                r'\b(ethnicity|ethnic)\b'
            ],
            BiasType.RELIGION: [
                r'\b(christian|muslim|hindu|jew|buddhist)\b',
                r'\b(religion|religious)\b',
                r'\b(faith|belief)\b'
            ],
            BiasType.DISABILITY: [
                r'\b(disabled|handicapped|impaired)\b',
                r'\b(able-bodied|normal)\b',
                r'\b(special needs)\b'
            ]
        }

        # Initialize severity thresholds
        self.severity_thresholds = {
            BiasSeverity.LOW: 1,
            BiasSeverity.MEDIUM: 3,
            BiasSeverity.HIGH: 5,
            BiasSeverity.CRITICAL: 7
        }

    def detect_bias(self, text: str, context: Optional[Dict] = None) -> List[BiasIncident]:
        """
        Detect potential bias in the given text.
        
        Args:
            text: The text to analyze
            context: Optional context information
            
        Returns:
            List of BiasIncident objects
        """
        incidents = []
        context = context or {}

        for bias_type, patterns in self.bias_patterns.items():
            matches = []
            for pattern in patterns:
                matches.extend(re.finditer(pattern, text.lower()))

            if matches:
                severity = self._determine_severity(len(matches))
                incident = BiasIncident(
                    bias_type=bias_type,
                    severity=severity,
                    text=text,
                    context=context
                )
                incidents.append(incident)

        return incidents

    def _determine_severity(self, match_count: int) -> BiasSeverity:
        """
        Determine the severity level based on the number of matches.
        """
        if match_count >= self.severity_thresholds[BiasSeverity.CRITICAL]:
            return BiasSeverity.CRITICAL
        elif match_count >= self.severity_thresholds[BiasSeverity.HIGH]:
            return BiasSeverity.HIGH
        elif match_count >= self.severity_thresholds[BiasSeverity.MEDIUM]:
            return BiasSeverity.MEDIUM
        else:
            return BiasSeverity.LOW

    def get_mitigation_suggestions(self, incident: BiasIncident) -> List[str]:
        """
        Get suggestions for mitigating the detected bias.
        """
        suggestions = []
        
        if incident.bias_type == BiasType.GENDER:
            suggestions.extend([
                "Use gender-neutral language",
                "Consider using 'they/them' pronouns",
                "Focus on skills and qualifications rather than gender"
            ])
        elif incident.bias_type == BiasType.AGE:
            suggestions.extend([
                "Avoid age-related terms",
                "Focus on experience and capabilities",
                "Use inclusive language for all age groups"
            ])
        elif incident.bias_type == BiasType.RACE:
            suggestions.extend([
                "Use race-neutral language",
                "Focus on individual qualifications",
                "Avoid racial stereotypes"
            ])
        elif incident.bias_type == BiasType.RELIGION:
            suggestions.extend([
                "Use religion-neutral language",
                "Focus on universal values",
                "Avoid religious assumptions"
            ])
        elif incident.bias_type == BiasType.DISABILITY:
            suggestions.extend([
                "Use person-first language",
                "Focus on abilities rather than limitations",
                "Avoid ableist language"
            ])

        return suggestions

    def log_incident(self, incident: BiasIncident):
        """
        Log the bias incident for monitoring and analysis.
        """
        logger.warning(f"Bias incident detected: {incident.to_dict()}") 