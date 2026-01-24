#!/usr/bin/env python3
"""
Example 07: Create and Automatically Delete Temporary Annotation

Demonstrates creating a temporary annotation that is automatically deleted
after a confirmation prompt. Useful for testing or demonstrating the API
without leaving artifacts.

Usage:
    python 07_temporary_annotation.py [uri]

If no URI is provided, uses https://example.com as the target.

Sample Output:
    ============================================================
    Temporary Annotation Demo
    ============================================================

    Creating temporary annotation on: https://example.com

    Annotation created:
      ID: abc123xyz
      Text: This is a TEMPORARY annotation...
      View: https://hypothes.is/a/abc123xyz

    Press Enter to delete this annotation (or Ctrl+C to keep it)...

    Annotation deleted successfully.
    Temporary annotations leave no trace!
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
    annotation_id = None
    keep_annotation = False

    print("=" * 60)
    print("Temporary Annotation Demo")
    print("=" * 60)
    print(f"\nCreating temporary annotation on: {uri}")

    try:
        # Create the temporary annotation
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "uri": uri,
            "text": f"This is a TEMPORARY annotation created by hypothesisapi.\n\n"
                    f"Created at: {timestamp}\n\n"
                    f"This annotation will be deleted automatically after confirmation.\n"
                    f"It demonstrates how to create and clean up test annotations.",
            "tags": ["temporary", "auto-delete", "hypothesisapi-demo"]
        }

        result = api.create(payload)
        annotation_id = result["id"]

        print("\nAnnotation created:")
        print(f"  ID:   {annotation_id}")
        text_preview = result.get("text", "").split("\n")[0]
        print(f"  Text: {text_preview}")
        print(f"  Tags: {', '.join(result.get('tags', []))}")
        print(f"  View: https://hypothes.is/a/{annotation_id}")
        print()

        # Wait for user confirmation
        try:
            input("Press Enter to delete this annotation (or Ctrl+C to keep it)...")
        except EOFError:
            # Non-interactive mode - auto-delete
            print("(non-interactive mode, auto-deleting)")
        except KeyboardInterrupt:
            keep_annotation = True
            print("\n\nKeeping annotation due to user interrupt.")

    except HypothesisAPIError as e:
        print(f"\nError creating annotation: {e}")
        sys.exit(1)

    # Cleanup
    if annotation_id and not keep_annotation:
        try:
            api.delete(annotation_id)
            print("\nAnnotation deleted successfully.")
            print("Temporary annotations leave no trace!")
        except HypothesisAPIError as e:
            print(f"\nError deleting annotation: {e}")
            print(f"Manual cleanup needed: api.delete('{annotation_id}')")
    elif annotation_id:
        print(f"\nAnnotation preserved: https://hypothes.is/a/{annotation_id}")
        print(f"Delete later with: api.delete('{annotation_id}')")


if __name__ == "__main__":
    main()
