# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python wrapper for the [Hypothesis](https://hypothes.is/) web annotation API. Enables programmatic creation, retrieval, and search of web annotations.

## Common Commands

```bash
# Install package (development)
pip install -e .

# Run tests
python setup.py test
# or
make test

# Lint
make lint  # uses flake8

# Build documentation
make docs

# Build distribution
make dist

# Clean build artifacts
make clean
```

## Architecture

The library is a single-module package in `hypothesisapi/__init__.py`:

- **`API` class**: Main interface for Hypothesis API interactions
  - Constructor takes `username` and `api_key` (bearer token authentication)
  - `create(payload)`: Create annotations (requires `uri` in payload)
  - `get_annotation(_id)`: Retrieve single annotation by ID
  - `search(...)`: Generator that paginates through search results (handles offset automatically)

## Authentication

Uses Bearer token authentication via Hypothesis API keys (not username/password login). Get your API key from https://hypothes.is/account/developer

## Key API Endpoints

- Base API URL: `https://hypothes.is/api`
- Create annotation: `POST /annotations`
- Get annotation: `GET /annotations/:id`
- Search: `GET /search?{params}`

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
```
