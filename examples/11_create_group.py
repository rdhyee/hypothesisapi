#!/usr/bin/env python3
"""
Example 11: Create a Private Group

Demonstrates how to create a new private group and optionally delete it.
This is a self-contained example with cleanup.

Usage:
    python 11_create_group.py [group_name]

If no name is provided, a default test name is used.

Sample Output:
    ============================================================
    Create Private Group Demo
    ============================================================

    Creating group: API Test Group (2024-01-15)

    Group created successfully!

    Name:        API Test Group (2024-01-15)
    ID:          abc123xyz
    Type:        private
    Description: A test group created via hypothesisapi

    Share URL:   https://hypothes.is/groups/abc123xyz/api-test-group

    ============================================================

    Delete this group? [y/N]: y
    Group deleted successfully.
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
    group_id = None

    # Generate group name
    date_str = datetime.now().strftime("%Y-%m-%d")
    if len(sys.argv) > 1:
        group_name = sys.argv[1]
    else:
        group_name = f"API Test Group ({date_str})"

    print("=" * 60)
    print("Create Private Group Demo")
    print("=" * 60)
    print(f"\nCreating group: {group_name}")

    try:
        # Create the group
        result = api.create_group(
            name=group_name,
            description="A test group created via hypothesisapi. "
                        "This group demonstrates the create_group() method."
        )

        group_id = result.get("id") or result.get("pubid")

        print("\nGroup created successfully!")
        print()
        print(f"Name:        {result.get('name', group_name)}")
        print(f"ID:          {group_id}")
        print(f"Type:        {result.get('type', 'private')}")

        description = result.get("description", "")
        if description:
            print(f"Description: {description[:50]}...")

        # Show share URL if available
        links = result.get("links", {})
        if links.get("html"):
            print()
            print(f"Share URL:   {links['html']}")

        print()
        print("=" * 60)

        # Cleanup prompt
        print()
        try:
            response = input("Delete this group? [y/N]: ")
        except EOFError:
            response = "n"
            print("(non-interactive mode, keeping group)")

        if response.lower() == "y":
            # Use leave_group to remove yourself (which effectively deletes
            # a private group if you're the only member)
            try:
                api.leave_group(group_id)
                print("Left the group successfully.")
                print("(Group will be deleted if you were the only member)")
                group_id = None
            except HypothesisAPIError as e:
                print(f"Could not leave group: {e}")
                print("You may need to delete it manually from the web interface.")
        else:
            print(f"Group kept: {group_id}")
            print(f"Leave/delete later with: api.leave_group('{group_id}')")

    except HypothesisAPIError as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
