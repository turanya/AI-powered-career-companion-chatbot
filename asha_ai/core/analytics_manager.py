from typing import Dict, List, Optional
import json
from datetime import datetime
import pandas as pd
from pathlib import Path

class AnalyticsManager:
    def __init__(self):
        self.metrics: Dict = {
            "user_interactions": [],
            "response_times": [],
            "error_rates": [],
            "bias_incidents": [],
            "user_feedback": []
        }
        self.analytics_path = Path("analytics")
        self.analytics_path.mkdir(exist_ok=True)
        
    def track_interaction(self, user_input: str, response: str, duration: float) -> None:
        """Track user interaction metrics."""
        self.metrics["user_interactions"].append({
            "timestamp": datetime.now().isoformat(),
            "input": user_input,
            "response": response,
            "duration": duration
        })
        
    def track_error(self, error_type: str, details: str) -> None:
        """Track error occurrences."""
        self.metrics["error_rates"].append({
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "details": details
        })
        
    def track_bias_incident(self, text: str, bias_type: str, confidence: float) -> None:
        """Track detected bias incidents."""
        self.metrics["bias_incidents"].append({
            "timestamp": datetime.now().isoformat(),
            "text": text,
            "bias_type": bias_type,
            "confidence": confidence
        })
        
    def track_feedback(self, response_id: str, rating: int, comments: str = None) -> None:
        """Track user feedback."""
        self.metrics["user_feedback"].append({
            "timestamp": datetime.now().isoformat(),
            "response_id": response_id,
            "rating": rating,
            "comments": comments
        })
        
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics."""
        if not self.metrics["user_interactions"]:
            return {}
            
        df = pd.DataFrame(self.metrics["user_interactions"])
        return {
            "avg_response_time": df["duration"].mean(),
            "total_interactions": len(df),
            "error_rate": len(self.metrics["error_rates"]) / len(df) if len(df) > 0 else 0,
            "bias_incidents": len(self.metrics["bias_incidents"]),
            "avg_feedback_rating": pd.DataFrame(self.metrics["user_feedback"])["rating"].mean() if self.metrics["user_feedback"] else 0
        }
        
    def save_analytics(self) -> None:
        """Save analytics data to files."""
        timestamp = datetime.now().strftime("%Y%m%d")
        for metric_type, data in self.metrics.items():
            if data:
                filename = self.analytics_path / f"{metric_type}_{timestamp}.json"
                with open(filename, 'w') as f:
                    json.dump(data, f)
                    
    def load_analytics(self, date: str = None) -> Dict:
        """Load analytics data from files."""
        if not date:
            date = datetime.now().strftime("%Y%m%d")
            
        loaded_metrics = {}
        for metric_type in self.metrics.keys():
            filename = self.analytics_path / f"{metric_type}_{date}.json"
            if filename.exists():
                with open(filename, 'r') as f:
                    loaded_metrics[metric_type] = json.load(f)
                    
        return loaded_metrics 