# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python wrapper for the [Hypothesis](https://hypothes.is/) web annotation API. Enables programmatic creation, retrieval, update, and search of web annotations.

## Common Commands

```bash
# Install package (development)
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy hypothesisapi

# Lint
flake8 hypothesisapi tests

# Build distribution
pip install build
python -m build

# Clean build artifacts
rm -rf build/ dist/ *.egg-info
```

## Architecture

The library is a single-module package in `hypothesisapi/__init__.py`:

### Main Class: `API`

Constructor: `API(username, api_key, api_url=API_URL, app_url=APP_URL)`

**Annotation Methods:**
- `create(payload, group="__world__")`: Create annotation (requires `uri` in payload)
- `get_annotation(annotation_id)`: Retrieve single annotation by ID
- `update(annotation_id, payload)`: Update an annotation
- `delete(annotation_id)`: Delete an annotation
- `flag(annotation_id)`: Flag annotation for review
- `hide(annotation_id)`: Hide annotation (moderator)
- `unhide(annotation_id)`: Unhide annotation (moderator)
- `search(...)`: Generator that paginates through search results
- `search_raw(...)`: Single-page search returning full response

**Group Methods:**
- `get_groups(authority, document_uri, expand)`: List groups
- `create_group(name, description, groupid)`: Create private group
- `get_group(group_id, expand)`: Get group details
- `update_group(group_id, name, description)`: Update group
- `get_group_members(group_id)`: List group members
- `leave_group(group_id)`: Leave a group

**Profile Methods:**
- `get_profile()`: Get current user's profile
- `get_profile_groups(...)`: Get user's groups

**User Methods (Admin):**
- `create_user(authority, username, email, ...)`: Create user
- `get_user(userid)`: Get user by ID
- `update_user(userid, email, display_name)`: Update user

### Custom Exceptions

- `HypothesisAPIError`: Base exception
- `AuthenticationError`: 401 errors
- `NotFoundError`: 404 errors
- `ForbiddenError`: 403 errors (named to avoid shadowing Python's builtin `PermissionError`)

## Authentication

Uses Bearer token authentication via Hypothesis API keys. Get your API key from https://hypothes.is/account/developer

## API Version

This library uses **Hypothesis API v1.0** (the current stable version). API v2.0 is experimental and under development.

## Key API Endpoints

- Base API URL: `https://hypothes.is/api`
- Annotations: `/annotations`, `/annotations/:id`, `/annotations/:id/flag`, `/annotations/:id/hide`
- Groups: `/groups`, `/groups/:id`, `/groups/:id/members`
- Profile: `/profile`, `/profile/groups`
- Users: `/users`, `/users/:userid`
- Search: `/search?{params}`

## Example Usage

```python
from hypothesisapi import API

api = API(username="your_username", api_key="your_api_key")

# Create annotation
result = api.create({
    "uri": "https://example.com",
    "text": "My annotation text",
    "tags": ["tag1", "tag2"]
})

# Search annotations
for annotation in api.search(user="username", uri="https://example.com"):
    print(annotation)

# Update annotation
api.update("annotation_id", {"text": "Updated text"})

# Delete annotation
api.delete("annotation_id")

# Work with groups
groups = api.get_groups()
new_group = api.create_group("My Group", description="A test group")

# Get profile
profile = api.get_profile()
```

## Testing

Tests are in the `tests/` directory. Run with `pytest`.

## Type Hints

The package is fully typed. Use `mypy hypothesisapi` to check types. A `py.typed` marker file is included.
