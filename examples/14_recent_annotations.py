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

    return API(username=username, api_key=api_key), username


def parse_datetime(iso_string):
    """Parse ISO datetime string to readable format."""
    try:
        if "." in iso_string:
            dt = datetime.fromisoformat(iso_string.replace("+00:00", "").split(".")[0])
        else:
            dt = datetime.fromisoformat(iso_string.replace("+00:00", "").replace("Z", ""))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return "unknown"


def truncate(text, max_length=60):
    """Truncate text to max length with ellipsis."""
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    if len(text) > max_length:
        return text[:max_length - 3] + "..."
    return text


def extract_quote(annotation):
    """Extract highlighted text from annotation selectors."""
    for target in annotation.get("target", []):
        for selector in target.get("selector", []):
            if selector.get("type") == "TextQuoteSelector":
                return selector.get("exact", "")
    return ""


def display_annotation(index, ann):
    """Display a single annotation with full context."""
    created = parse_datetime(ann.get("created", ""))

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
    header = f"{created}"
    if title:
        header += f" | {title}"
    print(f"\n{index}. {header}")

    # URI
    display_uri = uri if len(uri) <= 60 else uri[:57] + "..."
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
    print(f"   View: https://hypothes.is/a/{ann['id']}")


def main():
    api, default_username = get_api()

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
        # Search for recent annotations by user, sorted by creation date
        annotations = list(api.search(
            user=username,
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

        # Summary statistics
        total_result = api.search_raw(user=username, limit=1)
        total_count = total_result.get("total", len(annotations))
        print(f"\nTotal annotations by {username}: {total_count}")

        # Count unique URIs
        unique_uris = set(ann.get("uri", "") for ann in annotations)
        print(f"Unique pages (in recent {len(annotations)}): {len(unique_uris)}")

        # Count tags
        all_tags = []
        for ann in annotations:
            all_tags.extend(ann.get("tags", []))
        if all_tags:
            print(f"Total tags used: {len(set(all_tags))}")

        print("=" * 60)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
