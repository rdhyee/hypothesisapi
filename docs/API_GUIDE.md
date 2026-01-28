# Hypothesis API Guide

This guide explains the capabilities of the `hypothesisapi` Python library and how its features map to different user roles and permissions within the Hypothesis annotation system.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [User Roles and Permissions](#user-roles-and-permissions)
- [Annotation Operations](#annotation-operations)
- [Search and Discovery](#search-and-discovery)
- [Group Management](#group-management)
- [Profile Access](#profile-access)
- [Moderation Features](#moderation-features)
- [Admin Operations](#admin-operations)
- [Error Handling](#error-handling)
- [Common Use Cases](#common-use-cases)

---

## Overview

The `hypothesisapi` library provides programmatic access to the [Hypothesis](https://hypothes.is/) web annotation platform. Hypothesis allows users to annotate web pages, PDFs, and other documents collaboratively.

### What You Can Do

| Feature | Regular User | Moderator | Admin |
|---------|-------------|-----------|-------|
| Create annotations | Yes | Yes | Yes |
| Read public annotations | Yes | Yes | Yes |
| Read private/group annotations | Own only | Yes* | Yes |
| Update annotations | Own only | Own only | Yes |
| Delete annotations | Own only | Own only | Yes |
| Flag annotations | Yes | Yes | Yes |
| Hide/unhide annotations | No | Yes | Yes |
| Create/manage groups | Yes | Yes | Yes |
| Create/manage users | No | No | Yes |

*Moderators can access annotations in groups they moderate.

---

## Getting Started

### Installation

```bash
pip install hypothesisapi
```

### Authentication

All API operations require authentication via an API key. Get your personal API key from: https://hypothes.is/account/developer

```python
from hypothesisapi import API

api = API(
    username="your_username",
    api_key="your_api_key"
)
```

You can also use environment variables for security:

```python
import os
from hypothesisapi import API

api = API(
    username=os.environ["HYPOTHESIS_USERNAME"],
    api_key=os.environ["HYPOTHESIS_API_KEY"]
)
```

### Testing Your Connection

```python
# Verify authentication by fetching your profile
profile = api.get_profile()
print(f"Logged in as: {profile['userid']}")
```

---

## User Roles and Permissions

The Hypothesis platform has several user roles with different capabilities:

### Regular Users

Every registered Hypothesis user can:

- **Create annotations** on any web page
- **Read** their own annotations and public annotations
- **Update and delete** their own annotations
- **Search** for annotations by URL, tag, text, or user
- **Create private groups** for collaboration
- **Join and leave** groups
- **Flag** inappropriate content for review

### Moderators

Group moderators have additional powers within their groups:

- **Hide** inappropriate annotations from public view
- **Unhide** previously hidden annotations
- View all annotations in groups they moderate

### Administrators (Third-Party Authorities)

Organizations running their own Hypothesis instance can:

- **Create users** within their authority domain
- **Manage users** (update profiles, etc.)
- **Full access** to all annotations within their authority

---

## Annotation Operations

Annotations are the core objects in Hypothesis. Each annotation consists of:

- **URI**: The web page or document being annotated
- **Text**: The annotation content (optional for highlights)
- **Tags**: Categorization labels
- **Target**: What text is highlighted (for anchored annotations)
- **Permissions**: Who can read, update, delete the annotation

### Creating Annotations

```python
# Simple page note (not anchored to specific text)
result = api.create({
    "uri": "https://example.com/article",
    "text": "This is a great article about annotations!",
    "tags": ["review", "favorite"]
})
annotation_id = result["id"]
```

**Required fields:**
- `uri`: The URL of the page being annotated

**Optional fields:**
- `text`: The annotation body (supports Markdown)
- `tags`: List of tag strings
- `document`: Metadata about the document
- `target`: Selector information for anchored annotations
- `references`: Parent annotation ID (for replies)
- `group`: Group ID (defaults to `__world__` for public)

### Creating Annotations in Groups

```python
# Create annotation in a private group
result = api.create(
    payload={
        "uri": "https://example.com/article",
        "text": "Team review note"
    },
    group="your_group_id"  # Get this from get_groups()
)
```

### Creating Replies

```python
# Reply to an existing annotation
result = api.create({
    "uri": "https://example.com/article",
    "text": "I agree with your point!",
    "references": ["parent_annotation_id"]
})
```

### Reading Annotations

```python
# Get a single annotation by ID
annotation = api.get_annotation("annotation_id")

print(f"Text: {annotation['text']}")
print(f"Created: {annotation['created']}")
print(f"Author: {annotation['user']}")
print(f"Tags: {annotation.get('tags', [])}")
```

For public annotations, authentication is optional:

```python
# Read public annotation without authentication
annotation = api.get_annotation("annotation_id", authenticated=False)
```

### Updating Annotations

You can only update annotations you own:

```python
# Update text and tags
updated = api.update("annotation_id", {
    "text": "Updated annotation text with more details",
    "tags": ["updated", "reviewed"]
})
```

**Updatable fields:**
- `text`: New annotation content
- `tags`: Replace all tags
- `permissions`: Change visibility

### Deleting Annotations

You can only delete annotations you own:

```python
# Delete an annotation
result = api.delete("annotation_id")
# Returns: {"id": "annotation_id", "deleted": True}
```

### Flagging Annotations

Any user can flag content for moderator review:

```python
# Flag inappropriate content
api.flag("annotation_id")
```

---

## Search and Discovery

The search functionality is one of the most powerful features, allowing you to find annotations across the entire Hypothesis corpus.

### Basic Search

```python
# Search returns a generator that handles pagination automatically
for annotation in api.search(user="username"):
    print(annotation["text"])

# Convert to list (loads all results into memory)
all_annotations = list(api.search(user="username"))
```

### Search Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `user` | Filter by username | `user="janedoe"` |
| `uri` | Exact URL match | `uri="https://example.com"` |
| `wildcard_uri` | URL pattern with wildcards | `wildcard_uri="https://example.com/*"` |
| `tag` | Single tag filter | `tag="python"` |
| `tags` | Multiple tags (all must match) | `tags=["python", "tutorial"]` |
| `text` | Search annotation text | `text="important concept"` |
| `any_field` | Search across multiple fields | `any_field="hypothesis"` |
| `group` | Filter by group ID | `group="group_id"` |
| `quote` | Search highlighted text | `quote="the quick brown fox"` |
| `references` | Find replies to annotation | `references="parent_id"` |

### Search by URL

```python
# Exact URL match
for ann in api.search(uri="https://en.wikipedia.org/wiki/Python"):
    print(ann["text"])

# Wildcard match - all pages under a domain
for ann in api.search(wildcard_uri="https://docs.python.org/*"):
    print(f"{ann['uri']}: {ann['text'][:50]}")
```

### Search by Tags

```python
# Single tag
for ann in api.search(tag="machine-learning"):
    print(ann["text"])

# Multiple tags (AND logic - all must match)
for ann in api.search(tags=["python", "tutorial", "beginner"]):
    print(ann["text"])
```

### Sorting and Ordering

```python
# Sort by creation date, newest first
for ann in api.search(user="username", sort="created", order="desc"):
    print(f"{ann['created']}: {ann['text'][:50]}")

# Sort options: created, updated, id, group, user
```

### Pagination Control

```python
# Limit results per page (max 200)
for ann in api.search(user="username", limit=50):
    print(ann["text"])

# Start from specific offset
for ann in api.search(user="username", offset=100, limit=50):
    print(ann["text"])
```

### Raw Search Results

For access to metadata like total count:

```python
# Get raw API response (single page only)
result = api.search_raw(user="username", limit=20)
print(f"Total matching: {result['total']}")
print(f"Returned: {len(result['rows'])}")
```

---

## Group Management

Groups enable private or semi-private annotation collections. They're useful for:

- Classroom discussions
- Team research projects
- Reading clubs
- Private note-taking

### Listing Your Groups

```python
# Get all groups you belong to
groups = api.get_groups()
for group in groups:
    print(f"{group['name']} (ID: {group['id']})")
```

### Creating a Group

```python
# Create a new private group
new_group = api.create_group(
    name="Research Team",
    description="Annotations for our research project"
)
group_id = new_group["id"]
print(f"Created group: {group_id}")
```

### Getting Group Details

```python
# Get information about a specific group
group = api.get_group("group_id")
print(f"Name: {group['name']}")
print(f"Description: {group.get('description', 'No description')}")

# Expand additional information
group = api.get_group("group_id", expand=["organization", "scopes"])
```

### Updating a Group

```python
# Update group name and/or description
api.update_group(
    "group_id",
    name="New Group Name",
    description="Updated description"
)
```

### Viewing Group Members

```python
# List members of a group
members = api.get_group_members("group_id")
for member in members:
    print(member["username"])
```

### Leaving a Group

```python
# Remove yourself from a group
api.leave_group("group_id")
```

### Searching Within Groups

```python
# Search annotations in a specific group
for ann in api.search(group="group_id"):
    print(ann["text"])
```

---

## Profile Access

Access information about the authenticated user.

### Getting Your Profile

```python
profile = api.get_profile()
print(f"User ID: {profile['userid']}")
print(f"Username: {profile['user_info']['display_name']}")
```

### Getting Your Groups via Profile

```python
# Alternative way to get your groups
groups = api.get_profile_groups()
for group in groups:
    print(f"{group['name']}: {group['id']}")
```

---

## Moderation Features

Moderators can hide inappropriate annotations from public view. These features require moderator permissions within a group.

### Hiding Annotations

When content violates community guidelines:

```python
# Hide annotation from public view (moderator only)
api.hide("annotation_id")
```

Hidden annotations:
- Are no longer visible to regular users
- Can still be seen by the author and moderators
- Can be restored later

### Unhiding Annotations

To restore a previously hidden annotation:

```python
# Unhide annotation (moderator only)
api.unhide("annotation_id")
```

### Permission Errors

Non-moderators will receive a `ForbiddenError`:

```python
from hypothesisapi import ForbiddenError

try:
    api.hide("annotation_id")
except ForbiddenError:
    print("You don't have moderator permissions for this group")
```

---

## Admin Operations

These operations are only available to administrators of third-party Hypothesis instances (organizations running their own authority).

### Creating Users

```python
# Create a user in your authority domain
user = api.create_user(
    authority="your-organization.com",
    username="newuser",
    email="newuser@your-organization.com",
    display_name="New User"
)
```

### Getting User Information

```python
# Get user by ID
user = api.get_user("acct:username@your-organization.com")
print(f"Email: {user['email']}")
print(f"Display name: {user.get('display_name')}")
```

### Updating Users

```python
# Update user profile
api.update_user(
    "acct:username@your-organization.com",
    email="newemail@your-organization.com",
    display_name="Updated Name"
)
```

### Authority Concept

The **authority** is the domain that manages a user account:

- `hypothes.is` - Public Hypothesis users
- `your-organization.com` - Users in your private instance

User IDs follow the format: `acct:username@authority`

---

## Error Handling

The library provides specific exception types for different error conditions.

### Exception Hierarchy

```
HypothesisAPIError (base)
├── AuthenticationError (401)
├── ForbiddenError (403)
└── NotFoundError (404)
```

### Handling Errors

```python
from hypothesisapi import (
    API,
    HypothesisAPIError,
    AuthenticationError,
    NotFoundError,
    ForbiddenError
)

try:
    annotation = api.get_annotation("some_id")
except AuthenticationError:
    print("Invalid API key - check your credentials")
except NotFoundError:
    print("Annotation doesn't exist or was deleted")
except ForbiddenError:
    print("You don't have permission to access this annotation")
except HypothesisAPIError as e:
    print(f"API error {e.status_code}: {e}")
```

### Error Properties

All exceptions include:

- `message`: Human-readable error description
- `status_code`: HTTP status code
- `response`: Raw response body from the API

```python
try:
    api.update("someone_elses_annotation", {"text": "new"})
except ForbiddenError as e:
    print(f"Status: {e.status_code}")  # 403
    print(f"Details: {e.response}")     # API response body
```

---

## Common Use Cases

### Personal Annotation Backup

Export all your annotations to a file:

```python
import json

annotations = list(api.search(user="your_username"))
with open("my_annotations.json", "w") as f:
    json.dump(annotations, f, indent=2)
print(f"Exported {len(annotations)} annotations")
```

### Monitor a Website for New Annotations

```python
from datetime import datetime, timedelta

# Get annotations from the last 24 hours
yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
recent = api.search_raw(
    wildcard_uri="https://your-site.com/*",
    sort="created",
    order="desc",
    limit=100
)

for ann in recent["rows"]:
    if ann["created"] > yesterday:
        print(f"New: {ann['text'][:50]}...")
```

### Batch Tag Update

Add a tag to multiple annotations:

```python
# Find annotations and add a new tag
for ann in api.search(user="your_username", tag="needs-review"):
    current_tags = ann.get("tags", [])
    if "reviewed" not in current_tags:
        api.update(ann["id"], {
            "tags": current_tags + ["reviewed"]
        })
        print(f"Updated: {ann['id']}")
```

### Research Bibliography

Collect annotations about a topic:

```python
# Search across all your annotations for a research topic
research_notes = []
for ann in api.search(user="your_username", any_field="machine learning"):
    research_notes.append({
        "url": ann["uri"],
        "quote": ann.get("target", [{}])[0].get("selector", [{}])[0].get("exact", ""),
        "note": ann.get("text", ""),
        "tags": ann.get("tags", []),
        "date": ann["created"]
    })

print(f"Found {len(research_notes)} relevant annotations")
```

### Classroom Group Management

Set up a reading group for a class:

```python
# Create group
course_group = api.create_group(
    name="CS101 Fall 2024",
    description="Course readings and discussions"
)

# Share the group ID with students
print(f"Students should join group: {course_group['id']}")

# Monitor activity
for ann in api.search(group=course_group["id"], sort="created", order="desc"):
    user = ann["user"].split(":")[1].split("@")[0]
    print(f"{user}: {ann.get('text', '(highlight)')[:50]}")
```

### Quality Assurance - Find Orphaned Annotations

Find annotations on pages that may have moved:

```python
import requests

for ann in api.search(user="your_username", limit=50):
    try:
        resp = requests.head(ann["uri"], timeout=5)
        if resp.status_code == 404:
            print(f"Broken link: {ann['uri']}")
            print(f"  Annotation: {ann['id']}")
    except requests.RequestException:
        print(f"Unreachable: {ann['uri']}")
```

---

## API Reference Summary

### Annotation Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `create(payload, group)` | Create new annotation | User |
| `get_annotation(id)` | Get annotation by ID | User* |
| `update(id, payload)` | Update annotation | Owner |
| `delete(id)` | Delete annotation | Owner |
| `flag(id)` | Flag for review | User |
| `hide(id)` | Hide annotation | Moderator |
| `unhide(id)` | Unhide annotation | Moderator |
| `search(...)` | Search with pagination | User |
| `search_raw(...)` | Single-page search | User |

*Public annotations are readable by anyone; private annotations require appropriate permissions.

### Group Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `get_groups()` | List accessible groups | User |
| `create_group(name, description)` | Create private group | User |
| `get_group(id)` | Get group details | Member |
| `update_group(id, name, description)` | Update group | Owner |
| `get_group_members(id)` | List members | Member |
| `leave_group(id)` | Leave group | Member |

### Profile Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `get_profile()` | Get current user profile | User |
| `get_profile_groups()` | Get user's groups | User |

### User Methods (Admin Only)

| Method | Description | Permission |
|--------|-------------|------------|
| `create_user(...)` | Create new user | Admin |
| `get_user(userid)` | Get user info | Admin |
| `update_user(userid, ...)` | Update user | Admin |

---

## API Comprehensiveness

This section analyzes what the Hypothesis API covers compared to all available functionality, and what this Python wrapper implements.

### Hypothesis API Coverage

The Hypothesis API v1.0 provides programmatic access to most core annotation functionality, but not everything users can do through the website or browser extension.

#### What the API Provides

| Category | Available via API |
|----------|------------------|
| Annotations | Full CRUD, search, flagging, moderation |
| Groups | Create, read, update, membership management |
| Search | Comprehensive filtering and pagination |
| Profile | Read profile, update preferences |
| Users | Admin operations for third-party authorities |
| Bulk Operations | Batch retrieval and operations |
| Analytics | Event tracking |

#### What's NOT Available via API

These features require the web interface or browser extension:

| Feature | Notes |
|---------|-------|
| Account registration | Must use hypothes.is website |
| Password management | Reset/change via website only |
| OAuth/SSO connections | Configured through account settings |
| Account deletion | Contact support or use website |
| Browser extension features | Real-time sync, sidebar UI |
| "Via" proxy | hypothes.is/via/ for viewing annotations |
| PDF viewer | Built into the browser extension |
| Email notifications | Managed in account preferences |
| Public activity stream | Available on user profile pages |

### Python Wrapper Coverage

This library (`hypothesisapi`) implements most of the Hypothesis API v1.0, but not all endpoints.

#### Implemented Endpoints

| Category | Endpoints | Status |
|----------|-----------|--------|
| **Annotations** | create, get, update, delete | Complete |
| | flag, hide, unhide | Complete |
| | search (paginated) | Complete |
| **Groups** | create, get, list, update | Complete |
| | get_members, leave | Complete |
| **Profile** | get_profile, get_profile_groups | Complete |
| **Users** | create, get, update (admin) | Complete |

#### Not Yet Implemented

These API endpoints exist but aren't wrapped by this library:

| Endpoint | Description | Use Case |
|----------|-------------|----------|
| `POST /api/bulk` | Batch operations | Efficient bulk updates |
| `POST /api/bulk/annotation` | Bulk annotation retrieval | Export large datasets |
| `POST /api/bulk/group` | Bulk group retrieval | Multi-group queries |
| `GET /api/groups/:id/annotations` | All annotations in group | Group-level export |
| `POST /api/groups/:id/members/:userid` | Add member to group | Group administration |
| `DELETE /api/groups/:id/members/:userid` | Remove member from group | Group administration |
| `PATCH /api/groups/:id/members/:userid` | Change member role | Promote/demote members |
| `PATCH /api/profile` | Update preferences | Change user settings |
| `POST /api/annotations/:id/reindex` | Reindex annotation | Admin maintenance |
| `PATCH /api/annotations/:id/moderation` | Moderation actions | Content moderation |
| `POST /api/analytics/events` | Track events | Usage analytics |
| `GET /api/links` | URL templates | Generate page URLs |

#### Workarounds for Missing Features

**Bulk annotation retrieval:** Use `search()` with pagination:
```python
# Instead of bulk endpoint, paginate through results
all_annotations = list(api.search(group="group_id"))
```

**Add user to group:** Currently requires sharing the group join link manually or using the website.

**Group annotations:** Use search with group filter:
```python
# Get all annotations in a group
for ann in api.search(group="group_id"):
    print(ann["text"])
```

### API vs Website Feature Matrix

| Feature | API | Website | Extension | This Library |
|---------|-----|---------|-----------|--------------|
| Create annotation | Yes | Yes | Yes | Yes |
| Anchored annotations | Yes* | Yes | Yes | Yes* |
| Page notes | Yes | Yes | Yes | Yes |
| Replies | Yes | Yes | Yes | Yes |
| Search annotations | Yes | Yes | No | Yes |
| Create groups | Yes | Yes | No | Yes |
| Join groups | No | Yes | Yes | No |
| Invite to groups | No | Yes | No | No |
| Manage group roles | Yes | Yes | No | No |
| Real-time updates | No | Yes | Yes | No |
| PDF annotation | Yes* | No | Yes | Yes* |
| Notifications | No | Yes | Yes | No |
| Account settings | Partial | Yes | No | Partial |

*Anchored annotations and PDF support require constructing proper selectors, which the API accepts but the library doesn't help generate.

### Recommendations

1. **For most use cases**, this library provides sufficient coverage for:
   - Building annotation tools and integrations
   - Exporting and analyzing annotations
   - Automating annotation workflows
   - Group management (basic)

2. **Use the website/extension for:**
   - Account management
   - Joining groups via invite links
   - Real-time collaborative annotation
   - Managing notification preferences

3. **Consider contributing** if you need:
   - Bulk operations
   - Advanced group membership management
   - Analytics tracking

---

## Additional Resources

- **Hypothesis Website**: https://hypothes.is/
- **API Documentation**: https://h.readthedocs.io/en/latest/api/
- **Get Your API Key**: https://hypothes.is/account/developer
- **Library Examples**: See the `examples/` directory

## Getting Help

If you encounter issues:

1. Check error messages for specific details
2. Verify your API key is valid
3. Ensure you have appropriate permissions
4. Review the [Hypothesis API documentation](https://h.readthedocs.io/en/latest/api/)
