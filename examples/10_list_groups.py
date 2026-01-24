#!/usr/bin/env python3
"""
Example 10: List Groups

Demonstrates how to retrieve and display information about groups the
authenticated user has access to, including public and private groups.

Usage:
    python 10_list_groups.py

Sample Output:
    ============================================================
    Your Hypothesis Groups
    ============================================================

    Found 3 group(s):

    1. Public
       ID:          __world__
       Type:        open
       Description: (Public annotations visible to everyone)

    2. My Research Group
       ID:          abc123xyz
       Type:        private
       Members:     5
       Description: A group for research annotations

    3. Team Annotations
       ID:          def456abc
       Type:        restricted
       Members:     12
       Description: Team collaboration space
    ============================================================
"""

import os
import sys

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


def display_group(index, group):
    """Display information about a single group."""
    name = group.get("name", "Unnamed")
    group_id = group.get("id", group.get("pubid", "unknown"))
    group_type = group.get("type", "unknown")
    description = group.get("description", "")

    print(f"\n{index}. {name}")
    print(f"   ID:          {group_id}")
    print(f"   Type:        {group_type}")

    # Show member count if available
    if "members" in group:
        print(f"   Members:     {len(group['members'])}")

    # Show description
    if description:
        # Truncate long descriptions
        if len(description) > 60:
            description = description[:57] + "..."
        print(f"   Description: {description}")
    elif group_id == "__world__":
        print("   Description: (Public annotations visible to everyone)")

    # Show links if available
    links = group.get("links", {})
    if links.get("html"):
        print(f"   URL:         {links['html']}")


def main():
    api = get_api()

    print("=" * 60)
    print("Your Hypothesis Groups")
    print("=" * 60)

    try:
        # Get groups with expanded membership info
        groups = api.get_groups(expand=["organization", "scopes"])

        if not groups:
            print("\nNo groups found.")
            print("You are only a member of the Public group.")
            return

        print(f"\nFound {len(groups)} group(s):")

        for i, group in enumerate(groups, 1):
            display_group(i, group)

        print()
        print("=" * 60)

        # Additional group information
        print("\nGroup Types:")
        print("  - open:       Anyone can join and post")
        print("  - restricted: Anyone can read, members can post")
        print("  - private:    Only members can read and post")
        print()
        print("Use get_group(group_id) for detailed info on a specific group.")
        print("=" * 60)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
