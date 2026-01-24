#!/usr/bin/env python3
"""
Example 05: Create an Annotation with Cleanup

Demonstrates how to create a new annotation on a web page. This is a
self-contained example that creates an annotation and optionally deletes it.

The annotation is tagged with 'example-temp' for easy identification.

Usage:
    python 05_create_annotation.py [uri]

If no URI is provided, uses https://example.com as the target.

Sample Output:
    ============================================================
    Create Annotation Example
    ============================================================

    Creating annotation on: https://example.com

    Annotation created successfully!

    ID:       abc123xyz
    Created:  2024-01-15T10:30:00.000000+00:00
    URI:      https://example.com
    Text:     This is a test annotation created by hypothesisapi...
    Tags:     example-temp, hypothesisapi-demo

    View at:  https://hypothes.is/a/abc123xyz

    ============================================================

    Delete this annotation? [y/N]: y
    Annotation deleted successfully.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesisapi import API, HypothesisAPIError

# Default target URI
DEFAULT_URI = "https://example.com"


def get_api():
    """Initialize the Hypothesis API client."""
    api_key = os.environ.get("HYPOTHESIS_API_KEY")
    username = os.environ.get("HYPOTHESIS_USERNAME")

    if not api_key:
        print("Error: HYPOTHESIS_API_KEY environment variable not set.")
        print("Get your API key from: https://hypothes.is/account/developer")
        sys.exit(1)

    if not username:
        print("Error: HYPOTHESIS_USERNAME environment variable not set.")
        sys.exit(1)

    return API(username=username, api_key=api_key)


def main():
    api = get_api()

    # Get URI from command line or use default
    uri = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URI

    print("=" * 60)
    print("Create Annotation Example")
    print("=" * 60)
    print(f"\nCreating annotation on: {uri}")

    # Prepare the annotation payload
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    payload = {
        "uri": uri,
        "text": f"This is a test annotation created by hypothesisapi.\n\n"
                f"Created at: {timestamp}\n\n"
                f"This annotation demonstrates the create() method.",
        "tags": ["example-temp", "hypothesisapi-demo"]
    }

    try:
        # Create the annotation
        result = api.create(payload)

        print("\nAnnotation created successfully!")
        print()
        print(f"ID:       {result['id']}")
        print(f"Created:  {result['created']}")
        print(f"URI:      {result['uri']}")
        print()
        print("Text:")
        for line in result.get("text", "").split("\n"):
            print(f"  {line}")
        print()
        print(f"Tags:     {', '.join(result.get('tags', []))}")
        print()
        print(f"View at:  https://hypothes.is/a/{result['id']}")
        print()
        print("=" * 60)

        # Cleanup prompt
        annotation_id = result["id"]
        print()
        try:
            response = input("Delete this annotation? [y/N]: ")
        except EOFError:
            # Non-interactive mode
            response = "n"
            print("(non-interactive mode, keeping annotation)")

        if response.lower() == "y":
            api.delete(annotation_id)
            print("Annotation deleted successfully.")
        else:
            print(f"Annotation kept. Delete later with:")
            print(f"  api.delete('{annotation_id}')")

    except HypothesisAPIError as e:
        print(f"\nError creating annotation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
