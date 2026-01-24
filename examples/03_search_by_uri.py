#!/usr/bin/env python3
"""
Example 03: Search Annotations by URI

Demonstrates how to search for annotations on a specific web page using
both exact URI matching and wildcard URI patterns.

This example searches for annotations on the Wikipedia "Web annotation" article.

Usage:
    python 03_search_by_uri.py [uri]

If no URI is provided, uses the Wikipedia fixture URL.

Sample Output:
    ============================================================
    Searching for annotations on:
    https://en.wikipedia.org/w/index.php?title=Web_annotation&oldid=1318004643
    ============================================================

    Found 5 annotation(s):

    1. [abc123] Page note by rdhyee
       This is a page-level note demonstrating the hypothesisapi...
       Tags: hypothesisapi-example, page-note, demo

    2. [def456] Highlight by rdhyee
       "Web annotation" - This annotation highlights specific text...
       Tags: hypothesisapi-example, highlight, anchored

    ... (more results)

    ============================================================
    Wildcard Search: en.wikipedia.org/*
    ============================================================
    Found 12 total annotations on en.wikipedia.org
"""

import sys
from urllib.parse import urlparse

from _common import get_api, truncate, extract_username, extract_quote, WIKIPEDIA_URL
from hypothesisapi import HypothesisAPIError


def display_annotation(index, ann):
    """Display a single annotation in summary format."""
    ann_id = ann.get("id", "unknown")[:7]
    user = extract_username(ann.get("user"))

    text = ann.get("text", "")
    tags = ann.get("tags", [])
    quote = extract_quote(ann)

    # Format the display
    ann_type = "Highlight" if quote else "Page note"
    print(f"\n{index}. [{ann_id}] {ann_type} by {user}")

    if quote:
        print(f'   "{truncate(quote, 40)}"')
        if text:
            print(f"   {truncate(text)}")
    else:
        print(f"   {truncate(text)}")

    if tags:
        print(f"   Tags: {', '.join(tags[:5])}")


def main():
    api = get_api()

    # Get URI from command line or use default
    uri = sys.argv[1] if len(sys.argv) > 1 else WIKIPEDIA_URL

    print("=" * 60)
    print("Searching for annotations on:")
    print(uri)
    print("=" * 60)

    try:
        # Exact URI search
        annotations = list(api.search(uri=uri, limit=20))

        if annotations:
            print(f"\nFound {len(annotations)} annotation(s):")
            for i, ann in enumerate(annotations, 1):
                display_annotation(i, ann)
        else:
            print("\nNo annotations found for this exact URI.")

        # Demonstrate wildcard search
        print()
        print("=" * 60)
        parsed = urlparse(uri)
        domain = parsed.netloc

        print(f"Wildcard Search: {domain}/*")
        print("=" * 60)

        # Search both http and https schemes to ensure complete results
        # The API doesn't normalize schemes, so we need to check both
        wildcard_annotations = []
        seen_ids = set()

        for scheme in ["https", "http"]:
            wildcard_pattern = f"{scheme}://{domain}/*"
            for ann in api.search(wildcard_uri=wildcard_pattern, limit=20):
                ann_id = ann.get("id")
                if ann_id and ann_id not in seen_ids:
                    seen_ids.add(ann_id)
                    wildcard_annotations.append(ann)

        if wildcard_annotations:
            print(f"Found {len(wildcard_annotations)} annotations on {domain}")
            print("\nSample (first 5):")
            for i, ann in enumerate(wildcard_annotations[:5], 1):
                display_annotation(i, ann)
        else:
            print(f"No annotations found on {domain}")

        # Additional search tips
        print()
        print("-" * 60)
        print("Search Tips:")
        print("  - Use exact URI for specific page annotations")
        print("  - Use wildcard_uri='https://domain.com/*' for site-wide search")
        print("  - Combine with user= or tag= for filtered results")
        print("-" * 60)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
