#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_hypothesisapi
----------------------------------

Tests for `hypothesisapi` module.
"""

import unittest
from unittest.mock import Mock, patch

from hypothesisapi import (
    API,
    API_URL,
    APP_URL,
    HypothesisAPIError,
    AuthenticationError,
    NotFoundError,
    PermissionError,
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

    def test_handle_response_auth_error(self):
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        with self.assertRaises(AuthenticationError):
            self.api._handle_response(mock_response)

    def test_handle_response_permission_error(self):
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        with self.assertRaises(PermissionError):
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

    def test_permission_error_inheritance(self):
        error = PermissionError("Permission denied")
        self.assertIsInstance(error, HypothesisAPIError)


if __name__ == "__main__":
    unittest.main()
