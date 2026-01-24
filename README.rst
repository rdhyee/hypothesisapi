===============================
Hypothesis API
===============================

Python wrapper for the `Hypothesis <https://hypothes.is/>`_ web annotation API.

* Free software: BSD license
* Documentation: https://hypothesisapi.readthedocs.org

Installation
------------

.. code-block:: bash

    pip install hypothesisapi

Quick Start
-----------

.. code-block:: python

    from hypothesisapi import API

    # Initialize with your credentials
    # Get your API key at: https://hypothes.is/account/developer
    api = API(username="your_username", api_key="your_api_key")

    # Create an annotation
    annotation = api.create({
        "uri": "https://example.com",
        "text": "My annotation",
        "tags": ["example", "test"]
    })

    # Search for annotations
    for annotation in api.search(user="your_username"):
        print(annotation["text"])

    # Get a specific annotation
    annotation = api.get_annotation("annotation_id")

    # Update an annotation
    api.update("annotation_id", {"text": "Updated text"})

    # Delete an annotation
    api.delete("annotation_id")

Features
--------

**Annotations**

* Create, read, update, delete annotations
* Search with filters (user, URI, tags, text, group)
* Flag annotations for moderator review
* Hide/unhide annotations (moderator)

**Groups**

* List, create, update groups
* Get group details and members
* Leave groups

**Profile**

* Get current user profile
* List user's groups

**Users (Admin)**

* Create, read, update users (for third-party authorities)

API Version
-----------

This library uses the Hypothesis API v1.0, which is the current stable version.
API v2.0 is experimental and under development by Hypothesis.

Requirements
------------

* Python 3.8+
* requests >= 2.28.0

Development
-----------

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/rdhyee/hypothesisapi.git
    cd hypothesisapi

    # Install with development dependencies
    pip install -e ".[dev]"

    # Run tests
    pytest

    # Run type checking
    mypy hypothesisapi

    # Run linting
    flake8 hypothesisapi tests

License
-------

BSD License. See LICENSE file for details.
