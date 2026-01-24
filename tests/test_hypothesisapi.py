#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_hypothesisapi
----------------------------------

Tests for `hypothesisapi` module.
"""

import unittest
from unittest.mock import Mock, patch, call

from hypothesisapi import (
    API,
    API_URL,
    APP_URL,
    HypothesisAPIError,
    AuthenticationError,
    NotFoundError,
    ForbiddenError,
)


class TestAPIInit(unittest.TestCase):
    """Tests for API initialization."""

    def test_init_with_defaults(self):
        api = API(username="testuser", api_key="testkey")
        self.assertEqual(api.username, "testuser")
        self.assertEqual(api.api_key, "testkey")
        self.assertEqual(api.api_url, API_URL)
        self.assertEqual(api.app_url, APP_URL)

    def test_init_with_custom_urls(self):
        api = API(
            username="testuser",
            api_key="testkey",
            api_url="https://custom.api.com/api",
            app_url="https://custom.api.com/app",
        )
        self.assertEqual(api.api_url, "https://custom.api.com/api")
        self.assertEqual(api.app_url, "https://custom.api.com/app")


class TestAPIHelpers(unittest.TestCase):
    """Tests for API helper methods."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    def test_get_user_acct_default(self):
        result = self.api._get_user_acct()
        self.assertEqual(result, "acct:testuser@hypothes.is")

    def test_get_user_acct_custom_user(self):
        result = self.api._get_user_acct(user="otheruser")
        self.assertEqual(result, "acct:otheruser@hypothes.is")

    def test_get_user_acct_custom_authority(self):
        result = self.api._get_user_acct(authority="custom.org")
        self.assertEqual(result, "acct:testuser@custom.org")

    def test_get_headers_authenticated(self):
        headers = self.api._get_headers(authenticated=True)
        self.assertEqual(headers["Authorization"], "Bearer testkey")
        self.assertEqual(headers["Accept"], "application/json")
        self.assertIn("Content-Type", headers)

    def test_get_headers_unauthenticated(self):
        headers = self.api._get_headers(authenticated=False)
        self.assertNotIn("Authorization", headers)
        self.assertEqual(headers["Accept"], "application/json")


class TestAPIResponseHandling(unittest.TestCase):
    """Tests for API response handling."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    def test_handle_response_success_200(self):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123"}
        result = self.api._handle_response(mock_response)
        self.assertEqual(result, {"id": "123"})

    def test_handle_response_success_201(self):
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": "123"}
        result = self.api._handle_response(mock_response)
        self.assertEqual(result, {"id": "123"})

    def test_handle_response_204_no_content(self):
        """Test that 204 responses return empty dict."""
        mock_response = Mock()
        mock_response.status_code = 204
        result = self.api._handle_response(mock_response)
        self.assertEqual(result, {})

    def test_handle_response_auth_error(self):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        with self.assertRaises(AuthenticationError):
            self.api._handle_response(mock_response)

    def test_handle_response_forbidden_error(self):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        with self.assertRaises(ForbiddenError):
            self.api._handle_response(mock_response)

    def test_handle_response_not_found(self):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        with self.assertRaises(NotFoundError):
            self.api._handle_response(mock_response)

    def test_handle_response_other_error(self):
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = "Server error"
        with self.assertRaises(HypothesisAPIError):
            self.api._handle_response(mock_response)


class TestAPICreate(unittest.TestCase):
    """Tests for annotation creation."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    def test_create_requires_uri(self):
        with self.assertRaises(ValueError) as ctx:
            self.api.create({"text": "Test annotation"})
        self.assertIn("uri", str(ctx.exception))

    @patch("hypothesisapi.requests.post")
    def test_create_success(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123"}
        mock_post.return_value = mock_response

        result = self.api.create({"uri": "https://example.com", "text": "Test"})
        self.assertEqual(result["id"], "abc123")
        mock_post.assert_called_once()

    @patch("hypothesisapi.requests.post")
    def test_create_with_group(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123", "group": "mygroup"}
        mock_post.return_value = mock_response

        result = self.api.create({"uri": "https://example.com"}, group="mygroup")
        self.assertEqual(result["group"], "mygroup")
        # Verify the group was passed in the payload
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        self.assertEqual(payload["group"], "mygroup")

    @patch("hypothesisapi.requests.post")
    def test_create_does_not_override_payload_group(self, mock_post):
        """Test that create() doesn't override group if already in payload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123", "group": "payload_group"}
        mock_post.return_value = mock_response

        # Pass group in payload AND as argument - payload should win
        result = self.api.create(
            {"uri": "https://example.com", "group": "payload_group"},
            group="arg_group"
        )
        call_args = mock_post.call_args
        payload = call_args.kwargs["json"]
        # The group from payload should be preserved, not overwritten by arg
        self.assertEqual(payload["group"], "payload_group")


class TestAPISearch(unittest.TestCase):
    """Tests for search functionality including pagination."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    @patch("hypothesisapi.requests.get")
    def test_search_single_page(self, mock_get):
        """Test search with results fitting in one page."""
        # First call returns results, second call returns empty (pagination check)
        mock_response_page1 = Mock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "rows": [{"id": "1"}, {"id": "2"}],
            "total": 2,
        }

        mock_response_page2 = Mock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {"rows": [], "total": 2}

        mock_get.side_effect = [mock_response_page1, mock_response_page2]

        results = list(self.api.search(user="testuser"))
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["id"], "1")
        self.assertEqual(results[1]["id"], "2")

    @patch("hypothesisapi.requests.get")
    def test_search_pagination(self, mock_get):
        """Test search handles pagination correctly."""
        # First page returns results, second page is empty
        mock_response_page1 = Mock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {
            "rows": [{"id": "1"}, {"id": "2"}],
            "total": 2,
        }

        mock_response_page2 = Mock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {"rows": [], "total": 2}

        mock_get.side_effect = [mock_response_page1, mock_response_page2]

        results = list(self.api.search(user="testuser", limit=2))
        self.assertEqual(len(results), 2)
        # Should have made 2 calls (first page + check for more)
        self.assertEqual(mock_get.call_count, 2)

    @patch("hypothesisapi.requests.get")
    def test_search_with_uri(self, mock_get):
        """Test search with URI filter."""
        mock_response_page1 = Mock()
        mock_response_page1.status_code = 200
        mock_response_page1.json.return_value = {"rows": [{"id": "1"}], "total": 1}

        mock_response_page2 = Mock()
        mock_response_page2.status_code = 200
        mock_response_page2.json.return_value = {"rows": [], "total": 1}

        mock_get.side_effect = [mock_response_page1, mock_response_page2]

        list(self.api.search(uri="https://example.com"))
        # Check the first call's URL contains the uri parameter
        call_url = mock_get.call_args_list[0][0][0]
        self.assertIn("uri=https", call_url)

    @patch("hypothesisapi.requests.get")
    def test_search_empty_results(self, mock_get):
        """Test search with no results."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rows": [], "total": 0}
        mock_get.return_value = mock_response

        results = list(self.api.search(user="nonexistent"))
        self.assertEqual(len(results), 0)

    @patch("hypothesisapi.requests.get")
    def test_search_error_handling(self, mock_get):
        """Test that search raises errors for non-200 responses."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_get.return_value = mock_response

        with self.assertRaises(AuthenticationError):
            # Need to consume the generator to trigger the request
            list(self.api.search(user="testuser"))

    @patch("hypothesisapi.requests.get")
    def test_search_with_multiple_tags(self, mock_get):
        """Test that multiple tags are serialized as repeated tag= parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rows": [], "total": 0}
        mock_get.return_value = mock_response

        list(self.api.search(tags=["tag1", "tag2"]))
        # Check the URL contains repeated tag= parameters (not tags=)
        call_url = mock_get.call_args_list[0][0][0]
        self.assertIn("tag=tag1", call_url)
        self.assertIn("tag=tag2", call_url)
        self.assertNotIn("tags=", call_url)

    @patch("hypothesisapi.requests.get")
    def test_search_with_single_tag_and_tags(self, mock_get):
        """Test combining tag and tags parameters."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rows": [], "total": 0}
        mock_get.return_value = mock_response

        list(self.api.search(tag="single", tags=["multi1", "multi2"]))
        call_url = mock_get.call_args_list[0][0][0]
        # All tags should be included as repeated tag= parameters
        self.assertIn("tag=single", call_url)
        self.assertIn("tag=multi1", call_url)
        self.assertIn("tag=multi2", call_url)

    @patch("hypothesisapi.requests.get")
    def test_search_with_authority(self, mock_get):
        """Test search with custom authority."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rows": [], "total": 0}
        mock_get.return_value = mock_response

        list(self.api.search(user="testuser", authority="custom.org"))
        call_url = mock_get.call_args_list[0][0][0]
        self.assertIn("acct%3Atestuser%40custom.org", call_url)

    @patch("hypothesisapi.requests.get")
    def test_search_with_full_acct_user(self, mock_get):
        """Test search accepts full acct: format for user."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"rows": [], "total": 0}
        mock_get.return_value = mock_response

        list(self.api.search(user="acct:someone@other.org"))
        call_url = mock_get.call_args_list[0][0][0]
        # Should use the full acct string as-is
        self.assertIn("acct%3Asomeone%40other.org", call_url)

    @patch("hypothesisapi.requests.get")
    def test_search_infinite_loop_guard(self, mock_get):
        """Test search breaks if same results are returned (infinite loop guard)."""
        # Return the same results twice - should break on second iteration
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rows": [{"id": "same_id"}],
            "total": 1,
        }
        mock_get.return_value = mock_response

        results = list(self.api.search(user="testuser"))
        # Should only get results from first call due to infinite loop guard
        self.assertEqual(len(results), 1)
        # Should have made 2 calls max (first + check that triggers guard)
        self.assertLessEqual(mock_get.call_count, 2)


class TestAPIAnnotationOperations(unittest.TestCase):
    """Tests for annotation CRUD operations."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    @patch("hypothesisapi.requests.get")
    def test_get_annotation(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123", "text": "Test"}
        mock_get.return_value = mock_response

        result = self.api.get_annotation("abc123")
        self.assertEqual(result["id"], "abc123")

    @patch("hypothesisapi.requests.get")
    def test_get_annotation_authenticated_by_default(self, mock_get):
        """Test that get_annotation sends auth headers by default."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123"}
        mock_get.return_value = mock_response

        self.api.get_annotation("abc123")
        # Check that Authorization header was included
        call_kwargs = mock_get.call_args.kwargs
        self.assertIn("Authorization", call_kwargs["headers"])
        self.assertEqual(call_kwargs["headers"]["Authorization"], "Bearer testkey")

    @patch("hypothesisapi.requests.get")
    def test_get_annotation_unauthenticated(self, mock_get):
        """Test get_annotation with authenticated=False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123"}
        mock_get.return_value = mock_response

        self.api.get_annotation("abc123", authenticated=False)
        # Check that Authorization header was NOT included
        call_kwargs = mock_get.call_args.kwargs
        self.assertNotIn("Authorization", call_kwargs["headers"])

    @patch("hypothesisapi.requests.patch")
    def test_update_annotation(self, mock_patch):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123", "text": "Updated"}
        mock_patch.return_value = mock_response

        result = self.api.update("abc123", {"text": "Updated"})
        self.assertEqual(result["text"], "Updated")

    @patch("hypothesisapi.requests.delete")
    def test_delete_annotation(self, mock_delete):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123", "deleted": True}
        mock_delete.return_value = mock_response

        result = self.api.delete("abc123")
        self.assertTrue(result["deleted"])

    @patch("hypothesisapi.requests.put")
    def test_flag_annotation(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        result = self.api.flag("abc123")
        self.assertEqual(result, {})

    @patch("hypothesisapi.requests.put")
    def test_hide_annotation(self, mock_put):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_put.return_value = mock_response

        result = self.api.hide("abc123")
        self.assertEqual(result, {})


class TestAPIGroups(unittest.TestCase):
    """Tests for group operations."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    @patch("hypothesisapi.requests.get")
    def test_get_groups(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "group1"}, {"id": "group2"}]
        mock_get.return_value = mock_response

        result = self.api.get_groups()
        self.assertEqual(len(result), 2)

    @patch("hypothesisapi.requests.post")
    def test_create_group(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "newgroup", "name": "Test Group"}
        mock_post.return_value = mock_response

        result = self.api.create_group("Test Group", description="A test group")
        self.assertEqual(result["name"], "Test Group")

    @patch("hypothesisapi.requests.get")
    def test_get_group(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "group1", "name": "Test Group"}
        mock_get.return_value = mock_response

        result = self.api.get_group("group1")
        self.assertEqual(result["id"], "group1")

    @patch("hypothesisapi.requests.patch")
    def test_update_group(self, mock_patch):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "group1", "name": "Updated Name"}
        mock_patch.return_value = mock_response

        result = self.api.update_group("group1", name="Updated Name")
        self.assertEqual(result["name"], "Updated Name")

    def test_update_group_no_fields_raises(self):
        """Test update_group raises ValueError when no fields provided."""
        with self.assertRaises(ValueError) as ctx:
            self.api.update_group("group1")
        self.assertIn("name", str(ctx.exception))
        self.assertIn("description", str(ctx.exception))

    @patch("hypothesisapi.requests.get")
    def test_get_group_members(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"userid": "user1"}, {"userid": "user2"}]
        mock_get.return_value = mock_response

        result = self.api.get_group_members("group1")
        self.assertEqual(len(result), 2)

    @patch("hypothesisapi.requests.delete")
    def test_leave_group(self, mock_delete):
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response

        result = self.api.leave_group("group1")
        self.assertEqual(result, {})


class TestAPIProfile(unittest.TestCase):
    """Tests for profile operations."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    @patch("hypothesisapi.requests.get")
    def test_get_profile(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"userid": "acct:testuser@hypothes.is"}
        mock_get.return_value = mock_response

        result = self.api.get_profile()
        self.assertIn("userid", result)

    @patch("hypothesisapi.requests.get")
    def test_get_profile_groups(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "group1"}]
        mock_get.return_value = mock_response

        result = self.api.get_profile_groups()
        self.assertEqual(len(result), 1)


class TestAPIUsers(unittest.TestCase):
    """Tests for user operations (admin)."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    @patch("hypothesisapi.requests.post")
    def test_create_user(self, mock_post):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "userid": "acct:newuser@myauthority.com",
            "username": "newuser",
        }
        mock_post.return_value = mock_response

        result = self.api.create_user(
            authority="myauthority.com",
            username="newuser",
            email="newuser@example.com",
        )
        self.assertEqual(result["username"], "newuser")

    @patch("hypothesisapi.requests.get")
    def test_get_user(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"userid": "acct:testuser@hypothes.is"}
        mock_get.return_value = mock_response

        result = self.api.get_user("acct:testuser@hypothes.is")
        self.assertIn("userid", result)

    @patch("hypothesisapi.requests.patch")
    def test_update_user(self, mock_patch):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "userid": "acct:testuser@hypothes.is",
            "display_name": "New Name",
        }
        mock_patch.return_value = mock_response

        result = self.api.update_user(
            "acct:testuser@hypothes.is", display_name="New Name"
        )
        self.assertEqual(result["display_name"], "New Name")


class TestExceptions(unittest.TestCase):
    """Tests for custom exceptions."""

    def test_hypothesis_api_error(self):
        error = HypothesisAPIError("Test error", status_code=500, response="Error details")
        self.assertEqual(str(error), "Test error")
        self.assertEqual(error.status_code, 500)
        self.assertEqual(error.response, "Error details")

    def test_authentication_error_inheritance(self):
        error = AuthenticationError("Auth failed")
        self.assertIsInstance(error, HypothesisAPIError)

    def test_not_found_error_inheritance(self):
        error = NotFoundError("Not found")
        self.assertIsInstance(error, HypothesisAPIError)

    def test_forbidden_error_inheritance(self):
        error = ForbiddenError("Permission denied")
        self.assertIsInstance(error, HypothesisAPIError)

    def test_forbidden_error_does_not_shadow_builtin(self):
        """Ensure ForbiddenError doesn't shadow Python's PermissionError."""
        # Python's builtin PermissionError should still be accessible
        try:
            raise PermissionError("OS permission error")
        except PermissionError as e:
            self.assertEqual(str(e), "OS permission error")
            # Verify it's the builtin, not ours
            self.assertNotIsInstance(e, HypothesisAPIError)


class TestDeprecatedMethods(unittest.TestCase):
    """Tests for deprecated methods."""

    def setUp(self):
        self.api = API(username="testuser", api_key="testkey")

    @patch("hypothesisapi.requests.get")
    def test_search_id_deprecation_warning(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "abc123"}
        mock_get.return_value = mock_response

        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = self.api.search_id("abc123")
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, DeprecationWarning))
            self.assertIn("deprecated", str(w[0].message))


if __name__ == "__main__":
    unittest.main()
