import time
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import statistics
import json
import os
from dataclasses import dataclass
from enum import Enum

class MetricType(Enum):
    RESPONSE_TIME = "response_time"
    ACCURACY = "accuracy"
    USER_SATISFACTION = "user_satisfaction"
    ERROR_RATE = "error_rate"
    CACHE_HIT_RATE = "cache_hit_rate"
    INTENT_DETECTION = "intent_detection"
    ENTITY_EXTRACTION = "entity_extraction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"

@dataclass
class PerformanceMetric:
    metric_type: MetricType
    value: float
    timestamp: datetime
    context: Dict[str, Any]

class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetric]] = {}
        self.ab_tests: Dict[str, Dict] = {}
        self.benchmarks: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize metrics storage
        for metric_type in MetricType:
            self.metrics[metric_type.value] = []
        
        # Load existing benchmarks if available
        self._load_benchmarks()
    
    def _load_benchmarks(self):
        """Load performance benchmarks from file"""
        try:
            if os.path.exists('data/benchmarks.json'):
                with open('data/benchmarks.json', 'r') as f:
                    self.benchmarks = json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading benchmarks: {str(e)}")
    
    def _save_benchmarks(self):
        """Save performance benchmarks to file"""
        try:
            os.makedirs('data', exist_ok=True)
            with open('data/benchmarks.json', 'w') as f:
                json.dump(self.benchmarks, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving benchmarks: {str(e)}")
    
    def record_metric(self, metric_type: MetricType, value: float, context: Optional[Dict] = None):
        """Record a performance metric"""
        metric = PerformanceMetric(
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            context=context or {}
        )
        self.metrics[metric_type.value].append(metric)
        self._check_benchmarks(metric)
    
    def _check_benchmarks(self, metric: PerformanceMetric):
        """Check if metric meets benchmark standards"""
        if metric.metric_type.value not in self.benchmarks:
            return
        
        benchmark = self.benchmarks[metric.metric_type.value]
        if metric.value < benchmark.get('min', float('-inf')) or metric.value > benchmark.get('max', float('inf')):
            self.logger.warning(
                f"Performance alert: {metric.metric_type.value} = {metric.value} "
                f"outside benchmark range [{benchmark.get('min')}, {benchmark.get('max')}]"
            )
    
    def start_ab_test(self, test_name: str, variants: List[Dict], metric_type: MetricType):
        """Start a new A/B test"""
        self.ab_tests[test_name] = {
            'variants': variants,
            'metric_type': metric_type.value,
            'start_time': datetime.now(),
            'results': {variant['name']: [] for variant in variants}
        }
    
    def record_ab_test_result(self, test_name: str, variant_name: str, value: float):
        """Record a result for an A/B test variant"""
        if test_name in self.ab_tests:
            self.ab_tests[test_name]['results'][variant_name].append(value)
    
    def get_ab_test_results(self, test_name: str) -> Optional[Dict]:
        """Get results of an A/B test"""
        if test_name not in self.ab_tests:
            return None
        
        test = self.ab_tests[test_name]
        results = {}
        
        for variant_name, values in test['results'].items():
            if values:
                results[variant_name] = {
                    'mean': statistics.mean(values),
                    'median': statistics.median(values),
                    'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
                    'count': len(values)
                }
        
        return results
    
    def set_benchmark(self, metric_type: MetricType, min_value: float, max_value: float):
        """Set performance benchmarks for a metric type"""
        self.benchmarks[metric_type.value] = {
            'min': min_value,
            'max': max_value,
            'last_updated': datetime.now().isoformat()
        }
        self._save_benchmarks()
    
    def get_metrics_summary(self, metric_type: Optional[MetricType] = None) -> Dict:
        """Get summary statistics for metrics"""
        if metric_type:
            metrics = self.metrics[metric_type.value]
        else:
            metrics = [m for metrics_list in self.metrics.values() for m in metrics_list]
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        return {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'std_dev': statistics.stdev(values) if len(values) > 1 else 0,
            'min': min(values),
            'max': max(values),
            'count': len(values)
        }
    
    def get_performance_report(self) -> Dict:
        """Generate a comprehensive performance report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'ab_tests': {},
            'benchmarks': self.benchmarks
        }
        
        # Add metric summaries
        for metric_type in MetricType:
            report['metrics'][metric_type.value] = self.get_metrics_summary(metric_type)
        
        # Add A/B test results
        for test_name in self.ab_tests:
            report['ab_tests'][test_name] = self.get_ab_test_results(test_name)
        
        return report
    
    def export_report(self, filename: str = 'performance_report.json'):
        """Export performance report to file"""
        try:
            os.makedirs('reports', exist_ok=True)
            with open(f'reports/{filename}', 'w') as f:
                json.dump(self.get_performance_report(), f, indent=2)
        except Exception as e:
            self.logger.error(f"Error exporting performance report: {str(e)}")
    
    def clear_metrics(self, metric_type: Optional[MetricType] = None):
        """Clear recorded metrics"""
        if metric_type:
            self.metrics[metric_type.value] = []
        else:
            for metric_type in MetricType:
                self.metrics[metric_type.value] = [] 