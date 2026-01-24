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

import os
import sys

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesisapi import API, HypothesisAPIError, NotFoundError

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


def format_annotation(annotation):
    """Format an annotation for display."""
    print("=" * 60)
    print("Annotation Details")
    print("=" * 60)
    print(f"ID:       {annotation['id']}")
    print(f"Created:  {annotation['created']}")
    print(f"Updated:  {annotation['updated']}")
    print(f"User:     {annotation['user']}")
    print()
    print(f"URI:      {annotation['uri']}")

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
    targets = annotation.get("target", [])
    for target in targets:
        for selector in target.get("selector", []):
            if selector.get("type") == "TextQuoteSelector":
                exact = selector.get("exact", "")
                if exact:
                    print()
                    print("Highlighted text:")
                    print(f'  "{exact}"')

    # Display group
    group = annotation.get("group", "__world__")
    print()
    print(f"Group:    {group}")

    # Display link
    print()
    print(f"View at:  https://hypothes.is/a/{annotation['id']}")
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
            annotation_id = fixtures[0]["id"]
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
