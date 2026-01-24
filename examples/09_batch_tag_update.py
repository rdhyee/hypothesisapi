#!/usr/bin/env python3
"""
Example 09: Batch Tag Updates

Demonstrates how to perform batch operations on annotations, specifically
adding or removing tags from multiple annotations at once. This is a
self-contained example that creates test annotations, modifies them, and cleans up.

Usage:
    python 09_batch_tag_update.py

Sample Output:
    ============================================================
    Batch Tag Update Demo
    ============================================================

    Step 1: Creating 3 test annotations...
      Created: abc123 (tags: test, batch-demo)
      Created: def456 (tags: test, batch-demo)
      Created: ghi789 (tags: test, batch-demo)

    Step 2: Adding tag 'processed' to all annotations...
      Updated: abc123 -> test, batch-demo, processed
      Updated: def456 -> test, batch-demo, processed
      Updated: ghi789 -> test, batch-demo, processed

    Step 3: Removing tag 'test' from all annotations...
      Updated: abc123 -> batch-demo, processed
      Updated: def456 -> batch-demo, processed
      Updated: ghi789 -> batch-demo, processed

    Step 4: Cleanup
    Delete all test annotations? [y/N]: y
    Deleted 3 annotation(s).
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


def add_tag(api, annotation_id, new_tag):
    """Add a tag to an annotation without removing existing tags."""
    # Get current annotation
    ann = api.get_annotation(annotation_id)
    current_tags = ann.get("tags", [])

    # Add new tag if not already present
    if new_tag not in current_tags:
        updated_tags = current_tags + [new_tag]
        api.update(annotation_id, {"tags": updated_tags})
        return updated_tags
    return current_tags


def remove_tag(api, annotation_id, tag_to_remove):
    """Remove a tag from an annotation."""
    # Get current annotation
    ann = api.get_annotation(annotation_id)
    current_tags = ann.get("tags", [])

    # Remove tag if present
    if tag_to_remove in current_tags:
        updated_tags = [t for t in current_tags if t != tag_to_remove]
        api.update(annotation_id, {"tags": updated_tags})
        return updated_tags
    return current_tags


def main():
    api = get_api()
    annotation_ids = []

    print("=" * 60)
    print("Batch Tag Update Demo")
    print("=" * 60)

    try:
        # Step 1: Create test annotations
        print("\nStep 1: Creating 3 test annotations...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for i in range(1, 4):
            payload = {
                "uri": DEFAULT_URI,
                "text": f"Test annotation #{i} for batch tag demo.\n"
                        f"Created at: {timestamp}",
                "tags": ["test", "batch-demo"]
            }
            result = api.create(payload)
            annotation_ids.append(result["id"])
            short_id = result["id"][:6]
            print(f"  Created: {short_id} (tags: {', '.join(result.get('tags', []))})")

        # Step 2: Add a tag to all annotations
        print("\nStep 2: Adding tag 'processed' to all annotations...")

        for ann_id in annotation_ids:
            updated_tags = add_tag(api, ann_id, "processed")
            short_id = ann_id[:6]
            print(f"  Updated: {short_id} -> {', '.join(updated_tags)}")

        # Step 3: Remove a tag from all annotations
        print("\nStep 3: Removing tag 'test' from all annotations...")

        for ann_id in annotation_ids:
            updated_tags = remove_tag(api, ann_id, "test")
            short_id = ann_id[:6]
            print(f"  Updated: {short_id} -> {', '.join(updated_tags)}")

        # Show final state
        print("\nFinal state:")
        for ann_id in annotation_ids:
            ann = api.get_annotation(ann_id)
            short_id = ann_id[:6]
            print(f"  {short_id}: {', '.join(ann.get('tags', []))}")

        # Step 4: Cleanup
        print("\nStep 4: Cleanup")
        try:
            response = input("Delete all test annotations? [y/N]: ")
        except EOFError:
            response = "n"
            print("(non-interactive mode, keeping annotations)")

        if response.lower() == "y":
            for ann_id in annotation_ids:
                api.delete(ann_id)
            print(f"Deleted {len(annotation_ids)} annotation(s).")
            annotation_ids = []
        else:
            print("Annotations kept. IDs:")
            for ann_id in annotation_ids:
                print(f"  {ann_id}")

    except HypothesisAPIError as e:
        print(f"\nError: {e}")
        sys.exit(1)
    finally:
        # Cleanup on error
        if annotation_ids:
            print(f"\nNote: {len(annotation_ids)} annotation(s) still exist.")
            print("Clean up with:")
            for ann_id in annotation_ids:
                print(f"  api.delete('{ann_id}')")


if __name__ == "__main__":
    main()
