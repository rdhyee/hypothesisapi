#!/usr/bin/env python3
"""
Common helper functions for hypothesisapi examples.

This module provides shared utilities to reduce code duplication
and ensure consistent behavior across all example scripts.
"""

import os
import sys
from datetime import datetime, timezone
from typing import Optional

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesisapi import API


# Fixture discovery tag
FIXTURE_TAG = "hypothesisapi-example"

# Wikipedia fixture URL (permanent revision)
WIKIPEDIA_URL = "https://en.wikipedia.org/w/index.php?title=Web_annotation&oldid=1318004643"


def get_api() -> API:
    """
    Initialize the Hypothesis API client from environment variables.

    Required:
        HYPOTHESIS_API_KEY: Your Hypothesis API key

    Optional:
        HYPOTHESIS_USERNAME: Your Hypothesis username (for user-specific queries)

    Returns:
        Configured API instance

    Exits with error if API key is not set.
    """
    api_key = os.environ.get("HYPOTHESIS_API_KEY")
    username = os.environ.get("HYPOTHESIS_USERNAME", "")

    if not api_key:
        print("Error: HYPOTHESIS_API_KEY environment variable not set.")
        print("Get your API key from: https://hypothes.is/account/developer")
        print()
        print("Usage with 1Password:")
        print("  op run --env HYPOTHESIS_API_KEY='op://vault/item/field' -- python script.py")
        sys.exit(1)

    return API(username=username, api_key=api_key)


def parse_date(iso_string: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO date string to timezone-aware datetime object.

    Handles various ISO formats from the Hypothesis API:
    - 2024-01-15T10:30:00.123456+00:00
    - 2024-01-15T10:30:00Z
    - 2024-01-15T10:30:00

    Args:
        iso_string: ISO format datetime string

    Returns:
        Timezone-aware datetime (UTC), or None if parsing fails
    """
    if not iso_string:
        return None

    try:
        # Python 3.11+ handles most ISO formats directly
        # For older Python, we need to handle Z suffix
        normalized = iso_string.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)

        # Ensure timezone-aware (assume UTC if naive)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        return dt
    except (ValueError, AttributeError):
        return None


def format_date(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M") -> str:
    """
    Format datetime for display.

    Args:
        dt: Datetime object (or None)
        fmt: strftime format string

    Returns:
        Formatted date string, or "(unknown)" if None
    """
    if dt is None:
        return "(unknown)"
    return dt.strftime(fmt)


def extract_username(user_string: Optional[str]) -> str:
    """
    Extract username from acct:username@domain format.

    Args:
        user_string: Full user string (e.g., "acct:rdhyee@hypothes.is")

    Returns:
        Just the username (e.g., "rdhyee"), or original string if not in expected format
    """
    if not user_string:
        return "(unknown)"
    if user_string.startswith("acct:"):
        return user_string.split(":")[1].split("@")[0]
    return user_string


def format_user_for_search(username: str) -> str:
    """
    Format username for Hypothesis API search queries.

    The API expects 'acct:username@hypothes.is' format for user filtering.

    Args:
        username: Plain username (e.g., "rdhyee")

    Returns:
        Full acct format (e.g., "acct:rdhyee@hypothes.is")
    """
    if not username:
        return ""
    if username.startswith("acct:"):
        return username
    return f"acct:{username}@hypothes.is"


def truncate(text: Optional[str], max_length: int = 60) -> str:
    """
    Truncate text to max length with ellipsis.

    Args:
        text: Text to truncate
        max_length: Maximum length including ellipsis

    Returns:
        Truncated text, or "(no text)" if empty/None
    """
    if not text:
        return "(no text)"
    text = text.replace("\n", " ").strip()
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def extract_quote(annotation: dict) -> str:
    """
    Extract highlighted text from annotation selectors.

    Args:
        annotation: Annotation dict from API

    Returns:
        Highlighted/quoted text, or empty string if not a highlight
    """
    for target in annotation.get("target", []):
        for selector in target.get("selector", []):
            if selector.get("type") == "TextQuoteSelector":
                return selector.get("exact", "")
    return ""
