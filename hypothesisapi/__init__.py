# -*- coding: utf-8 -*-
"""
Python wrapper for the Hypothesis web annotation API.

This library provides a Python interface to the Hypothesis API v1.0,
enabling programmatic creation, retrieval, update, and search of web annotations.

API Documentation: https://h.readthedocs.io/en/latest/api/
"""
from __future__ import annotations

__author__ = "Raymond Yee"
__email__ = "raymond.yee@gmail.com"
__version__ = "0.4.0"

import warnings
from typing import Any, Dict, Generator, List, Optional
from urllib.parse import quote, urlencode

import requests

__all__ = [
    # Main class and constants
    "API",
    "API_URL",
    "APP_URL",
    # Exceptions
    "HypothesisAPIError",
    "AuthenticationError",
    "NotFoundError",
    "ForbiddenError",
]

# Note: The following API methods are available on the API class:
# Annotations: create, get_annotation, update, delete, flag, hide, unhide, reindex, moderation
# Search: search, search_raw
# Bulk: bulk, bulk_annotations, bulk_groups, bulk_lms_annotations
# Groups: get_groups, create_group, get_group, update_group, get_group_annotations,
#         get_group_members, add_group_member, get_group_member, update_group_member,
#         remove_group_member, leave_group
# Profile: get_profile, get_profile_groups, update_profile
# Users (Admin): create_user, get_user, update_user
# Analytics: create_analytics_event
# Utility: root, get_links

APP_URL = "https://hypothes.is/app"
API_URL = "https://hypothes.is/api"
DEFAULT_TIMEOUT = 30  # seconds


def _remove_none(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove keys with None values from a dictionary."""
    return {k: v for k, v in d.items() if v is not None}


class HypothesisAPIError(Exception):
    """Base exception for Hypothesis API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[str] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class AuthenticationError(HypothesisAPIError):
    """Raised when authentication fails."""
    pass


class NotFoundError(HypothesisAPIError):
    """Raised when a resource is not found."""
    pass


class ForbiddenError(HypothesisAPIError):
    """Raised when user lacks permission for an action (403 Forbidden)."""
    pass


class API:
    """
    Main interface for Hypothesis API interactions.

    The Hypothesis API v1.0 is the current stable version. This class provides
    methods to interact with annotations, groups, and user profiles.

    Example:
        >>> api = API(username="your_username", api_key="your_api_key")
        >>> for annotation in api.search(user="username"):
        ...     print(annotation["text"])

    Attributes:
        api_url: Base URL for the Hypothesis API.
        app_url: Base URL for the Hypothesis web app.
        username: Hypothesis username.
        api_key: API key (bearer token) for authentication.
    """

    def __init__(
        self,
        username: str,
        api_key: str,
        api_url: str = API_URL,
        app_url: str = APP_URL,
    ) -> None:
        """
        Initialize the API client.

        Args:
            username: Hypothesis username.
            api_key: API key (bearer token). Get yours at https://hypothes.is/account/developer
            api_url: Base URL for the API (default: https://hypothes.is/api).
            app_url: Base URL for the web app (default: https://hypothes.is/app).
        """
        self.api_url = api_url
        self.app_url = app_url
        self.username = username
        self.api_key = api_key

    def _get_user_acct(self, user: Optional[str] = None, authority: str = "hypothes.is") -> str:
        """Format a username as a Hypothesis account identifier."""
        username = user or self.username
        return f"acct:{username}@{authority}"

    def _get_headers(self, authenticated: bool = True) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        headers = {
            "Content-Type": "application/json;charset=UTF-8",
            "Accept": "application/json",
        }
        if authenticated:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _handle_response(self, response: requests.Response) -> Any:
        """Handle API response and raise appropriate exceptions."""
        if response.status_code in (200, 201):
            return response.json()
        elif response.status_code == 204:
            return {}
        elif response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Check your API key.",
                status_code=response.status_code,
                response=response.text,
            )
        elif response.status_code == 403:
            raise ForbiddenError(
                "Permission denied for this action.",
                status_code=response.status_code,
                response=response.text,
            )
        elif response.status_code == 404:
            raise NotFoundError(
                "Resource not found.",
                status_code=response.status_code,
                response=response.text,
            )
        else:
            raise HypothesisAPIError(
                f"API request failed with status {response.status_code}",
                status_code=response.status_code,
                response=response.text,
            )

    # ========== Root Endpoint ==========

    def root(self) -> Dict[str, Any]:
        """
        Get API root with hypermedia links.

        Returns:
            Dictionary containing API links and version information.
        """
        response = requests.get(
            self.api_url,
            headers=self._get_headers(authenticated=False),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    # ========== Annotation Endpoints ==========

    def create(
        self,
        payload: Dict[str, Any],
        group: str = "__world__",
    ) -> Dict[str, Any]:
        """
        Create a new annotation.

        Args:
            payload: Annotation data. Must include 'uri'. May include:
                - text: The annotation text/body
                - tags: List of tags
                - target: Target selector information
                - document: Document metadata
                - references: Parent annotation IDs for replies
            group: Group ID for the annotation (default: "__world__" for public).

        Returns:
            The created annotation object.

        Raises:
            HypothesisAPIError: If the request fails.
            ValueError: If 'uri' is not provided in payload.
        """
        if "uri" not in payload:
            raise ValueError("Payload must include 'uri'")

        user_acct = self._get_user_acct()
        payload_out = payload.copy()
        payload_out["user"] = user_acct
        # Only set group if not already in payload
        if "group" not in payload_out:
            payload_out["group"] = group
        effective_group = payload_out["group"]

        if "permissions" not in payload:
            read_permissions = ["group:__world__"] if effective_group == "__world__" else [f"group:{effective_group}"]
            payload_out["permissions"] = {
                "read": read_permissions,
                "update": [user_acct],
                "delete": [user_acct],
                "admin": [user_acct],
            }

        if "document" not in payload:
            payload_out["document"] = {}

        response = requests.post(
            f"{self.api_url}/annotations",
            headers=self._get_headers(),
            json=payload_out,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_annotation(self, annotation_id: str, authenticated: bool = True) -> Dict[str, Any]:
        """
        Retrieve a single annotation by ID.

        Args:
            annotation_id: The annotation ID.
            authenticated: Whether to send authentication headers (default: True).
                Set to True to access private/group annotations.

        Returns:
            The annotation object.

        Raises:
            NotFoundError: If the annotation doesn't exist.
            ForbiddenError: If the annotation is private and user lacks access.
        """
        response = requests.get(
            f"{self.api_url}/annotations/{annotation_id}",
            headers=self._get_headers(authenticated=authenticated),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def update(self, annotation_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing annotation.

        Args:
            annotation_id: The annotation ID to update.
            payload: Fields to update. May include:
                - text: Updated annotation text
                - tags: Updated list of tags
                - permissions: Updated permissions

        Returns:
            The updated annotation object.

        Raises:
            NotFoundError: If the annotation doesn't exist.
            ForbiddenError: If user doesn't have update permission.
        """
        response = requests.patch(
            f"{self.api_url}/annotations/{annotation_id}",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def delete(self, annotation_id: str) -> Dict[str, Any]:
        """
        Delete an annotation.

        Args:
            annotation_id: The annotation ID to delete.

        Returns:
            Confirmation object with 'id' and 'deleted' fields.

        Raises:
            NotFoundError: If the annotation doesn't exist.
            ForbiddenError: If user doesn't have delete permission.
        """
        response = requests.delete(
            f"{self.api_url}/annotations/{annotation_id}",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def flag(self, annotation_id: str) -> Dict[str, Any]:
        """
        Flag an annotation for review by moderators.

        Args:
            annotation_id: The annotation ID to flag.

        Returns:
            Empty dict on success.

        Raises:
            NotFoundError: If the annotation doesn't exist.
        """
        response = requests.put(
            f"{self.api_url}/annotations/{annotation_id}/flag",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def hide(self, annotation_id: str) -> Dict[str, Any]:
        """
        Hide an annotation (moderator action).

        Args:
            annotation_id: The annotation ID to hide.

        Returns:
            Empty dict on success.

        Raises:
            ForbiddenError: If user is not a moderator.
        """
        response = requests.put(
            f"{self.api_url}/annotations/{annotation_id}/hide",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def unhide(self, annotation_id: str) -> Dict[str, Any]:
        """
        Unhide an annotation (moderator action).

        Args:
            annotation_id: The annotation ID to unhide.

        Returns:
            Empty dict on success.

        Raises:
            ForbiddenError: If user is not a moderator.
        """
        response = requests.delete(
            f"{self.api_url}/annotations/{annotation_id}/hide",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def reindex(self, annotation_id: str) -> Dict[str, Any]:
        """
        Reindex an annotation (admin action).

        Triggers reindexing of the annotation in the search index.

        Args:
            annotation_id: The annotation ID to reindex.

        Returns:
            Empty dict on success.

        Raises:
            ForbiddenError: If user lacks admin permissions.
            NotFoundError: If the annotation doesn't exist.
            HypothesisAPIError: May return 500 for non-admin users.

        Note:
            This is an internal/admin-only endpoint. Regular users will
            receive an error when attempting to use this method.
        """
        response = requests.post(
            f"{self.api_url}/annotations/{annotation_id}/reindex",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def moderation(
        self,
        annotation_id: str,
        moderation_status: str,
        annotation_updated: bool = True,
    ) -> Dict[str, Any]:
        """
        Update moderation status of an annotation.

        This endpoint allows moderators to change the moderation status of
        an annotation (e.g., approve, flag, or hide it).

        Args:
            annotation_id: The annotation ID to moderate.
            moderation_status: The new moderation status. Common values:
                - "APPROVED": Annotation is approved and visible
                - "HIDDEN": Annotation is hidden from public view
                - "FLAGGED": Annotation is flagged for review
            annotation_updated: Whether to mark the annotation as updated.
                Defaults to True.

        Returns:
            The updated annotation object.

        Raises:
            ForbiddenError: If user is not a moderator.
            NotFoundError: If the annotation doesn't exist.

        Note:
            This is an alternative to hide()/unhide() with more granular control.
            For simple hide/unhide operations, prefer those methods.
        """
        response = requests.patch(
            f"{self.api_url}/annotations/{annotation_id}/moderation",
            headers=self._get_headers(),
            json={
                "moderation_status": moderation_status,
                "annotation_updated": annotation_updated,
            },
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def search(
        self,
        user: Optional[str] = None,
        authority: Optional[str] = None,
        uri: Optional[str] = None,
        url: Optional[str] = None,
        wildcard_uri: Optional[str] = None,
        text: Optional[str] = None,
        any_field: Optional[str] = None,
        tag: Optional[str] = None,
        tags: Optional[List[str]] = None,
        group: Optional[str] = None,
        quote: Optional[str] = None,
        references: Optional[str] = None,
        sort: Optional[str] = None,
        order: str = "asc",
        offset: int = 0,
        limit: int = 200,
        search_after: Optional[str] = None,
        **kwargs: Any,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Search for annotations with pagination.

        This method returns a generator that automatically handles pagination,
        yielding annotations one at a time.

        Args:
            user: Filter by username. Can be just username or full acct: format.
                If just username, authority param determines the domain.
            authority: Authority domain for user filter (default: hypothes.is).
                Ignored if user is in full acct: format.
            uri: Filter by exact URI.
            url: Alias for uri.
            wildcard_uri: Filter by URI pattern with wildcards (*).
            text: Search annotation text.
            any_field: Search across multiple fields.
            tag: Filter by single tag.
            tags: Filter by multiple tags (all must match).
            group: Filter by group ID.
            quote: Search quoted text.
            references: Filter by parent annotation ID (for replies).
            sort: Sort field (created, updated, id, group, user).
            order: Sort order (asc or desc).
            offset: Starting offset for results (ignored if search_after is set).
            limit: Maximum results per page (max 200).
            search_after: Pagination cursor for efficient deep pagination.
                When set, offset-based pagination is disabled.
            **kwargs: Additional search parameters.

        Yields:
            Annotation objects matching the search criteria.

        Raises:
            HypothesisAPIError: If the search request fails.
            AuthenticationError: If authentication fails.
        """
        # Handle user parameter - support both username and full acct: format
        user_acct: Optional[str] = None
        if user:
            if user.startswith("acct:"):
                user_acct = user
            else:
                user_acct = self._get_user_acct(user, authority=authority or "hypothes.is")

        search_dict: Dict[str, Any] = {
            "user": user_acct,
            "uri": uri or url,
            "wildcard_uri": wildcard_uri,
            "text": text,
            "any": any_field,
            "group": group,
            "quote": quote,
            "references": references,
            "sort": sort,
            "order": order,
            "limit": limit,
        }

        # Handle tags - Hypothesis API expects repeated tag= parameters, not tags=
        # Build a list under "tag" key for urlencode with doseq=True
        tag_list: List[str] = []
        if tag:
            tag_list.append(tag)
        if tags:
            tag_list.extend(tags)
        if tag_list:
            search_dict["tag"] = tag_list

        # Handle pagination mode: cursor-based (search_after) vs offset-based
        use_cursor_pagination = search_after is not None
        if use_cursor_pagination:
            search_dict["search_after"] = search_after
        else:
            search_dict["offset"] = offset

        search_dict.update(kwargs)
        search_dict = _remove_none(search_dict)

        last_seen_id: Optional[str] = None

        while True:
            url_str = f"{self.api_url}/search?{urlencode(search_dict, doseq=True)}"
            response = requests.get(
                url_str,
                headers=self._get_headers(),
                timeout=DEFAULT_TIMEOUT,
            )
            # Use _handle_response to properly handle errors
            data = self._handle_response(response)
            rows = data.get("rows", [])

            if not rows:
                break

            # Guard against infinite loops - break if seeing same first result
            first_id = rows[0].get("id") if rows else None
            if first_id and first_id == last_seen_id:
                break
            last_seen_id = first_id

            for row in rows:
                yield row

            # Update pagination for next page
            if use_cursor_pagination:
                # For cursor-based pagination, use search_after from last result
                # Note: This is experimental - the API may return this differently
                last_row = rows[-1]
                search_dict["search_after"] = last_row.get("created", "") + last_row.get("id", "")
            else:
                # For offset-based pagination, increment offset
                search_dict["offset"] = search_dict.get("offset", 0) + limit

    def search_raw(
        self,
        limit: int = 20,
        offset: int = 0,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Perform a raw search and return the full response.

        Unlike search(), this method returns the complete API response
        including total count and metadata, without automatic pagination.

        Args:
            limit: Maximum results to return (max 200).
            offset: Starting offset.
            **kwargs: Search parameters (see search() for options).

        Returns:
            Full search response including 'rows' and 'total'.
        """
        search_dict = {"limit": limit, "offset": offset, **kwargs}
        search_dict = _remove_none(search_dict)

        url = f"{self.api_url}/search?{urlencode(search_dict, doseq=True)}"
        response = requests.get(
            url,
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    # ========== Bulk Endpoints ==========

    def bulk(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform multiple operations in a single API call.

        This endpoint allows batching multiple operations for efficiency.

        Args:
            operations: List of operation objects. Each operation should have:
                - action: The action type (e.g., "create", "update", "delete")
                - Additional fields depending on the action type

        Returns:
            Results of the bulk operation.

        Raises:
            HypothesisAPIError: If the bulk operation fails.
            NotFoundError: If endpoint is not available (admin/LMS only).

        Note:
            This endpoint may only be available to administrators or
            LMS (Learning Management System) integrations. Regular users
            will receive a 404 error.
        """
        response = requests.post(
            f"{self.api_url}/bulk",
            headers=self._get_headers(),
            json=operations,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def bulk_annotations(
        self,
        annotation_ids: Optional[List[str]] = None,
        group: Optional[str] = None,
        user: Optional[str] = None,
        uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a large number of annotations in one call.

        More efficient than paginated search for bulk retrieval.

        Args:
            annotation_ids: List of specific annotation IDs to retrieve.
            group: Filter by group ID.
            user: Filter by user (acct: format).
            uri: Filter by document URI.

        Returns:
            Dictionary containing the annotations.

        Raises:
            HypothesisAPIError: If the request fails.
            NotFoundError: If endpoint is not available (admin/LMS only).

        Note:
            This endpoint may only be available to administrators or
            LMS (Learning Management System) integrations. Regular users
            should use search() instead, which provides similar functionality
            with pagination.
        """
        payload: Dict[str, Any] = {}
        if annotation_ids:
            payload["ids"] = annotation_ids
        if group:
            payload["group"] = group
        if user:
            payload["user"] = user
        if uri:
            payload["uri"] = uri

        response = requests.post(
            f"{self.api_url}/bulk/annotation",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def bulk_groups(
        self,
        group_ids: Optional[List[str]] = None,
        authority: Optional[str] = None,
        expand: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve a large number of groups in one call.

        Args:
            group_ids: List of specific group IDs to retrieve.
            authority: Filter by authority domain.
            expand: Fields to expand (e.g., ["organization", "scopes"]).

        Returns:
            Dictionary containing the groups.

        Raises:
            HypothesisAPIError: If the request fails.
            NotFoundError: If endpoint is not available (admin/LMS only).

        Note:
            This endpoint may only be available to administrators or
            LMS (Learning Management System) integrations. Regular users
            should use get_groups() instead.
        """
        payload: Dict[str, Any] = {}
        if group_ids:
            payload["ids"] = group_ids
        if authority:
            payload["authority"] = authority
        if expand:
            payload["expand"] = expand

        response = requests.post(
            f"{self.api_url}/bulk/group",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def bulk_lms_annotations(
        self,
        group_ids: List[str],
        assignment_id: Optional[str] = None,
        course_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Retrieve annotations for LMS (Learning Management System) metrics.

        This endpoint is designed for educational integrations.

        Args:
            group_ids: List of group IDs to retrieve annotations from.
            assignment_id: Optional LMS assignment identifier.
            course_id: Optional LMS course identifier.

        Returns:
            Dictionary containing LMS-related annotation data.

        Raises:
            HypothesisAPIError: If the request fails.
            NotFoundError: If endpoint is not available.

        Note:
            This endpoint is only available for LMS integrations with
            proper authentication. Regular Hypothesis users will receive
            a 404 error.
        """
        payload: Dict[str, Any] = {"group_ids": group_ids}
        if assignment_id:
            payload["assignment_id"] = assignment_id
        if course_id:
            payload["course_id"] = course_id

        response = requests.post(
            f"{self.api_url}/bulk/lms/annotations",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    # ========== Group Endpoints ==========

    def get_groups(
        self,
        authority: Optional[str] = None,
        document_uri: Optional[str] = None,
        expand: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get a list of groups.

        Args:
            authority: Filter by authority (default: hypothes.is).
            document_uri: Filter groups associated with a document.
            expand: Fields to expand (e.g., ["organization", "scopes"]).

        Returns:
            List of group objects.
        """
        params: Dict[str, Any] = {}
        if authority:
            params["authority"] = authority
        if document_uri:
            params["document_uri"] = document_uri
        if expand:
            params["expand"] = expand

        url = f"{self.api_url}/groups"
        if params:
            url += f"?{urlencode(params, doseq=True)}"

        response = requests.get(url, headers=self._get_headers(), timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def create_group(
        self,
        name: str,
        description: Optional[str] = None,
        groupid: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new private group.

        Args:
            name: Display name for the group.
            description: Optional group description.
            groupid: Optional custom group ID (for third-party authorities).

        Returns:
            The created group object.
        """
        payload: Dict[str, Any] = {"name": name}
        if description:
            payload["description"] = description
        if groupid:
            payload["groupid"] = groupid

        response = requests.post(
            f"{self.api_url}/groups",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_group(
        self,
        group_id: str,
        expand: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Get a specific group by ID.

        Args:
            group_id: The group ID (pubid).
            expand: Fields to expand (e.g., ["organization", "scopes"]).

        Returns:
            The group object.
        """
        params: Dict[str, Any] = {}
        if expand:
            params["expand"] = expand

        url = f"{self.api_url}/groups/{group_id}"
        if params:
            url += f"?{urlencode(params, doseq=True)}"

        response = requests.get(url, headers=self._get_headers(), timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def update_group(
        self,
        group_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a group's properties.

        Args:
            group_id: The group ID to update.
            name: New display name.
            description: New description.

        Returns:
            The updated group object.

        Raises:
            ValueError: If neither name nor description is provided.
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description

        if not payload:
            raise ValueError("At least one of 'name' or 'description' must be provided")

        response = requests.patch(
            f"{self.api_url}/groups/{group_id}",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_group_members(self, group_id: str) -> List[Dict[str, Any]]:
        """
        Get members of a group.

        Args:
            group_id: The group ID.

        Returns:
            List of member objects.
        """
        response = requests.get(
            f"{self.api_url}/groups/{group_id}/members",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def leave_group(self, group_id: str) -> Dict[str, Any]:
        """
        Leave a group (remove current user from membership).

        Args:
            group_id: The group ID to leave.

        Returns:
            Empty dict on success.
        """
        response = requests.delete(
            f"{self.api_url}/groups/{group_id}/members/me",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_group_annotations(
        self,
        group_id: str,
        limit: int = 200,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get all annotations in a group.

        This is a direct endpoint for retrieving group annotations,
        alternative to using search() with a group filter.

        Args:
            group_id: The group ID (pubid).
            limit: Maximum results to return (max 200).
            offset: Starting offset for pagination.

        Returns:
            Dictionary with structure:
            {
                "meta": {"page": {"total": <int>}},
                "data": [<annotation>, ...]
            }
            Access annotations via result["data"] and total count via
            result["meta"]["page"]["total"].

        Note:
            This differs from search() which returns {"rows": [...], "total": N}.
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        encoded_group_id = quote(group_id, safe="")
        url = f"{self.api_url}/groups/{encoded_group_id}/annotations?{urlencode(params)}"

        response = requests.get(url, headers=self._get_headers(), timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def add_group_member(
        self,
        group_id: str,
        userid: str,
        roles: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Add a user to a group.

        Args:
            group_id: The group ID (pubid).
            userid: The user ID to add (e.g., "acct:username@authority").
            roles: Optional list of roles to assign (e.g., ["member", "moderator"]).

        Returns:
            The membership object.

        Raises:
            ForbiddenError: If user lacks permission to add members.
            NotFoundError: If the group or user doesn't exist.
        """
        payload: Dict[str, Any] = {}
        if roles:
            payload["roles"] = roles

        encoded_group_id = quote(group_id, safe="")
        encoded_userid = quote(userid, safe="")
        response = requests.post(
            f"{self.api_url}/groups/{encoded_group_id}/members/{encoded_userid}",
            headers=self._get_headers(),
            json=payload,  # Always send JSON body (empty dict if no roles)
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_group_member(self, group_id: str, userid: str) -> Dict[str, Any]:
        """
        Get a specific member's information in a group.

        Args:
            group_id: The group ID (pubid).
            userid: The user ID (e.g., "acct:username@authority").

        Returns:
            The membership object with user info and roles.

        Raises:
            NotFoundError: If the membership doesn't exist.
        """
        encoded_group_id = quote(group_id, safe="")
        encoded_userid = quote(userid, safe="")
        response = requests.get(
            f"{self.api_url}/groups/{encoded_group_id}/members/{encoded_userid}",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def update_group_member(
        self,
        group_id: str,
        userid: str,
        roles: List[str],
    ) -> Dict[str, Any]:
        """
        Update a member's role in a group.

        Args:
            group_id: The group ID (pubid).
            userid: The user ID (e.g., "acct:username@authority").
            roles: List of roles to assign (e.g., ["member"], ["moderator"]).

        Returns:
            The updated membership object.

        Raises:
            ForbiddenError: If user lacks permission to update roles.
            NotFoundError: If the membership doesn't exist.
        """
        encoded_group_id = quote(group_id, safe="")
        encoded_userid = quote(userid, safe="")
        response = requests.patch(
            f"{self.api_url}/groups/{encoded_group_id}/members/{encoded_userid}",
            headers=self._get_headers(),
            json={"roles": roles},
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def remove_group_member(self, group_id: str, userid: str) -> Dict[str, Any]:
        """
        Remove a user from a group.

        Args:
            group_id: The group ID (pubid).
            userid: The user ID to remove (e.g., "acct:username@authority").

        Returns:
            Empty dict on success.

        Raises:
            ForbiddenError: If user lacks permission to remove members.
            NotFoundError: If the membership doesn't exist.
        """
        encoded_group_id = quote(group_id, safe="")
        encoded_userid = quote(userid, safe="")
        response = requests.delete(
            f"{self.api_url}/groups/{encoded_group_id}/members/{encoded_userid}",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    # ========== Profile Endpoints ==========

    def get_profile(self) -> Dict[str, Any]:
        """
        Get the current user's profile.

        Returns:
            Profile object with user information.
        """
        response = requests.get(
            f"{self.api_url}/profile",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_profile_groups(
        self,
        authority: Optional[str] = None,
        document_uri: Optional[str] = None,
        expand: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get groups for the current user's profile.

        Args:
            authority: Filter by authority.
            document_uri: Filter groups associated with a document.
            expand: Fields to expand.

        Returns:
            List of group objects.
        """
        params: Dict[str, Any] = {}
        if authority:
            params["authority"] = authority
        if document_uri:
            params["document_uri"] = document_uri
        if expand:
            params["expand"] = expand

        url = f"{self.api_url}/profile/groups"
        if params:
            url += f"?{urlencode(params, doseq=True)}"

        response = requests.get(url, headers=self._get_headers(), timeout=DEFAULT_TIMEOUT)
        return self._handle_response(response)

    def update_profile(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update the current user's profile preferences.

        Args:
            preferences: Dictionary of preference settings to update.
                Common preferences include notification settings.

        Returns:
            The updated profile object.

        Raises:
            HypothesisAPIError: If the update fails.
        """
        response = requests.patch(
            f"{self.api_url}/profile",
            headers=self._get_headers(),
            json={"preferences": preferences},
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    # ========== User Endpoints (Admin) ==========

    def create_user(
        self,
        authority: str,
        username: str,
        email: str,
        display_name: Optional[str] = None,
        identities: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new user (requires admin authority).

        This endpoint is typically used by third-party authorities
        to create users in their namespace.

        Args:
            authority: The authority domain.
            username: Username for the new user.
            email: Email address.
            display_name: Optional display name.
            identities: Optional list of identity providers.

        Returns:
            The created user object.
        """
        payload: Dict[str, Any] = {
            "authority": authority,
            "username": username,
            "email": email,
        }
        if display_name:
            payload["display_name"] = display_name
        if identities:
            payload["identities"] = identities

        response = requests.post(
            f"{self.api_url}/users",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def get_user(self, userid: str) -> Dict[str, Any]:
        """
        Get a user by ID (requires admin authority).

        Args:
            userid: The user ID (e.g., "acct:username@authority").

        Returns:
            The user object.
        """
        response = requests.get(
            f"{self.api_url}/users/{userid}",
            headers=self._get_headers(),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    def update_user(
        self,
        userid: str,
        email: Optional[str] = None,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a user (requires admin authority).

        Args:
            userid: The user ID to update.
            email: New email address.
            display_name: New display name.

        Returns:
            The updated user object.
        """
        payload: Dict[str, Any] = {}
        if email is not None:
            payload["email"] = email
        if display_name is not None:
            payload["display_name"] = display_name

        response = requests.patch(
            f"{self.api_url}/users/{userid}",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    # ========== Analytics Endpoints ==========

    def create_analytics_event(
        self,
        event: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an analytics event.

        Track usage events for analytics purposes.

        Args:
            event: The event name to track. Note: The Hypothesis API only
                accepts specific event names (e.g., "client.realtime.apply_updates").
                Check API documentation for the full list of accepted events.
            properties: Optional dictionary of event properties.

        Returns:
            Empty dict on success.

        Raises:
            HypothesisAPIError: If the event creation fails or the event
                name is not in the allowed list.

        Note:
            This endpoint has restricted event types. It is primarily used
            by the Hypothesis client for internal analytics, not for
            general-purpose event tracking.
        """
        payload: Dict[str, Any] = {"event": event}
        if properties:
            payload["properties"] = properties

        response = requests.post(
            f"{self.api_url}/analytics/events",
            headers=self._get_headers(),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    # ========== Links Endpoints ==========

    def get_links(self) -> Dict[str, Any]:
        """
        Get URL templates for generating URLs to HTML pages.

        Returns URL templates that can be used to construct links
        to various pages in the Hypothesis web application.

        Returns:
            Dictionary of URL templates with placeholders.
        """
        response = requests.get(
            f"{self.api_url}/links",
            headers=self._get_headers(authenticated=False),
            timeout=DEFAULT_TIMEOUT,
        )
        return self._handle_response(response)

    # ========== Deprecated Methods (for backward compatibility) ==========

    def search_id(self, _id: str) -> Optional[Dict[str, Any]]:
        """
        Search for an annotation by ID.

        .. deprecated::
            Use get_annotation() instead.
        """
        warnings.warn(
            "search_id() is deprecated, use get_annotation() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        try:
            return self.get_annotation(_id)
        except NotFoundError:
            return None
