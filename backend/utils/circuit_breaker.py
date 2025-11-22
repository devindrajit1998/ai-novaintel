"""
Circuit breaker pattern for resilient service calls.
"""
from typing import Callable, Any, Optional, Type, Tuple
from functools import wraps
from enum import Enum
import time
import logging

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """Circuit breaker for protecting services from cascading failures."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception,
        name: str = "default"
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name
        
        self.failure_count = 0
        self.last_failure_time: Optional[float] = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) >= self.recovery_timeout:
                logger.info(f"Circuit breaker {self.name}: Attempting recovery (HALF_OPEN)")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Service unavailable. Retry after {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            
            # Success - reset on success
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit breaker {self.name}: Service recovered (CLOSED)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_failure_time = None
            
            return result
        
        except self.expected_exception as e:
            self._record_failure()
            raise e
    
    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """Execute async function with circuit breaker protection."""
        if self.state == CircuitState.OPEN:
            # Check if recovery timeout has passed
            if self.last_failure_time and \
               (time.time() - self.last_failure_time) >= self.recovery_timeout:
                logger.info(f"Circuit breaker {self.name}: Attempting recovery (HALF_OPEN)")
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(
                    f"Circuit breaker {self.name} is OPEN. "
                    f"Service unavailable. Retry after {self.recovery_timeout}s"
                )
        
        try:
            result = await func(*args, **kwargs)
            
            # Success - reset on success
            if self.state == CircuitState.HALF_OPEN:
                logger.info(f"Circuit breaker {self.name}: Service recovered (CLOSED)")
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                self.last_failure_time = None
            
            return result
        
        except self.expected_exception as e:
            self._record_failure()
            raise e
    
    def _record_failure(self):
        """Record a failure and update circuit state."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            if self.state != CircuitState.OPEN:
                logger.error(
                    f"Circuit breaker {self.name}: Opening circuit "
                    f"({self.failure_count} failures >= {self.failure_threshold})"
                )
                self.state = CircuitState.OPEN
    
    def reset(self):
        """Manually reset circuit breaker."""
        logger.info(f"Circuit breaker {self.name}: Manually reset")
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception,
    name: Optional[str] = None
):
    """
    Circuit breaker decorator.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to catch
        name: Name for circuit breaker (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        cb_name = name or f"{func.__module__}.{func.__name__}"
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=cb_name
        )
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        
        return wrapper
    return decorator


def async_circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception,
    name: Optional[str] = None
):
    """
    Async circuit breaker decorator.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Seconds to wait before attempting recovery
        expected_exception: Exception type to catch
        name: Name for circuit breaker (defaults to function name)
    """
    def decorator(func: Callable) -> Callable:
        cb_name = name or f"{func.__module__}.{func.__name__}"
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            expected_exception=expected_exception,
            name=cb_name
        )
        
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            return await breaker.call_async(func, *args, **kwargs)
        
        return wrapper
    return decorator

