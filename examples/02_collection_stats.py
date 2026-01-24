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

    Date Range:
      Earliest: 2024-01-15
      Latest:   2024-01-15

    Content Types:
      With text: 5
      Highlights only: 0
      Replies: 1
    ============================================================
"""

import sys
from collections import Counter

from _common import get_api, parse_date, extract_username, truncate, FIXTURE_TAG
from hypothesisapi import HypothesisAPIError


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
        "replies": 0,  # Annotations that ARE replies (have references)
        "uris": Counter(),
        "uri_display": {},  # Map full URI to truncated display version
    }

    for ann in annotations:
        stats["total"] += 1

        # User stats
        user = extract_username(ann.get("user"))
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
            stats["dates"].append(created.date() if hasattr(created, 'date') else created)

        # Content type stats
        text = ann.get("text", "").strip()
        if text:
            stats["with_text"] += 1
        else:
            stats["highlights_only"] += 1

        # Reply stats (annotations that ARE replies, not that HAVE replies)
        if ann.get("references"):
            stats["replies"] += 1

        # URI stats - count with full URI, store truncated for display
        uri = ann.get("uri", "unknown")
        stats["uris"][uri] += 1
        if uri not in stats["uri_display"]:
            stats["uri_display"][uri] = truncate(uri, 50)

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
    print(f"  Replies: {stats['replies']}")

    # URIs (if multiple)
    if len(stats["uris"]) > 1:
        print("\nBy URI:")
        for uri, count in stats["uris"].most_common(5):
            display_uri = stats["uri_display"].get(uri, uri)
            print(f"  {display_uri}: {count}")

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
