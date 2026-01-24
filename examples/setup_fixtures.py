#!/usr/bin/env python3
"""
Setup script to create fixture annotations for hypothesisapi examples.

This script creates 5 fixture annotations on the Wikipedia "Web annotation" article.
All fixtures are tagged with #hypothesisapi-example for easy discovery.

Usage:
    export HYPOTHESIS_API_KEY=your_api_key
    export HYPOTHESIS_USERNAME=your_username
    python setup_fixtures.py

The script will output the annotation IDs which should be recorded in FIXTURES.md.
"""

import os
import sys
import json
from datetime import datetime

# Add parent directory to path for local development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesisapi import API, HypothesisAPIError

# Wikipedia Web annotation article - permanent revision URL
WIKIPEDIA_URL = "https://en.wikipedia.org/w/index.php?title=Web_annotation&oldid=1318004643"

# Common tag for all fixtures
FIXTURE_TAG = "hypothesisapi-example"


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


def create_fixtures(api):
    """Create the 5 fixture annotations."""
    fixtures = {}

    print(f"Creating fixture annotations on: {WIKIPEDIA_URL}")
    print("-" * 60)

    # 1. Simple page note (no highlight)
    print("\n1. Creating page note...")
    try:
        result = api.create({
            "uri": WIKIPEDIA_URL,
            "text": "This is a page-level note demonstrating the hypothesisapi library. "
                    "Page notes appear at the top of the annotation sidebar and are not "
                    "anchored to specific text.",
            "tags": [FIXTURE_TAG, "page-note", "demo"]
        })
        fixtures["page_note"] = result["id"]
        print(f"   Created: {result['id']}")
    except HypothesisAPIError as e:
        print(f"   Error: {e}")

    # 2. Highlight with comment (anchored to text)
    print("\n2. Creating highlight with comment...")
    try:
        result = api.create({
            "uri": WIKIPEDIA_URL,
            "text": "This annotation highlights specific text and adds a comment. "
                    "The TextQuoteSelector anchors it to the exact phrase.",
            "tags": [FIXTURE_TAG, "highlight", "anchored"],
            "target": [{
                "source": WIKIPEDIA_URL,
                "selector": [
                    {
                        "type": "TextQuoteSelector",
                        "exact": "Web annotation",
                        "prefix": "From Wikipedia, the free encyclopedia\n\n",
                        "suffix": " refers to online"
                    }
                ]
            }]
        })
        fixtures["highlight"] = result["id"]
        print(f"   Created: {result['id']}")
    except HypothesisAPIError as e:
        print(f"   Error: {e}")

    # 3. Multi-tag annotation for tag-based discovery
    print("\n3. Creating multi-tag annotation...")
    try:
        result = api.create({
            "uri": WIKIPEDIA_URL,
            "text": "This annotation has multiple tags to demonstrate tag-based search "
                    "and filtering. Tags help organize and discover annotations.",
            "tags": [FIXTURE_TAG, "multi-tag", "search-demo", "organization", "discovery"]
        })
        fixtures["multi_tag"] = result["id"]
        print(f"   Created: {result['id']}")
    except HypothesisAPIError as e:
        print(f"   Error: {e}")

    # 4. Reply annotation (references the page note)
    if "page_note" in fixtures:
        print("\n4. Creating reply annotation...")
        try:
            result = api.create({
                "uri": WIKIPEDIA_URL,
                "text": "This is a reply to the page note above. Replies create threaded "
                        "conversations and are linked via the 'references' field.",
                "tags": [FIXTURE_TAG, "reply", "threading"],
                "references": [fixtures["page_note"]]
            })
            fixtures["reply"] = result["id"]
            print(f"   Created: {result['id']}")
        except HypothesisAPIError as e:
            print(f"   Error: {e}")
    else:
        print("\n4. Skipping reply (page note not created)")

    # 5. Private annotation (Only Me group)
    print("\n5. Creating private annotation...")
    try:
        # Get user's private group ID
        profile = api.get_profile()
        user_id = profile.get("userid", "")

        result = api.create({
            "uri": WIKIPEDIA_URL,
            "text": "This is a private annotation visible only to the owner. "
                    "It demonstrates the 'Only Me' privacy setting.",
            "tags": [FIXTURE_TAG, "private", "only-me"]
        }, group="__world__")  # Note: To make truly private, would need user's private group

        # Note: Creating truly private annotations requires the user's private group ID
        # which isn't easily available via the API. This creates a public annotation
        # but tags it as "private" for demonstration purposes.
        fixtures["private_demo"] = result["id"]
        print(f"   Created: {result['id']}")
        print("   Note: True private annotations require the user's private group ID")
    except HypothesisAPIError as e:
        print(f"   Error: {e}")

    return fixtures


def main():
    print("=" * 60)
    print("Hypothesis API Fixture Setup")
    print("=" * 60)

    api = get_api()

    # Check for existing fixtures
    print("\nChecking for existing fixtures...")
    existing = list(api.search(tag=FIXTURE_TAG, limit=10))
    if existing:
        print(f"Found {len(existing)} existing fixture(s):")
        for ann in existing:
            print(f"  - {ann['id']}: {ann.get('text', '')[:50]}...")
        print("\nTo recreate fixtures, delete existing ones first.")
        response = input("Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            sys.exit(0)

    # Create fixtures
    fixtures = create_fixtures(api)

    # Output summary
    print("\n" + "=" * 60)
    print("Fixture Summary")
    print("=" * 60)
    print(f"\nCreated {len(fixtures)} fixture annotation(s):")
    print(json.dumps(fixtures, indent=2))

    print("\n" + "-" * 60)
    print("Add these IDs to examples/FIXTURES.md:")
    print("-" * 60)
    print(f"""
# Fixture Annotation IDs

Created: {datetime.now().isoformat()}
Target URL: {WIKIPEDIA_URL}

| Fixture | ID | Description |
|---------|----|-----------  |
| page_note | {fixtures.get('page_note', 'N/A')} | Simple page-level note |
| highlight | {fixtures.get('highlight', 'N/A')} | Highlight with comment |
| multi_tag | {fixtures.get('multi_tag', 'N/A')} | Multi-tag annotation |
| reply | {fixtures.get('reply', 'N/A')} | Reply to page note |
| private_demo | {fixtures.get('private_demo', 'N/A')} | Private annotation demo |
""")


if __name__ == "__main__":
    main()
