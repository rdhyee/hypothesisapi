#!/usr/bin/env python3
"""
Example 08: Export Annotations to JSON and CSV

Demonstrates how to export annotations in multiple formats for backup,
analysis, or integration with other tools.

Usage:
    python 08_export_annotations.py [tag] [--json output.json] [--csv output.csv]

If no tag is provided, uses the fixture tag 'hypothesisapi-example'.

Sample Output:
    ============================================================
    Export Annotations
    ============================================================

    Fetching annotations with tag: hypothesisapi-example
    Found 5 annotation(s)

    Exporting to JSON: annotations.json
    Exporting to CSV: annotations.csv

    Export complete!

    JSON structure:
      - Full annotation data preserved
      - Nested objects (target, document) included
      - Ready for import/backup

    CSV columns:
      id, created, updated, user, uri, text, tags, quote, group
"""

import json
import csv
import argparse
from datetime import datetime

from _common import (
    get_api, extract_quote, extract_username, format_user_for_search,
    FIXTURE_TAG
)
from hypothesisapi import HypothesisAPIError


def export_json(annotations, filename):
    """Export annotations to JSON format."""
    # Include metadata
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "count": len(annotations),
        "annotations": annotations
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)

    print(f"  Exported {len(annotations)} annotations to {filename}")


def export_csv(annotations, filename):
    """Export annotations to CSV format."""
    # Define CSV columns
    fieldnames = [
        "id", "created", "updated", "user", "uri", "title",
        "text", "tags", "quote", "group", "references"
    ]

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for ann in annotations:
            # Extract document title
            doc = ann.get("document", {})
            title = ""
            if doc.get("title"):
                title = doc["title"][0] if isinstance(doc["title"], list) else doc["title"]

            row = {
                "id": ann.get("id", ""),
                "created": ann.get("created", ""),
                "updated": ann.get("updated", ""),
                "user": extract_username(ann.get("user")),
                "uri": ann.get("uri", ""),
                "title": title,
                "text": ann.get("text", "").replace("\n", " "),
                "tags": "|".join(ann.get("tags", [])),
                "quote": extract_quote(ann),
                "group": ann.get("group", ""),
                "references": "|".join(ann.get("references", []))
            }
            writer.writerow(row)

    print(f"  Exported {len(annotations)} annotations to {filename}")


def main():
    parser = argparse.ArgumentParser(description="Export Hypothesis annotations")
    parser.add_argument("tag", nargs="?", default=FIXTURE_TAG,
                        help=f"Tag to search for (default: {FIXTURE_TAG})")
    parser.add_argument("--json", dest="json_file", default="annotations.json",
                        help="JSON output filename (default: annotations.json)")
    parser.add_argument("--csv", dest="csv_file", default="annotations.csv",
                        help="CSV output filename (default: annotations.csv)")
    parser.add_argument("--limit", type=int, default=100,
                        help="Maximum annotations to export (default: 100)")
    parser.add_argument("--user", help="Filter by username")
    parser.add_argument("--uri", help="Filter by URI")
    args = parser.parse_args()

    api = get_api()

    print("=" * 60)
    print("Export Annotations")
    print("=" * 60)
    print(f"\nFetching annotations with tag: {args.tag}")

    try:
        # Build search parameters
        search_kwargs = {"tag": args.tag, "limit": args.limit}
        if args.user:
            # Format username for API (expects acct:user@hypothes.is)
            search_kwargs["user"] = format_user_for_search(args.user)
            print(f"  Filtered by user: {args.user}")
        if args.uri:
            search_kwargs["uri"] = args.uri
            print(f"  Filtered by URI: {args.uri}")

        # Fetch annotations
        annotations = list(api.search(**search_kwargs))

        if not annotations:
            print(f"\nNo annotations found with tag '{args.tag}'.")
            print("Tip: Run setup_fixtures.py to create fixture annotations.")
            return

        print(f"Found {len(annotations)} annotation(s)")
        print()

        # Privacy warning
        has_private_groups = any(
            ann.get("group", "__world__") != "__world__"
            for ann in annotations
        )
        if has_private_groups:
            print("=" * 60)
            print("WARNING: Export includes annotations from private groups.")
            print("The exported files may contain sensitive data.")
            print("=" * 60)
            print()

        # Export to both formats
        print("Exporting...")
        export_json(annotations, args.json_file)
        export_csv(annotations, args.csv_file)

        print("\nExport complete!")
        print()
        print("-" * 60)
        print("JSON structure:")
        print("  - Full annotation data preserved")
        print("  - Nested objects (target, document) included")
        print("  - Ready for import/backup")
        print()
        print("CSV columns:")
        print("  id, created, updated, user, uri, title, text, tags, quote, group")
        print("-" * 60)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
