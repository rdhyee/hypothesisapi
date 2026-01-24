#!/usr/bin/env python3
"""
Example 12: Search Group-Specific Annotations

Demonstrates how to search for annotations within a specific group,
including public and private group annotations.

Usage:
    python 12_search_group_annotations.py [group_id]

If no group ID is provided, searches public annotations (__world__).

Sample Output:
    ============================================================
    Group Annotations Search
    ============================================================

    Searching in group: __world__ (Public)

    Found 20 annotation(s):

    1. [abc123] 2024-01-15 by rdhyee
       https://en.wikipedia.org/wiki/Web_annotation
       This is a page-level note demonstrating...
       Tags: hypothesisapi-example, page-note

    ... (more results)

    ============================================================
    Tips:
    - Use '__world__' for public annotations
    - Find group IDs with: python 10_list_groups.py
    ============================================================
"""

import sys

from _common import get_api, parse_date, format_date, truncate, extract_username
from hypothesisapi import HypothesisAPIError


def display_annotation(index, ann):
    """Display a single annotation in summary format."""
    ann_id = ann.get("id", "unknown")[:6]
    user = extract_username(ann.get("user"))

    created = parse_date(ann.get("created", ""))
    date_str = format_date(created, "%Y-%m-%d") if created else "unknown"
    uri = truncate(ann.get("uri", ""), 50)
    text = truncate(ann.get("text", ""), 55)
    tags = ann.get("tags", [])

    print(f"\n{index}. [{ann_id}] {date_str} by {user}")
    print(f"   {uri}")
    print(f"   {text}")
    if tags:
        print(f"   Tags: {', '.join(tags[:5])}")


def main():
    api = get_api()

    # Get group ID from command line or use public group
    if len(sys.argv) > 1:
        group_id = sys.argv[1]
        group_name = group_id
    else:
        group_id = "__world__"
        group_name = "__world__ (Public)"

    print("=" * 60)
    print("Group Annotations Search")
    print("=" * 60)

    # Try to get group details
    if group_id != "__world__":
        try:
            group_info = api.get_group(group_id)
            group_name = group_info.get("name", group_id)
            print(f"\nGroup: {group_name}")
            print(f"ID:    {group_id}")
            print(f"Type:  {group_info.get('type', 'unknown')}")
        except HypothesisAPIError:
            print(f"\nSearching in group: {group_id}")
    else:
        print(f"\nSearching in group: {group_name}")

    try:
        # Search annotations in the group
        annotations = list(api.search(group=group_id, limit=20, order="desc", sort="created"))

        if not annotations:
            print("\nNo annotations found in this group.")
            if group_id == "__world__":
                print("Tip: Create some public annotations first!")
            else:
                print("Tip: Make sure you have access to this group.")
            return

        print(f"\nFound {len(annotations)} annotation(s):")

        for i, ann in enumerate(annotations[:15], 1):
            display_annotation(i, ann)

        if len(annotations) > 15:
            print(f"\n... and {len(annotations) - 15} more")

        print()
        print("=" * 60)
        print("Tips:")
        print("  - Use '__world__' for public annotations")
        print("  - Find group IDs with: python 10_list_groups.py")
        print("  - Combine with uri= or tag= for filtered results")
        print("=" * 60)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
