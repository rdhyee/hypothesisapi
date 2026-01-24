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

import sys

from _common import get_api, parse_date, format_date, truncate, extract_username, FIXTURE_TAG
from hypothesisapi import HypothesisAPIError


def display_annotation(index, ann):
    """Display a single annotation in summary format."""
    ann_id = ann.get("id", "unknown")[:7]
    user = extract_username(ann.get("user"))

    created = parse_date(ann.get("created", ""))
    date_str = format_date(created, "%Y-%m-%d") if created else "unknown"
    text = truncate(ann.get("text", ""), 55)
    tags = ann.get("tags", [])

    print(f"\n{index}. [{ann_id}] {date_str} by {user}")
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
