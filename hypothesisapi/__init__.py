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
from urllib.parse import urlencode

import requests

__all__ = [
    "API",
    "API_URL",
    "APP_URL",
    "HypothesisAPIError",
    "AuthenticationError",
    "NotFoundError",
    "ForbiddenError",
]

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

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
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

        more_results = True

        while more_results:
            url_str = f"{self.api_url}/search?{urlencode(search_dict, doseq=True)}"
            response = requests.get(
                url_str,
                headers=self._get_headers(),
                timeout=DEFAULT_TIMEOUT,
            )
            # Use _handle_response to properly handle errors
            data = self._handle_response(response)
            rows = data.get("rows", [])

            if rows:
                for row in rows:
                    yield row

                # Update pagination for next page
                if use_cursor_pagination:
                    # For cursor-based pagination, use search_after from last result
                    last_row = rows[-1]
                    # search_after typically uses the annotation's created timestamp + id
                    search_dict["search_after"] = last_row.get("created", "") + last_row.get("id", "")
                else:
                    # For offset-based pagination, increment offset
                    search_dict["offset"] = search_dict.get("offset", 0) + limit
            else:
                more_results = False

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
        """
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description

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
