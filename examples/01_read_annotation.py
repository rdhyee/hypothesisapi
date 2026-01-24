#!/usr/bin/env python3
"""
Example 01: Read a Single Annotation by ID

Demonstrates how to retrieve a single annotation using its ID and display
its contents in a formatted way.

This example uses fixture annotations tagged with #hypothesisapi-example.
It can also fetch any public annotation by ID.

Usage:
    python 01_read_annotation.py [annotation_id]

If no ID is provided, it searches for fixture annotations and uses the first one found.

Sample Output:
    ============================================================
    Annotation Details
    ============================================================
    ID:       abc123xyz
    Created:  2024-01-15T10:30:00.000000+00:00
    Updated:  2024-01-15T10:30:00.000000+00:00
    User:     acct:rdhyee@hypothes.is

    URI:      https://en.wikipedia.org/w/index.php?title=Web_annotation&oldid=1318004643

    Text:
    This is a page-level note demonstrating the hypothesisapi library...

    Tags:     hypothesisapi-example, page-note, demo

    View at:  https://hypothes.is/a/abc123xyz
    ============================================================
"""

import sys

from _common import get_api, extract_quote, FIXTURE_TAG
from hypothesisapi import HypothesisAPIError, NotFoundError


def format_annotation(annotation):
    """Format an annotation for display."""
    print("=" * 60)
    print("Annotation Details")
    print("=" * 60)
    print(f"ID:       {annotation.get('id', '(unknown)')}")
    print(f"Created:  {annotation.get('created', '(unknown)')}")
    print(f"Updated:  {annotation.get('updated', '(unknown)')}")
    print(f"User:     {annotation.get('user', '(unknown)')}")
    print()
    print(f"URI:      {annotation.get('uri', '(unknown)')}")

    # Display document title if available
    doc = annotation.get("document", {})
    if doc.get("title"):
        title = doc["title"][0] if isinstance(doc["title"], list) else doc["title"]
        print(f"Title:    {title}")

    print()

    # Display text content
    text = annotation.get("text", "")
    if text:
        print("Text:")
        # Wrap long text
        for line in text.split("\n"):
            print(f"  {line}")
    else:
        print("Text:     (no text - highlight only)")

    print()

    # Display tags
    tags = annotation.get("tags", [])
    if tags:
        print(f"Tags:     {', '.join(tags)}")
    else:
        print("Tags:     (none)")

    # Display quote if present (highlighted text)
    quote = extract_quote(annotation)
    if quote:
        print()
        print("Highlighted text:")
        print(f'  "{quote}"')

    # Display group
    group = annotation.get("group", "__world__")
    print()
    print(f"Group:    {group}")

    # Display link
    ann_id = annotation.get('id', '')
    if ann_id:
        print()
        print(f"View at:  https://hypothes.is/a/{ann_id}")
    print("=" * 60)


def main():
    api = get_api()
    annotation_id = None

    # Check for command line argument
    if len(sys.argv) > 1:
        annotation_id = sys.argv[1]
    else:
        # Search for fixture annotations
        print(f"No annotation ID provided. Searching for fixtures (tag: {FIXTURE_TAG})...")
        print()
        fixtures = list(api.search(tag=FIXTURE_TAG, limit=5))
        if fixtures:
            annotation_id = fixtures[0].get("id")
            print(f"Found {len(fixtures)} fixture(s). Using first one: {annotation_id}")
            print()
        else:
            print("No fixture annotations found.")
            print("Run setup_fixtures.py first, or provide an annotation ID:")
            print(f"  python {sys.argv[0]} <annotation_id>")
            sys.exit(1)

    # Fetch and display the annotation
    try:
        annotation = api.get_annotation(annotation_id)
        format_annotation(annotation)
    except NotFoundError:
        print(f"Error: Annotation '{annotation_id}' not found.")
        sys.exit(1)
    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
