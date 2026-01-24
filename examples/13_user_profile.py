#!/usr/bin/env python3
"""
Example 13: Display User Profile

Demonstrates how to retrieve and display the authenticated user's profile
information, including account details and group memberships.

Usage:
    python 13_user_profile.py

Sample Output:
    ============================================================
    Your Hypothesis Profile
    ============================================================

    Account Information:
      User ID:     acct:rdhyee@hypothes.is
      Username:    rdhyee
      Authority:   hypothes.is
      Display:     Raymond Yee

    Features:
      - embed_cachebuster: True
      - client_oauth: False

    Groups (3):
      - Public (__world__)
      - My Research Group (abc123)
      - Team Annotations (def456)

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


def main():
    api = get_api()

    print("=" * 60)
    print("Your Hypothesis Profile")
    print("=" * 60)

    try:
        # Get profile information
        profile = api.get_profile()

        # Display account info
        print("\nAccount Information:")
        userid = profile.get("userid", "")
        print(f"  User ID:     {userid}")

        # Parse username and authority from userid
        if userid.startswith("acct:"):
            parts = userid.split(":")[1]
            if "@" in parts:
                username, authority = parts.split("@")
                print(f"  Username:    {username}")
                print(f"  Authority:   {authority}")

        # Display name if available
        user_info = profile.get("user_info", {})
        display_name = user_info.get("display_name")
        if display_name:
            print(f"  Display:     {display_name}")

        # Display features
        features = profile.get("features", {})
        if features:
            print("\nFeatures:")
            for feature, enabled in sorted(features.items())[:5]:
                print(f"  - {feature}: {enabled}")
            if len(features) > 5:
                print(f"  ... and {len(features) - 5} more")

        # Display groups
        groups = profile.get("groups", [])
        if groups:
            print(f"\nGroups ({len(groups)}):")
            for group in groups[:10]:
                name = group.get("name", "Unnamed")
                group_id = group.get("id", group.get("pubid", "?"))
                print(f"  - {name} ({group_id})")
            if len(groups) > 10:
                print(f"  ... and {len(groups) - 10} more")

        # Additional profile fields
        print()
        print("-" * 60)
        print("Additional Profile Data:")

        # Preferences
        preferences = profile.get("preferences", {})
        if preferences:
            print("\nPreferences:")
            for key, value in preferences.items():
                print(f"  {key}: {value}")

        print()
        print("=" * 60)
        print("API Methods for Profile:")
        print("  get_profile()       - Get your profile")
        print("  get_profile_groups() - Get groups with more details")
        print("=" * 60)

    except HypothesisAPIError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
