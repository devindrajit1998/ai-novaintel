"""
Timezone utility for converting timestamps to Indian Standard Time (IST).
"""
from datetime import datetime
from typing import Optional
import pytz

# IST timezone
IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.UTC

def to_ist(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert a datetime to IST.
    
    Args:
        dt: Datetime object (assumed UTC if timezone-naive)
    
    Returns:
        Datetime in IST timezone, or None if input is None
    """
    if dt is None:
        return None
    
    # If timezone-naive, assume UTC
    if dt.tzinfo is None:
        dt = UTC.localize(dt)
    
    # Convert to IST
    return dt.astimezone(IST)

def from_ist(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert a datetime from IST to UTC.
    
    Args:
        dt: Datetime object in IST (assumed IST if timezone-naive)
    
    Returns:
        Datetime in UTC timezone, or None if input is None
    """
    if dt is None:
        return None
    
    # If timezone-naive, assume IST
    if dt.tzinfo is None:
        dt = IST.localize(dt)
    
    # Convert to UTC
    return dt.astimezone(UTC)

def now_ist() -> datetime:
    """
    Get current time in IST.
    
    Returns:
        Current datetime in IST
    """
    return datetime.now(IST)

def now_utc_from_ist() -> datetime:
    """
    Get current time in IST, but return as UTC for database storage.
    This ensures we're using IST as the source timezone but storing in UTC.
    
    Returns:
        Current datetime in UTC (converted from IST)
    """
    ist_now = datetime.now(IST)
    return ist_now.astimezone(UTC).replace(tzinfo=None)

def format_ist(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format a datetime in IST.
    
    Args:
        dt: Datetime object
        format_str: Format string
    
    Returns:
        Formatted string, or empty string if dt is None
    """
    if dt is None:
        return ""
    
    dt_ist = to_ist(dt)
    return dt_ist.strftime(format_str)

