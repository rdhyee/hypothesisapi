# Hypothesis API Examples

This directory contains example scripts demonstrating how to use the `hypothesisapi` library.

## Quick Start

### 1. Install the library

```bash
pip install -e ..
```

### 2. Set up authentication

Get your API key from [https://hypothes.is/account/developer](https://hypothes.is/account/developer)

```bash
export HYPOTHESIS_API_KEY=your_api_key_here
export HYPOTHESIS_USERNAME=your_username
```

### 3. Run an example

```bash
python 01_read_annotation.py
```

## Examples Overview

### Basic Operations (Read-Only)

| Example | Description |
|---------|-------------|
| `01_read_annotation.py` | Read a single annotation by ID |
| `02_collection_stats.py` | Gather statistics about a collection of annotations |
| `03_search_by_uri.py` | Search annotations by URL (exact and wildcard) |
| `04_search_by_tag.py` | Search annotations by tag (single and multiple) |

### Create/Update/Delete Operations

| Example | Description |
|---------|-------------|
| `05_create_annotation.py` | Create a new annotation with optional cleanup |
| `06_update_annotation.py` | Create, update, and compare annotation versions |
| `07_temporary_annotation.py` | Create a self-deleting temporary annotation |

### Bulk Operations

| Example | Description |
|---------|-------------|
| `08_export_annotations.py` | Export annotations to JSON and CSV formats |
| `09_batch_tag_update.py` | Add/remove tags from multiple annotations |

### Groups

| Example | Description |
|---------|-------------|
| `10_list_groups.py` | List all groups you have access to |
| `11_create_group.py` | Create a new private group |
| `12_search_group_annotations.py` | Search annotations within a specific group |

### Profile & Discovery

| Example | Description |
|---------|-------------|
| `13_user_profile.py` | Display your user profile information |
| `14_recent_annotations.py` | Show recent annotations with context |

## Fixture Annotations

Several examples use fixture annotations for demonstration. These are public
annotations tagged with `#hypothesisapi-example` on the Wikipedia
[Web annotation](https://en.wikipedia.org/wiki/Web_annotation) article.

### Setting up fixtures

```bash
python setup_fixtures.py
```

This creates 5 fixture annotations:
1. **Page note** - A simple note not anchored to text
2. **Highlight** - Text anchored with a comment
3. **Multi-tag** - Annotation with multiple tags
4. **Reply** - A reply to another annotation
5. **Visibility demo** - Documents privacy options (PUBLIC annotation)

See [FIXTURES.md](FIXTURES.md) for fixture annotation IDs.

### Using existing fixtures

The examples will automatically search for fixtures by tag. If fixtures exist,
they'll be used; if not, you'll be prompted to create them.

## Common Patterns

### Authentication

All examples use environment variables for authentication:

```python
import os
from hypothesisapi import API

api = API(
    username=os.environ.get("HYPOTHESIS_USERNAME"),
    api_key=os.environ.get("HYPOTHESIS_API_KEY")
)
```

### Error handling

```python
from hypothesisapi import API, HypothesisAPIError, NotFoundError

try:
    annotation = api.get_annotation("invalid-id")
except NotFoundError:
    print("Annotation not found")
except HypothesisAPIError as e:
    print(f"API error: {e}")
```

### Search with pagination

The `search()` method returns a generator that automatically handles pagination:

```python
# Iterate through all matching annotations
for annotation in api.search(tag="python", limit=100):
    print(annotation["text"])

# Get all results as a list
annotations = list(api.search(user="username"))
```

### Self-contained examples

Write examples (05-09, 11) follow a create-use-cleanup pattern:

```python
# Create
result = api.create({"uri": "...", "text": "..."})
annotation_id = result["id"]

try:
    # Use
    # ... do something with the annotation ...

finally:
    # Cleanup (optional)
    api.delete(annotation_id)
```

## Running All Examples

To run all read-only examples:

```bash
for f in 01_*.py 02_*.py 03_*.py 04_*.py 10_*.py 13_*.py 14_*.py; do
    echo "Running $f..."
    python "$f"
    echo
done
```

## Troubleshooting

### "HYPOTHESIS_API_KEY not set"

Make sure you've exported the environment variable:

```bash
export HYPOTHESIS_API_KEY=your_api_key_here
```

### "No annotations found"

- For fixture-based examples, run `setup_fixtures.py` first
- Check that you're searching the right user/tag/URI
- Verify your API key has the correct permissions

### Rate limiting

The Hypothesis API has rate limits. If you hit them:
- Wait a few minutes before retrying
- Reduce the frequency of API calls
- Use pagination with reasonable limits

## Shared Helpers

The `_common.py` module provides shared utilities used across examples:

```python
from _common import (
    get_api,              # Initialize API from environment
    parse_date,           # Parse ISO dates (timezone-aware)
    format_date,          # Format datetime for display
    extract_username,     # Extract username from acct:user@domain
    format_user_for_search,  # Format username for API search
    truncate,             # Truncate text with ellipsis
    extract_quote,        # Get highlighted text from annotation
    FIXTURE_TAG,          # Common fixture tag
    WIKIPEDIA_URL,        # Fixture target URL
)
```

## Contributing

When adding new examples:

1. Follow the naming convention: `XX_descriptive_name.py`
2. Include a comprehensive docstring with usage and sample output
3. Use helpers from `_common.py` to reduce duplication
4. Support `HYPOTHESIS_API_KEY` environment variable
5. Include error handling for common cases
6. For write operations, include cleanup options
