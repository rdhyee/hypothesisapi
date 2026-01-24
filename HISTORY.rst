.. :changelog:

History
-------

0.4.0 (2026-01-24)
------------------

* Major update to cover the full Hypothesis API v1.0
* Added type hints throughout
* Modern Python packaging with pyproject.toml
* Fixed security vulnerability in wheel dependency (CVE-2022-40898, CVE-2026-24049)
* Requires Python 3.8+

New features:

* Annotation update and delete methods
* Flag annotations for review
* Hide/unhide annotations (moderator)
* Group management (create, update, list, members, leave)
* User profile access
* User management (admin)
* Custom exception classes for better error handling
* New search_raw() method for single-page search results

Breaking changes:

* Dropped Python 2.7 and Python 3.4-3.7 support
* create() now raises ValueError instead of returning None for missing URI

0.3.1 (2019-xx-xx)
------------------

* Minor updates

0.2.0 (2016-xx-xx)
------------------

* API token authentication support
* Search with pagination

0.1.0 (2015-04-23)
------------------

* First release on PyPI.
