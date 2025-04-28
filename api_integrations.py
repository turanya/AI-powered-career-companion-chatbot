import requests
import time
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from functools import wraps
import backoff
from ratelimit import limits, sleep_and_retry


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    base_url: str
    api_key: str
    rate_limit: int  # requests per minute
    retry_attempts: int
    timeout: int
    headers: Dict[str, str]

class RateLimiter:
    def __init__(self, calls: int, period: int):
        self.calls = calls
        self.period = period
        self.timestamps = []

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            now = time.time()
            # Remove timestamps older than the period
            self.timestamps = [ts for ts in self.timestamps if now - ts < self.period]
            
            if len(self.timestamps) >= self.calls:
                sleep_time = self.period - (now - self.timestamps[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self.timestamps = self.timestamps[1:]
            
            self.timestamps.append(now)
            return func(*args, **kwargs)
        return wrapper

class BaseAPIIntegration:
    def __init__(self, config: APIConfig):
        self.config = config
        self.rate_limiter = RateLimiter(config.rate_limit, 60)  # 60 seconds
        self.session = requests.Session()
        self.session.headers.update(config.headers)
        self.session.headers.update({'Authorization': f'Bearer {config.api_key}'})

    @sleep_and_retry
    @limits(calls=30, period=60)  # 30 calls per minute
    @backoff.on_exception(backoff.expo, 
                         (requests.exceptions.RequestException, 
                          requests.exceptions.Timeout),
                         max_tries=3)
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make an API request with rate limiting and retry logic"""
        try:
            url = f"{self.config.base_url}{endpoint}"
            response = self.session.request(
                method=method,
                url=url,
                params=params,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise

class JobAPIIntegration(BaseAPIIntegration):
    def __init__(self, config: APIConfig):
        super().__init__(config)

    def get_job_listings(self, 
                        query: Optional[str] = None,
                        location: Optional[str] = None,
                        job_type: Optional[str] = None,
                        experience_level: Optional[str] = None,
                        page: int = 1,
                        page_size: int = 10) -> Dict:
        """Get job listings with filters"""
        params = {
            'q': query,
            'location': location,
            'job_type': job_type,
            'experience_level': experience_level,
            'page': page,
            'page_size': page_size
        }
        # Remove None values
        params = {k: v for k, v in params.items() if v is not None}
        
        return self._make_request('GET', '/jobs', params=params)

    def get_job_details(self, job_id: str) -> Dict:
        """Get detailed information about a specific job"""
        return self._make_request('GET', f'/jobs/{job_id}')

    def search_jobs_by_company(self, company_name: str) -> Dict:
        """Search for jobs by company name"""
        return self._make_request('GET', '/jobs/search', params={'company': company_name})

class EventAPIIntegration(BaseAPIIntegration):
    def get_events(self, filters: Optional[Dict] = None) -> Dict:
        """Get events with optional filters"""
        return self._make_request('GET', '/events', params=filters)

    def get_event_details(self, event_id: str) -> Dict:
        """Get detailed information about a specific event"""
        return self._make_request('GET', f'/events/{event_id}')

    def register_for_event(self, event_id: str, user_data: Dict) -> Dict:
        """Register a user for an event"""
        return self._make_request('POST', f'/events/{event_id}/register', params=user_data)

class ProfessionalDevelopmentAPIIntegration(BaseAPIIntegration):
    def get_programs(self, filters: Optional[Dict] = None) -> Dict:
        """Get professional development programs with optional filters"""
        return self._make_request('GET', '/programs', params=filters)

    def get_program_details(self, program_id: str) -> Dict:
        """Get detailed information about a specific program"""
        return self._make_request('GET', f'/programs/{program_id}')

    def enroll_in_program(self, program_id: str, user_data: Dict) -> Dict:
        """Enroll a user in a program"""
        return self._make_request('POST', f'/programs/{program_id}/enroll', params=user_data)

class BaseAggregator:
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self.cache:
            return False
        cache_time, _ = self.cache[cache_key]
        return (datetime.now() - cache_time).total_seconds() < self.cache_ttl

    def _get_cached_data(self, cache_key: str) -> Optional[Dict]:
        """Get data from cache if valid"""
        if self._is_cache_valid(cache_key):
            _, data = self.cache[cache_key]
            return data
        return None

    def _update_cache(self, cache_key: str, data: Dict):
        """Update cache with new data"""
        self.cache[cache_key] = (datetime.now(), data)

class JobAPIAggregator(BaseAggregator):
    def __init__(self, api_configs: List[APIConfig]):
        super().__init__()
        self.apis = [JobAPIIntegration(config) for config in api_configs]

    def get_job_listings(self, 
                        query: Optional[str] = None,
                        location: Optional[str] = None,
                        job_type: Optional[str] = None,
                        experience_level: Optional[str] = None,
                        page: int = 1,
                        page_size: int = 10) -> Dict:
        """Aggregate job listings from multiple APIs"""
        cache_key = f"jobs_{query}_{location}_{job_type}_{experience_level}_{page}_{page_size}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        all_jobs = []
        for api in self.apis:
            try:
                jobs = api.get_job_listings(
                    query=query,
                    location=location,
                    job_type=job_type,
                    experience_level=experience_level,
                    page=page,
                    page_size=page_size
                )
                all_jobs.extend(jobs.get('results', []))
            except Exception as e:
                logger.error(f"Error fetching jobs from API: {str(e)}")
                continue

        # Remove duplicates based on job ID
        unique_jobs = {job['id']: job for job in all_jobs}.values()
        
        result = {
            'total': len(unique_jobs),
            'page': page,
            'page_size': page_size,
            'results': list(unique_jobs)
        }
        
        self._update_cache(cache_key, result)
        return result

    def get_job_details(self, job_id: str) -> Dict:
        """Get job details from multiple APIs"""
        cache_key = f"job_details_{job_id}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        for api in self.apis:
            try:
                job_details = api.get_job_details(job_id)
                if job_details:
                    self._update_cache(cache_key, job_details)
                    return job_details
            except Exception as e:
                logger.error(f"Error fetching job details from API: {str(e)}")
                continue

        return {'error': 'Job details not found'}

    def search_jobs_by_company(self, company_name: str) -> Dict:
        """Search for jobs by company name across multiple APIs"""
        cache_key = f"company_jobs_{company_name}"
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data

        all_jobs = []
        for api in self.apis:
            try:
                jobs = api.search_jobs_by_company(company_name)
                all_jobs.extend(jobs.get('results', []))
            except Exception as e:
                logger.error(f"Error searching company jobs from API: {str(e)}")
                continue

        # Remove duplicates based on job ID
        unique_jobs = {job['id']: job for job in all_jobs}.values()
        
        result = {
            'company': company_name,
            'total': len(unique_jobs),
            'results': list(unique_jobs)
        }
        
        self._update_cache(cache_key, result)
        return result 