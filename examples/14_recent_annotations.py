#!/usr/bin/env python3
"""
Example 14: Show Recent Annotations

Demonstrates how to retrieve and display recent annotations, either from
a specific user or from the public stream, with context about each annotation.

Usage:
    python 14_recent_annotations.py [username]

If no username is provided, shows your own recent annotations.

Sample Output:
    ============================================================
    Recent Annotations by rdhyee
    ============================================================

    Showing 10 most recent annotations:

    1. 2024-01-15 10:30 | Web annotation - Wikipedia
       https://en.wikipedia.org/wiki/Web_annotation
       "Web annotation refers to online annotation..."
       This is a page-level note demonstrating the hypothesisapi...
       Tags: hypothesisapi-example, page-note, demo
       View: https://hypothes.is/a/abc123xyz

    2. 2024-01-14 15:45 | Example Domain
       https://example.com
       This is a test annotation...
       Tags: test, example
       View: https://hypothes.is/a/def456abc

    ... (more results)
    ============================================================
"""

import os
import sys

from _common import (
    get_api, parse_date, format_date, truncate, extract_quote,
    format_user_for_search
)
from hypothesisapi import HypothesisAPIError


def display_annotation(index, ann):
    """Display a single annotation with full context."""
    created = parse_date(ann.get("created", ""))
    created_str = format_date(created, "%Y-%m-%d %H:%M") if created else "unknown"

    # Get document title
    doc = ann.get("document", {})
    title = ""
    if doc.get("title"):
        title = doc["title"][0] if isinstance(doc["title"], list) else doc["title"]
        title = truncate(title, 40)

    uri = ann.get("uri", "")
    text = ann.get("text", "")
    quote = extract_quote(ann)
    tags = ann.get("tags", [])

    # Header with date and title
    header = f"{created_str}"
    if title:
        header += f" | {title}"
    print(f"\n{index}. {header}")

    # URI
    display_uri = truncate(uri, 60)
    print(f"   {display_uri}")

    # Quote (highlighted text)
    if quote:
        print(f'   "{truncate(quote, 55)}"')

    # Text content
    if text:
        print(f"   {truncate(text)}")

    # Tags
    if tags:
        print(f"   Tags: {', '.join(tags[:5])}")

    # Link
    ann_id = ann.get('id', '')
    if ann_id:
        print(f"   View: https://hypothes.is/a/{ann_id}")


def main():
    api = get_api()
    default_username = os.environ.get("HYPOTHESIS_USERNAME", "")

    # Get username from command line or use default
    if len(sys.argv) > 1:
        username = sys.argv[1]
    else:
        username = default_username

    if not username:
        print("Error: No username provided.")
        print("Usage: python 14_recent_annotations.py <username>")
        print("   or: set HYPOTHESIS_USERNAME environment variable")
        sys.exit(1)

    print("=" * 60)
    print(f"Recent Annotations by {username}")
    print("=" * 60)

    try:
        # Format username for API search (expects acct:user@hypothes.is)
        user_query = format_user_for_search(username)

        # Search for recent annotations by user, sorted by creation date
        annotations = list(api.search(
            user=user_query,
            limit=10,
            sort="created",
            order="desc"
        ))

        if not annotations:
            print(f"\nNo annotations found for user '{username}'.")
            print("Tip: Create some annotations first!")
            return

        print(f"\nShowing {len(annotations)} most recent annotation(s):")

        for i, ann in enumerate(annotations, 1):
            display_annotation(i, ann)

        print()
        print("=" * 60)

        # Summary statistics (reuse the search we already did)
        total_count = len(annotations)  # We have limit=10, so this is just a sample
        print(f"\nShowing {total_count} most recent (of potentially more)")

        # Count unique URIs
        unique_uris = set(ann.get("uri", "") for ann in annotations)
        print(f"Unique pages (in recent {len(annotations)}): {len(unique_uris)}")

        # Count tags
        all_tags = []
        for ann in annotations:
            all_tags.extend(ann.get("tags", []))
        if all_tags:
            print(f"Unique tags used: {len(set(all_tags))}")

        print("=" * 60)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
