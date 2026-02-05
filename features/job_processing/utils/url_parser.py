import re
from typing import List
from datetime import datetime


def extract_urls(text: str) -> List[str]:
    """Extract all URLs from text, excluding base Upwork URLs.

    Args:
        text: Text to parse for URLs

    Returns:
        List of URLs found in text (excluding upwork.com)
    """
    # Common URL patterns
    patterns = [
        r'https?://[^\s<>"]+|www\.[^\s<>"]+',  # HTTP/HTTPS + www
        r'\b[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>"]*)?',  # Domain + path
    ]

    urls = []
    seen_urls = set()

    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            # Normalize URL
            url = match.strip('"\'.,;:)')
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            # Skip Upwork URLs and duplicates
            if 'upwork.com' not in url.lower() and url not in seen_urls:
                seen_urls.add(url)
                urls.append(url)

    return urls


def calculate_job_age(ts_publish: datetime) -> tuple[int, str]:
    """Calculate job age and return hours and human-readable string.

    Args:
        ts_publish: Job publish timestamp

    Returns:
        Tuple of (age_in_hours, human_readable_string)
    """
    now = datetime.utcnow()
    if isinstance(ts_publish, str):
        ts_publish = datetime.fromisoformat(ts_publish.replace('Z', '+00:00'))

    # Normalize to UTC if timezone-aware
    if ts_publish.tzinfo is not None:
        ts_publish = ts_publish.replace(tzinfo=None)

    delta = now - ts_publish
    hours = int(delta.total_seconds() / 3600)

    # Human-readable string - most granular appropriate unit
    minutes = int(delta.total_seconds() / 60)

    if minutes < 5:
        age_str = "just now"
    elif minutes < 60:
        age_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif hours < 24:
        age_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif hours < 168:  # 1 week
        days = hours // 24
        age_str = f"{days} day{'s' if days != 1 else ''} ago"
    else:
        weeks = hours // 168
        age_str = f"{weeks} week{'s' if weeks != 1 else ''} ago"

    return hours, age_str