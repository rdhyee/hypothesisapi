#!/usr/bin/env python3
"""
Example 02: Collection Statistics

Demonstrates how to gather statistics about a collection of annotations,
including counts by tag, user, date, and other metadata.

This example uses fixture annotations tagged with #hypothesisapi-example.

Usage:
    python 02_collection_stats.py [tag]

If no tag is provided, uses the fixture tag 'hypothesisapi-example'.

Sample Output:
    ============================================================
    Collection Statistics for tag: hypothesisapi-example
    ============================================================

    Total annotations: 5

    By User:
      rdhyee: 5

    By Tag:
      hypothesisapi-example: 5
      page-note: 1
      highlight: 1
      multi-tag: 1
      reply: 1
      private: 1

    Date Range:
      Earliest: 2024-01-15
      Latest:   2024-01-15

    Content Types:
      With text: 5
      Highlights only: 0
      With replies: 1
    ============================================================
"""

import os
import sys
from collections import Counter
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
    """Parse ISO date string to timezone-aware datetime, return date in UTC."""
    if not iso_string:
        return None
    try:
        # Normalize Z suffix to +00:00 for fromisoformat
        normalized = iso_string.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        # Return UTC date to avoid timezone shift issues
        return dt.date()
    except (ValueError, AttributeError):
        return None


def calculate_stats(annotations):
    """Calculate statistics for a collection of annotations."""
    stats = {
        "total": 0,
        "users": Counter(),
        "tags": Counter(),
        "groups": Counter(),
        "dates": [],
        "with_text": 0,
        "highlights_only": 0,
        "with_replies": 0,
        "uris": Counter(),
    }

    for ann in annotations:
        stats["total"] += 1

        # User stats
        user = ann.get("user", "unknown")
        # Extract username from acct:username@domain format
        if user.startswith("acct:"):
            user = user.split(":")[1].split("@")[0]
        stats["users"][user] += 1

        # Tag stats
        for tag in ann.get("tags", []):
            stats["tags"][tag] += 1

        # Group stats
        group = ann.get("group", "__world__")
        stats["groups"][group] += 1

        # Date stats
        created = parse_date(ann.get("created", ""))
        if created:
            stats["dates"].append(created)

        # Content type stats
        text = ann.get("text", "").strip()
        if text:
            stats["with_text"] += 1
        else:
            stats["highlights_only"] += 1

        # Reply stats
        if ann.get("references"):
            stats["with_replies"] += 1

        # URI stats
        uri = ann.get("uri", "unknown")
        # Truncate long URIs for display
        if len(uri) > 50:
            uri = uri[:47] + "..."
        stats["uris"][uri] += 1

    return stats


def display_stats(stats, tag):
    """Display statistics in a formatted way."""
    print("=" * 60)
    print(f"Collection Statistics for tag: {tag}")
    print("=" * 60)
    print()
    print(f"Total annotations: {stats['total']}")

    if stats["total"] == 0:
        print("\nNo annotations found.")
        print("=" * 60)
        return

    # Users
    print("\nBy User:")
    for user, count in stats["users"].most_common(10):
        print(f"  {user}: {count}")

    # Tags
    print("\nBy Tag:")
    for tag_name, count in stats["tags"].most_common(15):
        print(f"  {tag_name}: {count}")

    # Groups
    if len(stats["groups"]) > 1 or "__world__" not in stats["groups"]:
        print("\nBy Group:")
        for group, count in stats["groups"].most_common(5):
            display_name = "Public" if group == "__world__" else group
            print(f"  {display_name}: {count}")

    # Date range
    if stats["dates"]:
        print("\nDate Range:")
        print(f"  Earliest: {min(stats['dates'])}")
        print(f"  Latest:   {max(stats['dates'])}")

    # Content types
    print("\nContent Types:")
    print(f"  With text: {stats['with_text']}")
    print(f"  Highlights only: {stats['highlights_only']}")
    print(f"  Replies: {stats['with_replies']}")

    # URIs (if multiple)
    if len(stats["uris"]) > 1:
        print("\nBy URI:")
        for uri, count in stats["uris"].most_common(5):
            print(f"  {uri}: {count}")

    print("=" * 60)


def main():
    api = get_api()

    # Get tag from command line or use default
    tag = sys.argv[1] if len(sys.argv) > 1 else FIXTURE_TAG

    print(f"Fetching annotations with tag: {tag}")
    print()

    try:
        # Collect all annotations (search returns a generator)
        annotations = list(api.search(tag=tag, limit=200))

        if not annotations:
            print(f"No annotations found with tag '{tag}'.")
            print("\nTip: Run setup_fixtures.py to create fixture annotations,")
            print("     or try a different tag.")
            sys.exit(0)

        # Calculate and display stats
        stats = calculate_stats(annotations)
        display_stats(stats, tag)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
