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
| `reindex(id)` | Reindex annotation | Admin |
| `moderation(id, hidden)` | Update moderation status | Moderator |
| `search(...)` | Search with pagination | User |
| `search_raw(...)` | Single-page search | User |

*Public annotations are readable by anyone; private annotations require appropriate permissions.

### Bulk Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `bulk(operations)` | Perform batch operations | User |
| `bulk_annotations(...)` | Bulk retrieve annotations | User |
| `bulk_groups(...)` | Bulk retrieve groups | User |
| `bulk_lms_annotations(...)` | LMS annotation retrieval | User |

### Group Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `get_groups()` | List accessible groups | User |
| `create_group(name, description)` | Create private group | User |
| `get_group(id)` | Get group details | Member |
| `update_group(id, name, description)` | Update group | Owner |
| `get_group_annotations(id)` | Get all annotations in group | Member |
| `get_group_members(id)` | List members | Member |
| `add_group_member(id, userid)` | Add user to group | Admin/Owner |
| `get_group_member(id, userid)` | Get member details | Member |
| `update_group_member(id, userid, roles)` | Change member role | Admin/Owner |
| `remove_group_member(id, userid)` | Remove user from group | Admin/Owner |
| `leave_group(id)` | Leave group | Member |

### Profile Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `get_profile()` | Get current user profile | User |
| `get_profile_groups()` | Get user's groups | User |
| `update_profile(preferences)` | Update user preferences | User |

### User Methods (Admin Only)

| Method | Description | Permission |
|--------|-------------|------------|
| `create_user(...)` | Create new user | Admin |
| `get_user(userid)` | Get user info | Admin |
| `update_user(userid, ...)` | Update user | Admin |

### Analytics Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `create_analytics_event(type, properties)` | Track analytics event | User |

### Utility Methods

| Method | Description | Permission |
|--------|-------------|------------|
| `root()` | Get API information | Public |
| `get_links()` | Get URL templates | Public |

---

## API Comprehensiveness

This section analyzes what the Hypothesis API covers compared to all available functionality, and what this Python wrapper implements.

### Python Wrapper: 100% API Coverage

This library (`hypothesisapi`) now implements **all** Hypothesis API v1.0 endpoints. Every documented API endpoint has a corresponding Python method.

#### Complete API Coverage Table

| API Endpoint | Method | Description |
|--------------|--------|-------------|
| **Annotations** | | |
| `POST /api/annotations` | `create()` | Create annotation |
| `GET /api/annotations/:id` | `get_annotation()` | Get annotation |
| `PATCH /api/annotations/:id` | `update()` | Update annotation |
| `DELETE /api/annotations/:id` | `delete()` | Delete annotation |
| `PUT /api/annotations/:id/flag` | `flag()` | Flag for review |
| `PUT /api/annotations/:id/hide` | `hide()` | Hide annotation (moderator) |
| `DELETE /api/annotations/:id/hide` | `unhide()` | Unhide annotation (moderator) |
| `POST /api/annotations/:id/reindex` | `reindex()` | Reindex annotation (admin) |
| `PATCH /api/annotations/:id/moderation` | `moderation()` | Update moderation status |
| **Search** | | |
| `GET /api/search` | `search()` | Paginated search (generator) |
| `GET /api/search` | `search_raw()` | Single-page search |
| **Bulk Operations** | | |
| `POST /api/bulk` | `bulk()` | Batch operations |
| `POST /api/bulk/annotation` | `bulk_annotations()` | Bulk annotation retrieval |
| `POST /api/bulk/group` | `bulk_groups()` | Bulk group retrieval |
| `POST /api/bulk/lms/annotations` | `bulk_lms_annotations()` | LMS annotation retrieval |
| **Groups** | | |
| `GET /api/groups` | `get_groups()` | List groups |
| `POST /api/groups` | `create_group()` | Create group |
| `GET /api/groups/:id` | `get_group()` | Get group details |
| `PATCH /api/groups/:id` | `update_group()` | Update group |
| `GET /api/groups/:id/annotations` | `get_group_annotations()` | Get group annotations |
| `GET /api/groups/:id/members` | `get_group_members()` | List group members |
| `POST /api/groups/:id/members/:userid` | `add_group_member()` | Add member to group |
| `GET /api/groups/:id/members/:userid` | `get_group_member()` | Get member details |
| `PATCH /api/groups/:id/members/:userid` | `update_group_member()` | Update member role |
| `DELETE /api/groups/:id/members/:userid` | `remove_group_member()` | Remove member |
| `DELETE /api/groups/:id/members/me` | `leave_group()` | Leave group |
| **Profile** | | |
| `GET /api/profile` | `get_profile()` | Get user profile |
| `PATCH /api/profile` | `update_profile()` | Update preferences |
| `GET /api/profile/groups` | `get_profile_groups()` | Get user's groups |
| **Users (Admin)** | | |
| `POST /api/users` | `create_user()` | Create user |
| `GET /api/users/:userid` | `get_user()` | Get user |
| `PATCH /api/users/:username` | `update_user()` | Update user |
| **Analytics** | | |
| `POST /api/analytics/events` | `create_analytics_event()` | Track events |
| **Links** | | |
| `GET /api/links` | `get_links()` | Get URL templates |
| **Root** | | |
| `GET /api` | `root()` | API information |

### What the API Provides vs What It Doesn't

The Hypothesis API provides programmatic access to annotation functionality, but some features are only available through the website or browser extension.

#### Available via API (and this library)

| Category | Capabilities |
|----------|-------------|
| **Annotations** | Full CRUD, search, flagging, moderation, bulk retrieval |
| **Groups** | Create, read, update, full membership management |
| **Search** | Comprehensive filtering, pagination, wildcards |
| **Profile** | Read profile, update preferences |
| **Users** | Admin operations for third-party authorities |
| **Bulk Operations** | Batch retrieval for annotations and groups |
| **Analytics** | Event tracking |

#### NOT Available via API

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
| Real-time updates | WebSocket-based, not REST |
| Joining groups via invite | Requires clicking invite link |

### API vs Website Feature Matrix

| Feature | API | Website | Extension | This Library |
|---------|-----|---------|-----------|--------------|
| Create annotation | Yes | Yes | Yes | Yes |
| Anchored annotations | Yes* | Yes | Yes | Yes* |
| Page notes | Yes | Yes | Yes | Yes |
| Replies | Yes | Yes | Yes | Yes |
| Search annotations | Yes | Yes | No | Yes |
| Bulk operations | Yes | No | No | Yes |
| Create groups | Yes | Yes | No | Yes |
| Add/remove members | Yes | Yes | No | Yes |
| Manage group roles | Yes | Yes | No | Yes |
| Join groups (invite) | No | Yes | Yes | No |
| Real-time updates | No | Yes | Yes | No |
| PDF annotation | Yes* | No | Yes | Yes* |
| Track analytics | Yes | Auto | Auto | Yes |
| Account settings | Partial | Yes | No | Partial |

*Anchored annotations and PDF support require constructing proper selectors, which the API accepts but the library doesn't help generate.

### New Methods (Recently Added)

These methods complete the API coverage:

#### Annotation Moderation
```python
# Reindex an annotation (admin)
api.reindex("annotation_id")

# Update moderation status
api.moderation("annotation_id", hidden=True)
```

#### Bulk Operations
```python
# Retrieve many annotations efficiently
result = api.bulk_annotations(group="group_id")

# Retrieve many groups
result = api.bulk_groups(group_ids=["id1", "id2"])

# LMS-specific bulk retrieval
result = api.bulk_lms_annotations(group_ids=["id1"])
```

#### Group Membership Management
```python
# Add a user to a group
api.add_group_member("group_id", "acct:user@hypothes.is")

# Get member details
member = api.get_group_member("group_id", "acct:user@hypothes.is")

# Update member role (promote to moderator)
api.update_group_member("group_id", "acct:user@hypothes.is", roles=["moderator"])

# Remove a member
api.remove_group_member("group_id", "acct:user@hypothes.is")

# Get all annotations in a group directly
result = api.get_group_annotations("group_id")
```

#### Profile Management
```python
# Update profile preferences
api.update_profile({"notifications": {"reply": True}})
```

#### Analytics & Links
```python
# Track an analytics event
api.create_analytics_event("page_view", {"url": "https://example.com"})

# Get URL templates
links = api.get_links()
```

### Recommendations

1. **This library provides complete API coverage** for:
   - Building annotation tools and integrations
   - Exporting and analyzing annotations (including bulk operations)
   - Automating annotation workflows
   - Full group management including membership
   - Analytics tracking

2. **Use the website/extension for:**
   - Account registration and management
   - Joining groups via invite links
   - Real-time collaborative annotation
   - The visual annotation experience

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
