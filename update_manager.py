import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from cachetools import TTLCache, LRUCache
import hashlib
from pydantic import BaseModel, validator
import requests
from threading import Thread
import time
import queue

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataUpdate(BaseModel):
    """Data model for updates with validation"""
    type: str
    data: Dict[str, Any]
    timestamp: datetime
    source: str
    version: str

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['job', 'event', 'mentorship', 'resource', 'profile']
        if v not in valid_types:
            raise ValueError(f'Invalid update type. Must be one of {valid_types}')
        return v

    @validator('timestamp')
    def validate_timestamp(cls, v):
        if v > datetime.now() + timedelta(minutes=5):
            raise ValueError('Timestamp cannot be in the future')
        return v

class UpdateManager:
    def __init__(self):
        # Initialize caches with different strategies
        self.ttl_cache = TTLCache(maxsize=1000, ttl=3600)  # 1 hour TTL
        self.lru_cache = LRUCache(maxsize=500)  # Keep 500 most recent items
        
        # Webhook configuration
        self.webhooks: Dict[str, List[str]] = {
            'job': [],
            'event': [],
            'mentorship': [],
            'resource': [],
            'profile': []
        }
        
        # Update queue for processing
        self.update_queue = queue.Queue()
        
        # Start update processor thread
        self.processor_thread = Thread(target=self._process_updates, daemon=True)
        self.processor_thread.start()
        
        # Data validation rules
        self.validation_rules = {
            'job': self._validate_job,
            'event': self._validate_event,
            'mentorship': self._validate_mentorship,
            'resource': self._validate_resource,
            'profile': self._validate_profile
        }

    def _validate_job(self, data: Dict[str, Any]) -> bool:
        required_fields = ['title', 'company', 'location', 'description']
        return all(field in data for field in required_fields)

    def _validate_event(self, data: Dict[str, Any]) -> bool:
        required_fields = ['title', 'date', 'location', 'description']
        return all(field in data for field in required_fields)

    def _validate_mentorship(self, data: Dict[str, Any]) -> bool:
        required_fields = ['mentor_name', 'expertise', 'availability']
        return all(field in data for field in required_fields)

    def _validate_resource(self, data: Dict[str, Any]) -> bool:
        required_fields = ['title', 'type', 'url']
        return all(field in data for field in required_fields)

    def _validate_profile(self, data: Dict[str, Any]) -> bool:
        required_fields = ['user_id', 'name', 'email']
        return all(field in data for field in required_fields)

    def register_webhook(self, update_type: str, url: str) -> bool:
        """Register a webhook URL for specific update types"""
        if update_type not in self.webhooks:
            logger.error(f"Invalid update type: {update_type}")
            return False
        
        if url not in self.webhooks[update_type]:
            self.webhooks[update_type].append(url)
            logger.info(f"Registered webhook for {update_type} updates: {url}")
            return True
        return False

    def unregister_webhook(self, update_type: str, url: str) -> bool:
        """Unregister a webhook URL"""
        if update_type in self.webhooks and url in self.webhooks[update_type]:
            self.webhooks[update_type].remove(url)
            logger.info(f"Unregistered webhook for {update_type} updates: {url}")
            return True
        return False

    def _notify_webhooks(self, update: DataUpdate):
        """Notify all registered webhooks about the update"""
        if update.type not in self.webhooks:
            return

        for url in self.webhooks[update.type]:
            try:
                response = requests.post(
                    url,
                    json=update.dict(),
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                response.raise_for_status()
                logger.info(f"Successfully notified webhook: {url}")
            except Exception as e:
                logger.error(f"Failed to notify webhook {url}: {str(e)}")

    def _generate_cache_key(self, data_type: str, data: Dict[str, Any]) -> str:
        """Generate a unique cache key based on data type and content"""
        content = json.dumps(data, sort_keys=True)
        return f"{data_type}:{hashlib.md5(content.encode()).hexdigest()}"

    def cache_data(self, data_type: str, data: Dict[str, Any], ttl: int = 3600):
        """Cache data with both TTL and LRU strategies"""
        cache_key = self._generate_cache_key(data_type, data)
        
        # Store in TTL cache
        self.ttl_cache[cache_key] = {
            'data': data,
            'timestamp': datetime.now(),
            'ttl': ttl
        }
        
        # Store in LRU cache
        self.lru_cache[cache_key] = data
        
        logger.info(f"Cached {data_type} data with key: {cache_key}")

    def get_cached_data(self, data_type: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache using both strategies"""
        cache_key = self._generate_cache_key(data_type, data)
        
        # Try TTL cache first
        if cache_key in self.ttl_cache:
            cached_item = self.ttl_cache[cache_key]
            if datetime.now() - cached_item['timestamp'] < timedelta(seconds=cached_item['ttl']):
                return cached_item['data']
        
        # Fall back to LRU cache
        return self.lru_cache.get(cache_key)

    def queue_update(self, update: DataUpdate):
        """Queue an update for processing"""
        try:
            # Validate the update
            if not self._validate_update(update):
                logger.error(f"Invalid update: {update}")
                return False
            
            # Add to queue
            self.update_queue.put(update)
            logger.info(f"Queued update of type {update.type}")
            return True
        except Exception as e:
            logger.error(f"Error queueing update: {str(e)}")
            return False

    def _validate_update(self, update: DataUpdate) -> bool:
        """Validate update data against rules"""
        if update.type not in self.validation_rules:
            logger.error(f"Unknown update type: {update.type}")
            return False
        
        validator = self.validation_rules[update.type]
        return validator(update.data)

    def _process_updates(self):
        """Process updates from the queue"""
        while True:
            try:
                update = self.update_queue.get()
                
                # Cache the update
                self.cache_data(update.type, update.data)
                
                # Notify webhooks
                self._notify_webhooks(update)
                
                # Mark task as done
                self.update_queue.task_done()
                
                logger.info(f"Processed update of type {update.type}")
                
            except Exception as e:
                logger.error(f"Error processing update: {str(e)}")
                time.sleep(1)  # Prevent tight loop on errors

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about cache usage"""
        return {
            'ttl_cache_size': len(self.ttl_cache),
            'lru_cache_size': len(self.lru_cache),
            'update_queue_size': self.update_queue.qsize()
        }

    def clear_cache(self, cache_type: Optional[str] = None):
        """Clear cache(s)"""
        if cache_type is None or cache_type == 'ttl':
            self.ttl_cache.clear()
        if cache_type is None or cache_type == 'lru':
            self.lru_cache.clear()
 