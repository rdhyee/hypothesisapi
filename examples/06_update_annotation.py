#!/usr/bin/env python3
"""
Example 06: Create, Update, and Compare Annotations

Demonstrates the annotation lifecycle: create, update, and display the
differences between versions. This is a self-contained example with cleanup.

Usage:
    python 06_update_annotation.py [uri]

If no URI is provided, uses https://example.com as the target.

Sample Output:
    ============================================================
    Update Annotation Example
    ============================================================

    Step 1: Creating initial annotation...
    Created: abc123xyz

    Original:
      Text: This is the ORIGINAL annotation text...
      Tags: example-temp, version-1

    Step 2: Updating annotation...

    Updated:
      Text: This is the UPDATED annotation text...
      Tags: example-temp, version-2, updated

    Changes:
      - Text changed from 'ORIGINAL' to 'UPDATED'
      - Tags: removed 'version-1', added 'version-2', 'updated'
      - Updated timestamp changed

    Step 3: Cleanup
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


def show_annotation(ann, label):
    """Display annotation details with a label."""
    print(f"\n{label}:")
    text = ann.get("text", "").replace("\n", " ")[:60]
    print(f"  Text: {text}...")
    print(f"  Tags: {', '.join(ann.get('tags', []))}")
    print(f"  Updated: {ann.get('updated', 'N/A')}")


def show_diff(original, updated):
    """Show differences between two annotation versions."""
    print("\nChanges:")

    # Text comparison
    orig_text = original.get("text", "")
    upd_text = updated.get("text", "")
    if orig_text != upd_text:
        # Find what changed
        if "ORIGINAL" in orig_text and "UPDATED" in upd_text:
            print("  - Text changed from 'ORIGINAL' to 'UPDATED'")
        else:
            print("  - Text content modified")

    # Tags comparison
    orig_tags = set(original.get("tags", []))
    upd_tags = set(updated.get("tags", []))
    removed = orig_tags - upd_tags
    added = upd_tags - orig_tags

    if removed or added:
        changes = []
        if removed:
            changes.append(f"removed {', '.join(repr(t) for t in removed)}")
        if added:
            changes.append(f"added {', '.join(repr(t) for t in added)}")
        print(f"  - Tags: {'; '.join(changes)}")

    # Timestamp
    if original.get("updated") != updated.get("updated"):
        print("  - Updated timestamp changed")


def main():
    api = get_api()

    # Get URI from command line or use default
    uri = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URI
    annotation_id = None

    print("=" * 60)
    print("Update Annotation Example")
    print("=" * 60)

    try:
        # Step 1: Create initial annotation
        print("\nStep 1: Creating initial annotation...")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        original_payload = {
            "uri": uri,
            "text": f"This is the ORIGINAL annotation text.\n\n"
                    f"Created at: {timestamp}\n\n"
                    f"This text will be updated to demonstrate the update() method.",
            "tags": ["example-temp", "version-1"]
        }

        original = api.create(original_payload)
        annotation_id = original["id"]
        print(f"Created: {annotation_id}")
        show_annotation(original, "Original")

        # Step 2: Update the annotation
        print("\n" + "-" * 60)
        print("\nStep 2: Updating annotation...")

        update_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update_payload = {
            "text": f"This is the UPDATED annotation text.\n\n"
                    f"Originally created at: {timestamp}\n"
                    f"Updated at: {update_timestamp}\n\n"
                    f"The text and tags have been modified.",
            "tags": ["example-temp", "version-2", "updated"]
        }

        # Perform the update
        api.update(annotation_id, update_payload)

        # Fetch the updated annotation to see all changes
        updated = api.get_annotation(annotation_id)
        show_annotation(updated, "Updated")

        # Show differences
        show_diff(original, updated)

        # Step 3: Cleanup
        print("\n" + "-" * 60)
        print("\nStep 3: Cleanup")
        print()
        try:
            response = input("Delete this annotation? [y/N]: ")
        except EOFError:
            response = "n"
            print("(non-interactive mode, keeping annotation)")

        if response.lower() == "y":
            api.delete(annotation_id)
            print("Annotation deleted successfully.")
            annotation_id = None
        else:
            print(f"Annotation kept: https://hypothes.is/a/{annotation_id}")

    except HypothesisAPIError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        # Ensure cleanup on error
        if annotation_id:
            print(f"\nNote: Annotation {annotation_id} still exists.")
            print(f"Delete with: api.delete('{annotation_id}')")


if __name__ == "__main__":
    main()
