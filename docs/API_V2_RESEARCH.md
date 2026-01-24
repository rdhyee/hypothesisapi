# Hypothesis API v2.0 Research

**Date:** January 2026
**Status:** Research complete
**Related Issue:** [#8 - Explore Hypothesis API v2.0 support](https://github.com/rdhyee/hypothesisapi/issues/8)

## Summary

Hypothesis API v2.0 remains **experimental and under active development**, with the official documentation explicitly warning that "breaking changes may occur at any time." The v2.0 API is largely identical to v1.0 in terms of endpoints and functionality—there is **no URL path versioning** (both use `/api/` prefix), and most operations work the same way. The primary differences are: (1) a new moderation endpoint, (2) evolving pagination format for group members, and (3) response headers indicating API version. Given the experimental status and minimal new functionality, **waiting for v2.0 stabilization is recommended** before adding explicit support.

## Endpoint Comparison Table

### v1.0 vs v2.0 Endpoints

| Endpoint | v1.0 | v2.0 | Breaking? | Notes |
|----------|------|------|-----------|-------|
| **Root** |
| `GET /` | ✅ | ✅ | No | Identical |
| **Annotations** |
| `POST /annotations` | ✅ | ✅ | No | Identical |
| `GET /search` | ✅ | ✅ | No | Same params; `wildcard_uri` marked "experimental" in v2 |
| `GET /annotations/{id}` | ✅ | ✅ | No | Identical |
| `PATCH /annotations/{id}` | ✅ | ✅ | No | Identical |
| `PUT /annotations/{id}` | ✅ | ✅ (legacy) | No | Deprecated in v2, use PATCH |
| `DELETE /annotations/{id}` | ✅ | ✅ | No | Identical |
| `PUT /annotations/{id}/flag` | ✅ | ✅ | No | Identical |
| `PUT /annotations/{id}/hide` | ✅ | ✅ | No | Identical |
| `DELETE /annotations/{id}/hide` | ✅ | ✅ | No | Identical |
| `PATCH /annotations/{id}/moderation` | ✅ | ✅ | No | Available in both; more prominent in v2 |
| **Groups** |
| `GET /groups` | ✅ | ✅ | No | Identical |
| `POST /groups` | ✅ | ✅ | No | Identical |
| `GET /groups/{id}` | ✅ | ✅ | No | Identical |
| `PATCH /groups/{id}` | ✅ | ✅ | No | Identical |
| `GET /groups/{id}/members` | ✅ | ✅ | **Potentially** | v2 moving to paginated format; legacy will be removed |
| `GET /groups/{id}/members/{user}` | ✅ | ✅ | No | Identical |
| `POST /groups/{id}/members/{user}` | ✅ | ✅ | No | Identical |
| `PATCH /groups/{id}/members/{user}` | ✅ | ✅ | No | Identical |
| `DELETE /groups/{id}/members/{user}` | ✅ | ✅ | No | Identical |
| `GET /groups/{id}/annotations` | ✅ | ✅ | No | Uses `page[after]`, `page[size]` pagination |
| **Profile** |
| `GET /profile` | ✅ | ✅ | No | Identical |
| `GET /profile/groups` | ✅ | ✅ | No | Identical |
| **Users (Admin)** |
| `POST /users` | ✅ | ✅ | No | Identical |
| `GET /users/{user}` | ✅ | ✅ | No | Identical |
| `PATCH /users/{username}` | ✅ | ✅ | No | Identical |

### New in v2.0 (or more prominently documented)

| Endpoint | Description | Notes |
|----------|-------------|-------|
| `PATCH /annotations/{id}/moderation` | Change moderation status | Params: `moderation_status` (APPROVED/PENDING/DENIED/SPAM), `current_moderation_status`, `annotation_updated` |

## Key Differences

### 1. Authentication

**No changes.** Both versions use the same Bearer token authentication:

```
Authorization: Bearer <api_key>
```

API keys are obtained from https://hypothes.is/account/developer

Some endpoints also support AuthClient authentication (for third-party authorities), which is unchanged.

### 2. Pagination

**Largely unchanged, with one notable evolution:**

| Mechanism | v1.0 | v2.0 | Status |
|-----------|------|------|--------|
| `offset` + `limit` | ✅ | ✅ | Works, but limited to offset < 9800 |
| `search_after` | ✅ | ✅ | Recommended for deep pagination |
| `page[number]` + `page[size]` | ✅ (some endpoints) | ✅ | Used for group members |
| `page[after]` + `page[size]` | ✅ (some endpoints) | ✅ | Cursor-based, used for group annotations |

**Important:** The Elasticsearch limitation (`offset + limit <= 10000`) was resolved in 2018 by introducing `search_after` cursor-based pagination. Our current implementation already supports this via the `search_after` parameter.

**Breaking change incoming:** The `GET /groups/{id}/members` endpoint currently returns an unpaginated array. v2.0 documentation notes: "In the future this legacy un-paginated response format will be removed" in favor of the paginated `{meta, data}` format.

### 3. Response Format

**Mostly unchanged.** Key differences:

| Aspect | v1.0 | v2.0 |
|--------|------|------|
| Response body | JSON | JSON (identical) |
| Headers | Standard | Adds `Hypothesis-Media-Type` header |
| Annotation schema | Same fields | Same fields; `moderation_status` more prominent |

The annotation object schema is identical between versions, including:
- `id`, `created`, `updated`, `user`, `uri`, `text`, `tags`
- `group`, `permissions`, `target`, `document`, `links`
- `hidden`, `flagged`, `references`, `user_info`
- `moderation_status` (PENDING/APPROVED/DENIED/SPAM)

### 4. URL Structure

**No path-based versioning.** Both v1.0 and v2.0 use the same base URL:
- `https://hypothes.is/api`

Version selection appears to be implicit based on headers or is server-side determined. The documentation maintains separate specs but doesn't indicate how to explicitly request v1 vs v2.

## New Capabilities in v2.0

v2.0 adds minimal new functionality beyond v1.0:

1. **Moderation workflow endpoint** (`PATCH /annotations/{id}/moderation`)
   - Set `moderation_status` to APPROVED, PENDING, DENIED, or SPAM
   - Optimistic locking via `current_moderation_status` and `annotation_updated` params
   - Already available in v1.0 but better documented in v2.0

2. **Paginated group members response** (upcoming)
   - Returns `{meta: {...}, data: [...]}` format instead of bare array
   - Better for large groups

3. **Experimental features marked explicitly**
   - `wildcard_uri` search parameter marked experimental in v2.0 spec

## Current Status Assessment

### Is v2.0 still experimental?

**Yes.** The official documentation at [h.readthedocs.io](https://h.readthedocs.io/en/latest/api/) explicitly states:

> "Version 2.0 of the Hypothesis API is experimental and under development. Breaking changes may occur at any time."

### Any timeline for stable release?

**No timeline published.** The Hypothesis team has not announced when v2.0 will be considered stable. The [product backlog](https://github.com/hypothesis/product-backlog) and [developer resources](https://web.hypothes.is/developers/) do not mention a v2.0 stabilization date.

### What are other clients doing?

| Client | Status | v2.0 Support |
|--------|--------|--------------|
| [python-hypothesis](https://pypi.org/project/python-hypothesis/) | Dormant (last release 2020) | No |
| [hypothesis-api](https://pypi.org/project/hypothesis-api/) | Inactive (limited maintenance) | No |
| [h-api](https://github.com/hypothesis/h-api) | Internal to Hypothesis | Not documented |

No third-party client libraries have added explicit v2.0 support. This reinforces the recommendation to wait.

## Impact on This Library

### Methods that would need changes for v2.0

Based on our current `hypothesisapi/__init__.py` implementation:

| Method | Change Required | Reason |
|--------|-----------------|--------|
| `get_group_members()` | **Eventually** | Must handle both array (legacy) and `{meta, data}` (v2) formats |
| All methods | Minor | Could add `Hypothesis-Media-Type` header handling |
| New method | Optional | Could add `moderate_annotation()` wrapper |

### Methods that are already compatible

All other methods in our implementation are compatible with both v1.0 and v2.0:
- `create()`, `get_annotation()`, `update()`, `delete()`
- `flag()`, `hide()`, `unhide()`
- `search()`, `search_raw()`
- `get_groups()`, `create_group()`, `get_group()`, `update_group()`
- `leave_group()`
- `get_profile()`, `get_profile_groups()`
- `create_user()`, `get_user()`, `update_user()`

## Recommendation

### **Wait for v2.0 stabilization before adding explicit support.**

**Rationale:**

1. **v2.0 is still experimental** with explicit warning about breaking changes
2. **Minimal new functionality** — almost all v2.0 features exist in v1.0
3. **No path versioning** — can't easily support both simultaneously via URL
4. **No urgency** — our v1.0 implementation covers all current use cases
5. **Other clients aren't supporting v2.0** — we wouldn't be behind the ecosystem

### When to revisit

- When Hypothesis announces v2.0 as stable
- If v2.0 adds significant new functionality we need
- If v1.0 is deprecated with a sunset date

### Immediate actions (optional)

These low-risk improvements could be made now without committing to v2.0:

1. **Add `moderate_annotation()` method** — already available in v1.0 API
2. **Future-proof `get_group_members()`** — detect and handle both response formats
3. **Monitor Hypothesis releases** — watch [hypothesis/h releases](https://github.com/hypothesis/h/releases)

## Implementation Approach (If/When Proceeding)

If v2.0 stabilizes and we decide to add support, here are the options:

### Option A: Version parameter (Recommended)

```python
class API:
    def __init__(self, username, api_key, api_version="v1", ...):
        self.api_version = api_version

    def get_group_members(self, group_id):
        response = self._get(f"/groups/{group_id}/members")
        if self.api_version == "v2":
            return response.get("data", response)  # Handle paginated format
        return response
```

**Pros:** Single class, easy migration, backward compatible
**Cons:** Conditional logic throughout

### Option B: Separate class

```python
class API:  # v1.0 (existing)
    ...

class APIv2(API):  # v2.0 (inherits, overrides)
    def get_group_members(self, group_id):
        # v2-specific implementation
```

**Pros:** Clean separation, no conditionals
**Cons:** Code duplication, two classes to maintain

### Option C: Adapter pattern

```python
class API:
    def __init__(self, username, api_key, adapter=None):
        self.adapter = adapter or V1Adapter()

class V1Adapter:
    def parse_members(self, response): return response

class V2Adapter:
    def parse_members(self, response): return response.get("data", response)
```

**Pros:** Most flexible, testable
**Cons:** Over-engineered for minimal differences

**Recommended:** Option A (version parameter) due to minimal differences between versions.

## References

- [Hypothesis API v1.0 OpenAPI Spec](https://github.com/hypothesis/h/blob/main/docs/_extra/api-reference/hypothesis-v1.yaml)
- [Hypothesis API v2.0 OpenAPI Spec](https://github.com/hypothesis/h/blob/main/docs/_extra/api-reference/hypothesis-v2.yaml)
- [Hypothesis API Documentation](https://h.readthedocs.io/en/latest/api/)
- [Issue #5191: offset+limit > 10000](https://github.com/hypothesis/h/issues/5191) — resolved with `search_after`
- [Issue #5555: search_after clarification](https://github.com/hypothesis/h/issues/5555) — resolved with documentation
- [Hypothesis Developer Resources](https://web.hypothes.is/developers/)
- [h-api (internal Bulk API tools)](https://github.com/hypothesis/h-api)
