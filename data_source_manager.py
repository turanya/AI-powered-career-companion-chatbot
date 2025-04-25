import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
import requests
from requests.exceptions import RequestException
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import feedparser
import xml.etree.ElementTree as ET
from security import SecurityManager

class DataSourceConfig(BaseModel):
    """Configuration for a data source"""
    name: str
    type: str
    url: str
    api_key: Optional[str] = None
    refresh_interval: int = 300  # seconds
    validation_rules: Dict[str, Any] = {}
    headers: Dict[str, str] = {}
    params: Dict[str, str] = {}
    timeout: int = 30
    retry_attempts: int = 3
    retry_delay: int = 5

    @validator('type')
    def validate_type(cls, v):
        valid_types = ['api', 'rss', 'web_scrape', 'database', 'file']
        if v not in valid_types:
            raise ValueError(f'Invalid data source type. Must be one of {valid_types}')
        return v

class DataValidationRule(BaseModel):
    """Validation rule for data"""
    field: str
    rule_type: str
    parameters: Dict[str, Any]
    error_message: str

class DataSourceManager:
    def __init__(self, security_manager: SecurityManager):
        self.security_manager = security_manager
        self.data_sources: Dict[str, DataSourceConfig] = {}
        self.validation_rules: Dict[str, List[DataValidationRule]] = {}
        self.logger = logging.getLogger(__name__)
        
        # Initialize data source configurations
        self._load_data_sources()
        
        # Initialize validation rules
        self._load_validation_rules()

    def _load_data_sources(self):
        """Load data source configurations"""
        try:
            with open('config/data_sources.json', 'r') as f:
                sources = json.load(f)
                for source in sources:
                    config = DataSourceConfig(**source)
                    self.data_sources[config.name] = config
        except FileNotFoundError:
            self.logger.warning("Data sources configuration file not found")
        except Exception as e:
            self.logger.error(f"Error loading data sources: {str(e)}")

    def _load_validation_rules(self):
        """Load validation rules"""
        try:
            with open('config/validation_rules.json', 'r') as f:
                rules = json.load(f)
                for source_name, source_rules in rules.items():
                    self.validation_rules[source_name] = [
                        DataValidationRule(**rule) for rule in source_rules
                    ]
        except FileNotFoundError:
            self.logger.warning("Validation rules configuration file not found")
        except Exception as e:
            self.logger.error(f"Error loading validation rules: {str(e)}")

    async def fetch_data(self, source_name: str) -> Dict:
        """Fetch data from a source asynchronously"""
        if source_name not in self.data_sources:
            raise ValueError(f"Unknown data source: {source_name}")

        config = self.data_sources[source_name]
        
        try:
            if config.type == 'api':
                return await self._fetch_api_data(config)
            elif config.type == 'rss':
                return await self._fetch_rss_data(config)
            elif config.type == 'web_scrape':
                return await self._fetch_web_data(config)
            elif config.type == 'database':
                return await self._fetch_database_data(config)
            elif config.type == 'file':
                return await self._fetch_file_data(config)
            else:
                raise ValueError(f"Unsupported data source type: {config.type}")
        except Exception as e:
            self.logger.error(f"Error fetching data from {source_name}: {str(e)}")
            raise

    async def _fetch_api_data(self, config: DataSourceConfig) -> Dict:
        """Fetch data from an API"""
        async with aiohttp.ClientSession() as session:
            for attempt in range(config.retry_attempts):
                try:
                    async with session.get(
                        config.url,
                        headers=config.headers,
                        params=config.params,
                        timeout=config.timeout
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            return self._validate_data(config.name, data)
                        else:
                            self.logger.warning(
                                f"API request failed with status {response.status}"
                            )
                except Exception as e:
                    if attempt < config.retry_attempts - 1:
                        await asyncio.sleep(config.retry_delay)
                    else:
                        raise
        return {}

    async def _fetch_rss_data(self, config: DataSourceConfig) -> Dict:
        """Fetch data from an RSS feed"""
        try:
            feed = feedparser.parse(config.url)
            return self._validate_data(config.name, feed.entries)
        except Exception as e:
            self.logger.error(f"Error fetching RSS data: {str(e)}")
            raise

    async def _fetch_web_data(self, config: DataSourceConfig) -> Dict:
        """Fetch data by web scraping"""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    config.url,
                    headers=config.headers,
                    timeout=config.timeout
                ) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        # Implement specific scraping logic based on config
                        return self._validate_data(config.name, {})
            except Exception as e:
                self.logger.error(f"Error scraping web data: {str(e)}")
                raise

    async def _fetch_database_data(self, config: DataSourceConfig) -> Dict:
        """Fetch data from a database"""
        # Implement database connection and query logic
        return {}

    async def _fetch_file_data(self, config: DataSourceConfig) -> Dict:
        """Fetch data from a file"""
        try:
            with open(config.url, 'r') as f:
                data = json.load(f)
                return self._validate_data(config.name, data)
        except Exception as e:
            self.logger.error(f"Error reading file data: {str(e)}")
            raise

    def _validate_data(self, source_name: str, data: Any) -> Dict:
        """Validate data against configured rules"""
        if source_name not in self.validation_rules:
            return data

        validated_data = {}
        rules = self.validation_rules[source_name]

        for rule in rules:
            try:
                if rule.rule_type == 'required':
                    if rule.field not in data:
                        raise ValueError(rule.error_message)
                elif rule.rule_type == 'type':
                    if not isinstance(data.get(rule.field), eval(rule.parameters['type'])):
                        raise ValueError(rule.error_message)
                elif rule.rule_type == 'range':
                    value = data.get(rule.field)
                    if not (rule.parameters['min'] <= value <= rule.parameters['max']):
                        raise ValueError(rule.error_message)
                elif rule.rule_type == 'regex':
                    if not re.match(rule.parameters['pattern'], str(data.get(rule.field))):
                        raise ValueError(rule.error_message)
                elif rule.rule_type == 'custom':
                    if not rule.parameters['function'](data.get(rule.field)):
                        raise ValueError(rule.error_message)
            except Exception as e:
                self.logger.error(f"Validation error for {source_name}: {str(e)}")
                raise

        return data

    def add_data_source(self, config: DataSourceConfig):
        """Add a new data source"""
        self.data_sources[config.name] = config
        self._save_data_sources()

    def remove_data_source(self, source_name: str):
        """Remove a data source"""
        if source_name in self.data_sources:
            del self.data_sources[source_name]
            self._save_data_sources()

    def add_validation_rule(self, source_name: str, rule: DataValidationRule):
        """Add a validation rule for a data source"""
        if source_name not in self.validation_rules:
            self.validation_rules[source_name] = []
        self.validation_rules[source_name].append(rule)
        self._save_validation_rules()

    def _save_data_sources(self):
        """Save data source configurations"""
        try:
            with open('config/data_sources.json', 'w') as f:
                json.dump(
                    [source.dict() for source in self.data_sources.values()],
                    f,
                    indent=2
                )
        except Exception as e:
            self.logger.error(f"Error saving data sources: {str(e)}")

    def _save_validation_rules(self):
        """Save validation rules"""
        try:
            with open('config/validation_rules.json', 'w') as f:
                json.dump(
                    {
                        source: [rule.dict() for rule in rules]
                        for source, rules in self.validation_rules.items()
                    },
                    f,
                    indent=2
                )
        except Exception as e:
            self.logger.error(f"Error saving validation rules: {str(e)}")

    def get_data_source_status(self, source_name: str) -> Dict:
        """Get the status of a data source"""
        if source_name not in self.data_sources:
            raise ValueError(f"Unknown data source: {source_name}")

        config = self.data_sources[source_name]
        return {
            'name': config.name,
            'type': config.type,
            'url': config.url,
            'last_updated': datetime.now().isoformat(),
            'validation_rules': len(self.validation_rules.get(source_name, [])),
            'status': 'active'
        } 