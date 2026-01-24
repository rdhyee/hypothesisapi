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

import os
import sys
from datetime import datetime

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesisapi import API, HypothesisAPIError


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
    ann_id = ann["id"][:6]
    user = ann.get("user", "unknown")
    if user.startswith("acct:"):
        user = user.split(":")[1].split("@")[0]

    date = parse_date(ann.get("created", ""))
    uri = ann.get("uri", "")
    if len(uri) > 50:
        uri = uri[:47] + "..."
    text = truncate(ann.get("text", ""))
    tags = ann.get("tags", [])

    print(f"\n{index}. [{ann_id}] {date} by {user}")
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
