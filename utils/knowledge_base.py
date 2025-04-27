import json
import csv
from datetime import datetime
from typing import Dict, List, Optional
import pandas as pd
from pathlib import Path

class KnowledgeBase:
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.last_update = {}
        
    def _needs_update(self, key: str) -> bool:
        """Check if the cache needs updating."""
        if key not in self.last_update:
            return True
        return (datetime.now() - self.last_update[key]).seconds > self.cache_ttl

    def get_job_listings(self, filters: Optional[Dict] = None) -> List[Dict]:
        """Get job listings with optional filters."""
        if self._needs_update('jobs'):
            try:
                jobs_df = pd.read_csv(self.data_dir / 'job_listing_data.csv')
                jobs_list = jobs_df.fillna('').to_dict('records')
                # Clean up the data
                cleaned_jobs = []
                for job in jobs_list:
                    cleaned_job = {
                        'title': job.get('title', ''),
                        'company': job.get('company', ''),
                        'location': job.get('location', ''),
                        'salary': job.get('salary', 'Competitive'),
                        'type': job.get('type', 'Full-time'),
                        'benefits': job.get('benefits', '').split(',') if job.get('benefits') else []
                    }
                    cleaned_jobs.append(cleaned_job)
                self.cache['jobs'] = cleaned_jobs
                self.last_update['jobs'] = datetime.now()
            except Exception as e:
                print(f"Error loading job listings: {e}")
                # Return mock data if file read fails
                self.cache['jobs'] = [
                    {
                        'title': 'Senior Software Engineer',
                        'company': 'TechCo',
                        'location': 'Bangalore',
                        'salary': 'Competitive',
                        'type': 'Full-time',
                        'benefits': ['Health insurance', 'Flexible hours']
                    },
                    {
                        'title': 'Product Manager',
                        'company': 'InnovateX',
                        'location': 'Mumbai',
                        'salary': 'Competitive',
                        'type': 'Full-time',
                        'benefits': ['401k', 'Health coverage']
                    },
                    {
                        'title': 'Data Scientist',
                        'company': 'DataTech',
                        'location': 'Delhi',
                        'salary': 'Competitive',
                        'type': 'Remote',
                        'benefits': ['Remote work', 'Stock options']
                    }
                ]
                self.last_update['jobs'] = datetime.now()

        jobs = self.cache.get('jobs', [])
        
        if filters:
            filtered_jobs = []
            for job in jobs:
                if all(job.get(k) == v for k, v in filters.items()):
                    filtered_jobs.append(job)
            return filtered_jobs
        return jobs

    def get_events(self) -> List[Dict]:
        """Get upcoming events."""
        if self._needs_update('events'):
            try:
                with open(self.data_dir / 'session_details.json', 'r') as f:
                    data = json.load(f)
                    self.cache['events'] = data.get('events', [])
                    self.last_update['events'] = datetime.now()
            except Exception as e:
                print(f"Error loading events: {e}")
                # Return mock data if file read fails
                self.cache['events'] = [
                    {
                        'title': 'Women in Tech Leadership Summit',
                        'date': '2025-05-15',
                        'location': 'Bangalore',
                        'type': 'Conference'
                    },
                    {
                        'title': 'Career Development Workshop',
                        'date': '2025-05-20',
                        'location': 'Virtual',
                        'type': 'Workshop'
                    },
                    {
                        'title': 'Tech Skills Bootcamp',
                        'date': '2025-06-01',
                        'location': 'Mumbai',
                        'type': 'Training'
                    }
                ]
                self.last_update['events'] = datetime.now()
        return self.cache.get('events', [])

    def get_mentorship_programs(self) -> List[Dict]:
        """Get available mentorship programs."""
        if self._needs_update('mentorship'):
            try:
                with open(self.data_dir / 'session_details.json', 'r') as f:
                    data = json.load(f)
                    self.cache['mentorship'] = data.get('mentorship_programs', [])
                    self.last_update['mentorship'] = datetime.now()
            except Exception as e:
                print(f"Error loading mentorship programs: {e}")
                # Return mock data if file read fails
                self.cache['mentorship'] = [
                    {
                        'name': 'Sarah Johnson',
                        'expertise': 'Tech Leadership',
                        'experience': 15,
                        'background': 'Former CTO at TechCorp'
                    },
                    {
                        'name': 'Priya Sharma',
                        'expertise': 'Product Management',
                        'experience': 10,
                        'background': 'Senior PM at InnovateX'
                    },
                    {
                        'name': 'Lisa Chen',
                        'expertise': 'Data Science',
                        'experience': 8,
                        'background': 'Lead Data Scientist at DataTech'
                    }
                ]
                self.last_update['mentorship'] = datetime.now()
        return self.cache.get('mentorship', [])
