import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import asyncio
from pydantic import BaseModel
import traceback
import sys
from functools import wraps

class ErrorSeverity(Enum):
    """Severity levels for errors"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorType(Enum):
    """Types of errors that can occur"""
    NETWORK = "network"
    DATABASE = "database"
    API = "api"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    UNKNOWN = "unknown"

@dataclass
class ErrorContext:
    """Context information for an error"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    timestamp: datetime
    stack_trace: str
    metadata: Dict[str, Any]

class RecoveryStrategy(BaseModel):
    """Strategy for recovering from errors"""
    name: str
    description: str
    retry_count: int = 3
    retry_delay: int = 5
    fallback_action: Optional[str] = None
    conditions: Dict[str, Any] = {}

class ErrorHandler:
    def __init__(self, recovery_strategies: Optional[Dict[ErrorType, RecoveryStrategy]] = None):
        self.logger = logging.getLogger(__name__)
        self.error_history: List[ErrorContext] = []
        self.recovery_strategies = recovery_strategies or self._get_default_strategies()
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}

    def _get_default_strategies(self) -> Dict[ErrorType, RecoveryStrategy]:
        """Get default recovery strategies"""
        return {
            ErrorType.NETWORK: RecoveryStrategy(
                name="network_retry",
                description="Retry network operations with exponential backoff",
                retry_count=3,
                retry_delay=5,
                fallback_action="use_cached_data"
            ),
            ErrorType.DATABASE: RecoveryStrategy(
                name="database_fallback",
                description="Use fallback database or cached data",
                retry_count=2,
                retry_delay=10,
                fallback_action="use_read_replica"
            ),
            ErrorType.API: RecoveryStrategy(
                name="api_circuit_breaker",
                description="Use circuit breaker pattern for API calls",
                retry_count=2,
                retry_delay=15,
                fallback_action="use_cached_response"
            ),
            ErrorType.RATE_LIMIT: RecoveryStrategy(
                name="rate_limit_backoff",
                description="Implement exponential backoff for rate limits",
                retry_count=4,
                retry_delay=30,
                fallback_action="queue_request"
            )
        }

    async def handle_error(self, error: Exception, error_type: ErrorType, metadata: Optional[Dict] = None) -> Any:
        """Handle an error and attempt recovery"""
        try:
            # Create error context
            context = ErrorContext(
                error_type=error_type,
                severity=self._determine_severity(error, error_type),
                message=str(error),
                timestamp=datetime.now(),
                stack_trace=traceback.format_exc(),
                metadata=metadata or {}
            )
            
            # Log error
            self._log_error(context)
            
            # Add to error history
            self.error_history.append(context)
            
            # Get recovery strategy
            strategy = self.recovery_strategies.get(error_type)
            if not strategy:
                strategy = self.recovery_strategies[ErrorType.UNKNOWN]
            
            # Attempt recovery
            return await self._attempt_recovery(context, strategy)
            
        except Exception as e:
            self.logger.error(f"Error in error handler: {str(e)}")
            return None

    def _determine_severity(self, error: Exception, error_type: ErrorType) -> ErrorSeverity:
        """Determine the severity of an error"""
        if isinstance(error, (ConnectionError, TimeoutError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.MEDIUM
        elif isinstance(error, (PermissionError, AuthenticationError)):
            return ErrorSeverity.CRITICAL
        else:
            return ErrorSeverity.UNKNOWN

    def _log_error(self, context: ErrorContext):
        """Log error with appropriate severity"""
        log_message = f"{context.error_type.value} error: {context.message}"
        
        if context.severity == ErrorSeverity.CRITICAL:
            self.logger.critical(log_message, extra=context.metadata)
        elif context.severity == ErrorSeverity.HIGH:
            self.logger.error(log_message, extra=context.metadata)
        elif context.severity == ErrorSeverity.MEDIUM:
            self.logger.warning(log_message, extra=context.metadata)
        else:
            self.logger.info(log_message, extra=context.metadata)

    async def _attempt_recovery(self, context: ErrorContext, strategy: RecoveryStrategy) -> Any:
        """Attempt to recover from an error using the specified strategy"""
        try:
            # Check circuit breaker
            if self._is_circuit_breaker_open(context):
                return await self._execute_fallback(context, strategy)
            
            # Attempt retries
            for attempt in range(strategy.retry_count):
                try:
                    # Wait before retry if not first attempt
                    if attempt > 0:
                        await asyncio.sleep(strategy.retry_delay * (2 ** attempt))
                    
                    # Execute recovery action
                    return await self._execute_recovery(context, strategy)
                    
                except Exception as e:
                    if attempt == strategy.retry_count - 1:
                        # All retries failed, execute fallback
                        return await self._execute_fallback(context, strategy)
            
        except Exception as e:
            self.logger.error(f"Recovery failed: {str(e)}")
            return None

    def _is_circuit_breaker_open(self, context: ErrorContext) -> bool:
        """Check if circuit breaker is open for the given context"""
        key = f"{context.error_type.value}_{context.metadata.get('source', 'default')}"
        
        if key not in self.circuit_breakers:
            self.circuit_breakers[key] = CircuitBreaker()
            
        return self.circuit_breakers[key].is_open()

    async def _execute_recovery(self, context: ErrorContext, strategy: RecoveryStrategy) -> Any:
        """Execute the recovery action"""
        # Implement recovery logic based on error type and strategy
        if context.error_type == ErrorType.NETWORK:
            return await self._retry_network_operation(context)
        elif context.error_type == ErrorType.DATABASE:
            return await self._switch_database(context)
        elif context.error_type == ErrorType.API:
            return await self._retry_api_call(context)
        elif context.error_type == ErrorType.RATE_LIMIT:
            return await self._handle_rate_limit(context)
        else:
            return await self._generic_recovery(context)

    async def _execute_fallback(self, context: ErrorContext, strategy: RecoveryStrategy) -> Any:
        """Execute the fallback action"""
        if strategy.fallback_action == "use_cached_data":
            return await self._use_cached_data(context)
        elif strategy.fallback_action == "use_read_replica":
            return await self._use_read_replica(context)
        elif strategy.fallback_action == "use_cached_response":
            return await self._use_cached_response(context)
        elif strategy.fallback_action == "queue_request":
            return await self._queue_request(context)
        else:
            return None

    def get_error_history(self, time_window: Optional[timedelta] = None) -> List[Dict]:
        """Get error history with optional time window"""
        if not time_window:
            return [self._format_error_context(context) for context in self.error_history]
            
        cutoff = datetime.now() - time_window
        return [
            self._format_error_context(context)
            for context in self.error_history
            if context.timestamp >= cutoff
        ]

    def _format_error_context(self, context: ErrorContext) -> Dict:
        """Format error context for reporting"""
        return {
            'error_type': context.error_type.value,
            'severity': context.severity.value,
            'message': context.message,
            'timestamp': context.timestamp.isoformat(),
            'metadata': context.metadata
        }

    def clear_error_history(self, time_window: Optional[timedelta] = None):
        """Clear error history older than the specified time window"""
        if not time_window:
            self.error_history = []
            return
            
        cutoff = datetime.now() - time_window
        self.error_history = [
            context for context in self.error_history
            if context.timestamp >= cutoff
        ]

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = "closed"

    def is_open(self) -> bool:
        """Check if circuit breaker is open"""
        if self.state == "open":
            if self.last_failure_time and \
               (datetime.now() - self.last_failure_time).total_seconds() > self.reset_timeout:
                self.state = "half-open"
                return False
            return True
        return False

    def record_failure(self):
        """Record a failure"""
        self.failures += 1
        self.last_failure_time = datetime.now()
        
        if self.failures >= self.failure_threshold:
            self.state = "open"

    def record_success(self):
        """Record a success"""
        self.failures = 0
        self.state = "closed"

def error_handler(error_type: ErrorType):
    """Decorator for error handling"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            handler = ErrorHandler()
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return await handler.handle_error(e, error_type, {
                    'function': func.__name__,
                    'args': str(args),
                    'kwargs': str(kwargs)
                })
        return wrapper
    return decorator 