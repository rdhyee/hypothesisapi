#!/usr/bin/env python3
"""
Example 04: Search Annotations by Tag

Demonstrates how to search for annotations using single tags, multiple tags,
and combining tag searches with other filters.

Usage:
    python 04_search_by_tag.py [tag1] [tag2] ...

If no tags are provided, searches for fixture tag 'hypothesisapi-example'.

Sample Output:
    ============================================================
    Tag Search Results
    ============================================================

    Searching for tag: hypothesisapi-example
    Found 5 annotation(s):

    1. [abc123] 2024-01-15 by rdhyee
       This is a page-level note demonstrating...
       Tags: hypothesisapi-example, page-note, demo

    ... (more results)

    ============================================================
    Multi-Tag Search: hypothesisapi-example AND highlight
    ============================================================
    Found 1 annotation(s) with both tags:

    1. [def456] 2024-01-15 by rdhyee
       This annotation highlights specific text...
       Tags: hypothesisapi-example, highlight, anchored
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesisapi import API, HypothesisAPIError

# Fixture discovery tag
FIXTURE_TAG = "hypothesisapi-example"


def get_api():
    """Initialize the Hypothesis API client."""
    api_key = os.environ.get("HYPOTHESIS_API_KEY")
    username = os.environ.get("HYPOTHESIS_USERNAME", "")

    if not api_key:
        print("Error: HYPOTHESIS_API_KEY environment variable not set.")
        print("Get your API key from: https://hypothes.is/account/developer")
        sys.exit(1)

    return API(username=username, api_key=api_key)


def parse_date(iso_string):
    """Parse ISO date string to readable date."""
    try:
        if "." in iso_string:
            dt = datetime.fromisoformat(iso_string.replace("+00:00", "").split(".")[0])
        else:
            dt = datetime.fromisoformat(iso_string.replace("+00:00", "").replace("Z", ""))
        return dt.strftime("%Y-%m-%d")
    except (ValueError, AttributeError):
        return "unknown"


def truncate(text, max_length=55):
    """Truncate text to max length with ellipsis."""
    if not text:
        return "(no text)"
    text = text.replace("\n", " ").strip()
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def display_annotation(index, ann):
    """Display a single annotation in summary format."""
    ann_id = ann["id"][:7]
    user = ann.get("user", "unknown")
    if user.startswith("acct:"):
        user = user.split(":")[1].split("@")[0]

    date = parse_date(ann.get("created", ""))
    text = truncate(ann.get("text", ""))
    tags = ann.get("tags", [])

    print(f"\n{index}. [{ann_id}] {date} by {user}")
    print(f"   {text}")
    if tags:
        print(f"   Tags: {', '.join(tags)}")


def main():
    api = get_api()

    # Get tags from command line or use default
    if len(sys.argv) > 1:
        tags = sys.argv[1:]
    else:
        tags = [FIXTURE_TAG]

    # Single tag search
    primary_tag = tags[0]
    print("=" * 60)
    print("Tag Search Results")
    print("=" * 60)
    print(f"\nSearching for tag: {primary_tag}")

    try:
        # Search for single tag
        annotations = list(api.search(tag=primary_tag, limit=20))

        if annotations:
            print(f"Found {len(annotations)} annotation(s):")
            for i, ann in enumerate(annotations[:10], 1):
                display_annotation(i, ann)
            if len(annotations) > 10:
                print(f"\n... and {len(annotations) - 10} more")
        else:
            print(f"\nNo annotations found with tag '{primary_tag}'.")
            print("Tip: Run setup_fixtures.py to create fixture annotations.")

        # Multi-tag search (if multiple tags provided)
        if len(tags) > 1:
            print()
            print("=" * 60)
            print(f"Multi-Tag Search: {' AND '.join(tags)}")
            print("=" * 60)

            # Search with multiple tags (all must match)
            multi_annotations = list(api.search(tags=tags, limit=20))

            if multi_annotations:
                print(f"Found {len(multi_annotations)} annotation(s) with all tags:")
                for i, ann in enumerate(multi_annotations[:10], 1):
                    display_annotation(i, ann)
            else:
                print(f"\nNo annotations found with all specified tags.")

        # Demonstrate combining tag with other filters
        print()
        print("-" * 60)
        print("Advanced Tag Search Examples:")
        print("-" * 60)
        print()
        print("# Single tag search")
        print('api.search(tag="hypothesis")')
        print()
        print("# Multiple tags (AND logic - must have all)")
        print('api.search(tags=["python", "tutorial"])')
        print()
        print("# Tag + user filter")
        print('api.search(tag="hypothesis", user="username")')
        print()
        print("# Tag + URI filter")
        print('api.search(tag="hypothesis", uri="https://example.com")')
        print()
        print("# Tag + date ordering")
        print('api.search(tag="hypothesis", sort="created", order="desc")')
        print("-" * 60)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
