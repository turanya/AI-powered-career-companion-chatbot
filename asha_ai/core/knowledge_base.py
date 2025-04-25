from typing import Dict, List, Optional
import json
import aiohttp
import pandas as pd
import os
from datetime import datetime, timedelta
from pathlib import Path
import asyncio
from aiohttp import ClientTimeout

class KnowledgeBase:
    def __init__(self):
        self.job_listings: Dict = {}
        self.events: Dict = {}
        self.mentorship_programs: Dict = {}
        self.last_update: datetime = datetime.now()
        self.data_path = Path("data")
        self.data_path.mkdir(exist_ok=True)
        self.cache_ttl = int(os.getenv("CACHE_TTL", 3600))  # 1 hour default
        
        # Initialize with mock data
        self._initialize_mock_data()
        
    def _initialize_mock_data(self):
        """Initialize with mock data for testing."""
        self.job_listings = {
            "1": {
                "title": "Software Engineer",
                "company": "TechWomen Inc.",
                "description": "Looking for talented software engineers with experience in Python and JavaScript",
                "requirements": ["Python", "JavaScript", "SQL", "REST APIs"],
                "location": "Remote",
                "type": "Full-time",
                "flexibility": {"remote_work": True, "flexible_hours": True},
                "benefits": ["health_insurance", "parental_leave", "flexible_hours", "learning_budget"],
                "women_initiatives": ["mentorship_program", "diversity_training", "women_leadership_program"]
            },
            "2": {
                "title": "Data Scientist",
                "company": "DataForHer",
                "description": "Seeking data scientists to work on machine learning projects",
                "requirements": ["Python", "Machine Learning", "Data Analysis", "Statistics"],
                "location": "Hybrid",
                "type": "Full-time",
                "flexibility": {"remote_work": True, "flexible_hours": True},
                "benefits": ["health_insurance", "parental_leave", "flexible_hours", "wellness_program"],
                "women_initiatives": ["women_in_data_science", "career_development", "flexible_work"]
            }
        }
        
        self.events = {
            "1": {
                "title": "Women in Tech Conference 2024",
                "description": "Annual conference for women in technology featuring workshops and networking",
                "date": (datetime.now() + timedelta(days=30)).isoformat(),
                "category": "Technology",
                "format": "Virtual",
                "speakers": ["Jane Smith", "Sarah Johnson", "Priya Patel"],
                "registration_url": "https://example.com/register"
            },
            "2": {
                "title": "Career Development Workshop",
                "description": "Workshop on resume building and interview preparation",
                "date": (datetime.now() + timedelta(days=15)).isoformat(),
                "category": "Career Development",
                "format": "In-person",
                "speakers": ["Dr. Emily Brown", "Lisa Chen"],
                "registration_url": "https://example.com/workshop"
            }
        }
        
        self.mentorship_programs = {
            "1": {
                "title": "Women Leadership Program",
                "description": "Mentorship program for aspiring women leaders in technology",
                "mentor": "Dr. Emily Brown",
                "expertise_areas": ["leadership", "career_development", "technology"],
                "duration": "6 months",
                "availability": "Virtual"
            },
            "2": {
                "title": "Tech Career Accelerator",
                "description": "Mentorship program focused on technical skills and career growth",
                "mentor": "Sarah Johnson",
                "expertise_areas": ["software_development", "data_science", "career_growth"],
                "duration": "3 months",
                "availability": "Hybrid"
            }
        }
        
    async def update_job_listings(self, api_key: str) -> None:
        """Update job listings from external API."""
        try:
            # For now, just use mock data
            self.job_listings = self._initialize_mock_data().job_listings
        except Exception as e:
            print(f"Using mock job listings data: {e}")
            
    async def update_events(self) -> None:
        """Update events and workshops data."""
        try:
            # For now, just use mock data
            self.events = self._initialize_mock_data().events
        except Exception as e:
            print(f"Using mock events data: {e}")

    async def update_mentorship_programs(self) -> None:
        """Update mentorship programs data."""
        try:
            # For now, just use mock data
            self.mentorship_programs = self._initialize_mock_data().mentorship_programs
        except Exception as e:
            print(f"Using mock mentorship programs data: {e}")
            
    def get_relevant_jobs(self, query: str, filters: Dict = None) -> List[Dict]:
        """Get relevant job listings based on query and filters."""
        matched_jobs = []
        for job in self.job_listings.values():
            if self._match_job(job, query, filters):
                # Enrich job data with women empowerment insights
                job['women_friendly'] = self._check_women_friendly_company(job)
                job['flexibility_score'] = self._calculate_flexibility_score(job)
                matched_jobs.append(job)
        
        return sorted(matched_jobs, key=lambda x: (x['women_friendly'], x['flexibility_score']), reverse=True)
                
    def get_upcoming_events(self, category: str = None) -> List[Dict]:
        """Get upcoming events, optionally filtered by category."""
        now = datetime.now()
        events = [
            event for event in self.events.values()
            if datetime.fromisoformat(event['date']) > now
            and (not category or event['category'].lower() == category.lower())
        ]
        return sorted(events, key=lambda x: datetime.fromisoformat(x['date']))

    def get_mentorship_opportunities(self, expertise: str = None) -> List[Dict]:
        """Get mentorship opportunities, optionally filtered by expertise area."""
        return [
            program for program in self.mentorship_programs.values()
            if not expertise or expertise.lower() in program['expertise_areas']
        ]

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache is still valid based on TTL."""
        if not cache_file.exists():
            return False
        
        cache_age = datetime.now().timestamp() - cache_file.stat().st_mtime
        return cache_age < self.cache_ttl

    async def _fetch_jobs(self, api_key: str) -> Dict:
        """Fetch jobs from JobsForHer API."""
        url = os.getenv("JOBSFORHER_API_URL", "https://api.jobsforher.com/v1/jobs")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        timeout = ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status}")
                    
    async def _fetch_events(self) -> Dict:
        """Fetch events from events API."""
        url = os.getenv("EVENTS_API_URL", "https://api.jobsforher.com/v1/events")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status}")

    async def _fetch_mentorship_programs(self) -> Dict:
        """Fetch mentorship programs."""
        url = os.getenv("MENTORSHIP_API_URL", "https://api.jobsforher.com/v1/mentorship")
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise Exception(f"API Error: {response.status}")

    def _process_job_listings(self, data: Dict) -> Dict:
        """Process and structure job listings data."""
        processed = {}
        for job in data.get('jobs', []):
            job_id = job.get('id')
            if job_id:
                processed[job_id] = {
                    'title': job.get('title'),
                    'company': job.get('company'),
                    'description': job.get('description'),
                    'requirements': job.get('requirements', []),
                    'location': job.get('location'),
                    'type': job.get('type'),
                    'flexibility': job.get('flexibility', {}),
                    'benefits': job.get('benefits', []),
                    'posted_date': job.get('posted_date'),
                    'women_initiatives': job.get('women_initiatives', [])
                }
        return processed

    def _process_events(self, data: Dict) -> Dict:
        """Process and structure events data."""
        processed = {}
        for event in data.get('events', []):
            event_id = event.get('id')
            if event_id:
                processed[event_id] = {
                    'title': event.get('title'),
                    'description': event.get('description'),
                    'date': event.get('date'),
                    'category': event.get('category'),
                    'format': event.get('format'),
                    'speakers': event.get('speakers', []),
                    'registration_url': event.get('registration_url')
                }
        return processed

    def _process_mentorship_programs(self, data: Dict) -> Dict:
        """Process and structure mentorship programs data."""
        processed = {}
        for program in data.get('programs', []):
            program_id = program.get('id')
            if program_id:
                processed[program_id] = {
                    'title': program.get('title'),
                    'description': program.get('description'),
                    'mentor': program.get('mentor'),
                    'expertise_areas': program.get('expertise_areas', []),
                    'duration': program.get('duration'),
                    'availability': program.get('availability')
                }
        return processed

    def _check_women_friendly_company(self, job: Dict) -> bool:
        """Check if company has women-friendly policies."""
        indicators = [
            'flexible_hours' in job.get('benefits', []),
            'parental_leave' in job.get('benefits', []),
            'remote_work' in job.get('benefits', []),
            bool(job.get('women_initiatives')),
            'diversity_program' in job.get('benefits', [])
        ]
        return sum(indicators) >= 3

    def _calculate_flexibility_score(self, job: Dict) -> float:
        """Calculate job flexibility score."""
        score = 0.0
        flexibility = job.get('flexibility', {})
        
        if flexibility.get('remote_work'):
            score += 0.4
        if flexibility.get('flexible_hours'):
            score += 0.3
        if flexibility.get('part_time_option'):
            score += 0.2
        if 'work_life_balance' in job.get('benefits', []):
            score += 0.1
            
        return score

    def _match_job(self, job: Dict, query: str, filters: Dict = None) -> bool:
        """Check if job matches search criteria."""
        if not filters:
            filters = {}
            
        # Basic text matching
        query_lower = query.lower()
        text_match = (
            query_lower in job['title'].lower() or
            query_lower in job['description'].lower() or
            any(query_lower in req.lower() for req in job['requirements'])
        )
        
        # Apply filters
        filter_match = all(
            str(job.get(key, '')).lower() == str(value).lower()
            for key, value in filters.items()
        )
        
        return text_match and filter_match

    def _save_to_cache(self, filename: str, data: Dict) -> None:
        """Save data to cache file."""
        cache_file = self.data_path / filename
        with open(cache_file, 'w') as f:
            json.dump(data, f)
            
    def _load_from_cache(self, filename: str) -> Dict:
        """Load data from cache file."""
        cache_file = self.data_path / filename
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                return json.load(f)
        return {} 