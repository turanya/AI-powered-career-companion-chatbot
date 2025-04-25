from typing import Dict, List, Optional
import json
from datetime import datetime
from pathlib import Path
import pandas as pd
from enum import Enum

class FeedbackType(Enum):
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    BIAS = "bias"
    GENERAL = "general"

class FeedbackManager:
    def __init__(self):
        self.feedback_path = Path("feedback")
        self.feedback_path.mkdir(exist_ok=True)
        self.feedback_data: Dict[str, List] = {
            "responses": [],
            "bias_reports": [],
            "improvement_suggestions": []
        }
        
    def collect_response_feedback(self, response_id: str, rating: int, 
                                feedback_type: FeedbackType, comments: str = None) -> None:
        """Collect feedback for a specific response."""
        self.feedback_data["responses"].append({
            "timestamp": datetime.now().isoformat(),
            "response_id": response_id,
            "rating": rating,
            "type": feedback_type.value,
            "comments": comments
        })
        self._save_feedback()
        
    def report_bias(self, text: str, context: str, reporter_comments: str = None) -> None:
        """Report biased content for review."""
        self.feedback_data["bias_reports"].append({
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "context": context,
            "reporter_comments": reporter_comments,
            "status": "pending_review"
        })
        self._save_feedback()
        
    def suggest_improvement(self, category: str, suggestion: str, context: Dict = None) -> None:
        """Submit improvement suggestion."""
        self.feedback_data["improvement_suggestions"].append({
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "suggestion": suggestion,
            "context": context or {},
            "status": "under_review"
        })
        self._save_feedback()
        
    def get_feedback_summary(self) -> Dict:
        """Generate summary of feedback data."""
        if not any(self.feedback_data.values()):
            return {}
            
        response_df = pd.DataFrame(self.feedback_data["responses"])
        bias_df = pd.DataFrame(self.feedback_data["bias_reports"])
        
        summary = {
            "average_rating": response_df["rating"].mean() if not response_df.empty else 0,
            "feedback_count": len(response_df),
            "bias_reports_count": len(bias_df),
            "improvement_suggestions": len(self.feedback_data["improvement_suggestions"]),
            "feedback_by_type": response_df["type"].value_counts().to_dict() if not response_df.empty else {},
            "recent_bias_reports": len(bias_df[bias_df["status"] == "pending_review"]) if not bias_df.empty else 0
        }
        
        return summary
        
    def get_learning_insights(self) -> Dict:
        """Generate insights for continuous learning."""
        insights = {
            "common_issues": self._analyze_common_issues(),
            "improvement_areas": self._identify_improvement_areas(),
            "bias_patterns": self._analyze_bias_patterns()
        }
        return insights
        
    def _save_feedback(self) -> None:
        """Save feedback data to file."""
        timestamp = datetime.now().strftime("%Y%m%d")
        feedback_file = self.feedback_path / f"feedback_{timestamp}.json"
        
        with open(feedback_file, 'w') as f:
            json.dump(self.feedback_data, f)
            
    def _analyze_common_issues(self) -> List[Dict]:
        """Analyze common issues from feedback."""
        if not self.feedback_data["responses"]:
            return []
            
        df = pd.DataFrame(self.feedback_data["responses"])
        low_ratings = df[df["rating"] <= 2]
        
        issues = []
        if not low_ratings.empty:
            for feedback_type in FeedbackType:
                type_issues = low_ratings[low_ratings["type"] == feedback_type.value]
                if not type_issues.empty:
                    issues.append({
                        "type": feedback_type.value,
                        "count": len(type_issues),
                        "avg_rating": type_issues["rating"].mean(),
                        "sample_comments": type_issues["comments"].dropna().tolist()[:3]
                    })
                    
        return sorted(issues, key=lambda x: x["count"], reverse=True)
        
    def _identify_improvement_areas(self) -> List[Dict]:
        """Identify areas needing improvement."""
        if not self.feedback_data["improvement_suggestions"]:
            return []
            
        df = pd.DataFrame(self.feedback_data["improvement_suggestions"])
        areas = df["category"].value_counts().to_dict()
        
        return [
            {
                "category": category,
                "suggestion_count": count,
                "recent_suggestions": df[df["category"] == category]["suggestion"].tolist()[:3]
            }
            for category, count in areas.items()
        ]
        
    def _analyze_bias_patterns(self) -> List[Dict]:
        """Analyze patterns in bias reports."""
        if not self.feedback_data["bias_reports"]:
            return []
            
        df = pd.DataFrame(self.feedback_data["bias_reports"])
        return [
            {
                "status": status,
                "count": len(group),
                "recent_reports": group["text"].tolist()[:3]
            }
            for status, group in df.groupby("status")
        ] 