# Fixture Annotations for Examples

This document contains the IDs of fixture annotations used by the read-only examples.

## Target Document

**Wikipedia Article**: [Web annotation](https://en.wikipedia.org/wiki/Web_annotation)

**Permanent URL**: `https://en.wikipedia.org/w/index.php?title=Web_annotation&oldid=1318004643`

## Discovery Tag

All fixture annotations are tagged with `#hypothesisapi-example` for easy discovery.

## Fixture IDs

> **Note**: Run `setup_fixtures.py` to create these annotations, then update this file with the generated IDs.

| Fixture | ID | Description |
|---------|----|-----------  |
| page_note | `_PENDING_` | Simple page-level note (not anchored to text) |
| highlight | `_PENDING_` | Highlight with comment (anchored to "Web annotation" text) |
| multi_tag | `_PENDING_` | Multi-tag annotation for search demos |
| reply | `_PENDING_` | Reply annotation (threaded conversation) |
| private_demo | `_PENDING_` | Private annotation demonstration |

## Setup Instructions

1. Set your environment variables:
   ```bash
   export HYPOTHESIS_API_KEY=your_api_key
   export HYPOTHESIS_USERNAME=your_username
   ```

2. Run the setup script:
   ```bash
   python setup_fixtures.py
   ```

3. Update this file with the generated annotation IDs.

## Cleanup

To remove fixtures (e.g., before recreation):

```python
from hypothesisapi import API
import os

api = API(
    username=os.environ["HYPOTHESIS_USERNAME"],
    api_key=os.environ["HYPOTHESIS_API_KEY"]
)

# Find and delete all fixtures
for ann in api.search(tag="hypothesisapi-example"):
    api.delete(ann["id"])
    print(f"Deleted: {ann['id']}")
```
