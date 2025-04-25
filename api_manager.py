import time
import json
import requests
from typing import Dict, List, Optional, Any
from functools import wraps
from datetime import datetime, timedelta
import logging
from cachetools import TTLCache
import backoff

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class APIManager:
    def __init__(self):
        # Initialize cache with 1 hour TTL and max size of 1000 items
        self.cache = TTLCache(maxsize=1000, ttl=3600)
        
        # Rate limiting configuration
        self.rate_limits = {
            'jobs': {'calls': 0, 'last_reset': time.time(), 'limit': 100, 'window': 3600},
            'events': {'calls': 0, 'last_reset': time.time(), 'limit': 50, 'window': 3600},
            'mentorship': {'calls': 0, 'last_reset': time.time(), 'limit': 30, 'window': 3600}
        }
        
        # API endpoints configuration
        self.endpoints = {
            'jobs': 'https://api.jobsforher.com/v1/jobs',
            'events': 'https://api.jobsforher.com/v1/events',
            'mentorship': 'https://api.jobsforher.com/v1/mentorship'
        }
        
        # Error handling configuration
        self.max_retries = 3
        self.retry_delay = 1  # seconds

    def _check_rate_limit(self, api_type: str) -> bool:
        """Check if API call is within rate limits."""
        current_time = time.time()
        limit_info = self.rate_limits[api_type]
        
        # Reset counter if window has passed
        if current_time - limit_info['last_reset'] > limit_info['window']:
            limit_info['calls'] = 0
            limit_info['last_reset'] = current_time
        
        # Check if limit is reached
        if limit_info['calls'] >= limit_info['limit']:
            logger.warning(f"Rate limit reached for {api_type} API")
            return False
        
        limit_info['calls'] += 1
        return True

    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, 
                          requests.exceptions.Timeout),
                         max_tries=3)
    def _make_api_request(self, url: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with retry logic and error handling."""
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error occurred: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error occurred: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error occurred: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error occurred: {e}")
            raise

    def _get_cache_key(self, api_type: str, params: Optional[Dict] = None) -> str:
        """Generate cache key based on API type and parameters."""
        if params:
            return f"{api_type}:{json.dumps(params, sort_keys=True)}"
        return api_type

    def get_jobs(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get job listings with caching and rate limiting."""
        cache_key = self._get_cache_key('jobs', filters)
        
        # Check cache first
        if cache_key in self.cache:
            logger.info("Retrieved jobs from cache")
            return self.cache[cache_key]
        
        # Check rate limit
        if not self._check_rate_limit('jobs'):
            logger.warning("Rate limit reached for jobs API")
            return []
        
        try:
            data = self._make_api_request(self.endpoints['jobs'], filters)
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error fetching jobs: {e}")
            return []

    def get_events(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get events with caching and rate limiting."""
        cache_key = self._get_cache_key('events', filters)
        
        if cache_key in self.cache:
            logger.info("Retrieved events from cache")
            return self.cache[cache_key]
        
        if not self._check_rate_limit('events'):
            logger.warning("Rate limit reached for events API")
            return []
        
        try:
            data = self._make_api_request(self.endpoints['events'], filters)
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            return []

    def get_mentorship_opportunities(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get mentorship opportunities with caching and rate limiting."""
        cache_key = self._get_cache_key('mentorship', filters)
        
        if cache_key in self.cache:
            logger.info("Retrieved mentorship opportunities from cache")
            return self.cache[cache_key]
        
        if not self._check_rate_limit('mentorship'):
            logger.warning("Rate limit reached for mentorship API")
            return []
        
        try:
            data = self._make_api_request(self.endpoints['mentorship'], filters)
            self.cache[cache_key] = data
            return data
        except Exception as e:
            logger.error(f"Error fetching mentorship opportunities: {e}")
            return []

    def clear_cache(self, api_type: Optional[str] = None):
        """Clear cache for specific API type or all caches."""
        if api_type:
            keys_to_remove = [k for k in self.cache.keys() if k.startswith(api_type)]
            for key in keys_to_remove:
                self.cache.pop(key, None)
        else:
            self.cache.clear()
        logger.info(f"Cache cleared for {api_type if api_type else 'all APIs'}")

    def get_rate_limit_status(self) -> Dict[str, Dict]:
        """Get current rate limit status for all APIs."""
        status = {}
        for api_type, limit_info in self.rate_limits.items():
            status[api_type] = {
                'calls': limit_info['calls'],
                'limit': limit_info['limit'],
                'remaining': limit_info['limit'] - limit_info['calls'],
                'reset_in': max(0, limit_info['window'] - (time.time() - limit_info['last_reset']))
            }
        return status 