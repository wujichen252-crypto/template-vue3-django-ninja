"""Tests for response module."""
import pytest
from core.response import create_response, create_error_response


class TestResponse:
    """Test cases for response utilities."""

    def test_create_response_success(self):
        """Test create_response returns success response."""
        data = {"key": "value"}
        response = create_response(data)

        assert response["code"] == 200
        assert response["data"] == data
        assert response["msg"] == "ok"
        assert "request_id" in response

    def test_create_response_with_message(self):
        """Test create_response with custom message."""
        data = {"key": "value"}
        response = create_response(data, msg="操作成功")

        assert response["code"] == 200
        assert response["data"] == data
        assert response["msg"] == "操作成功"

    def test_create_error_response(self):
        """Test create_error_response returns error response."""
        response = create_error_response(400, "参数错误")

        assert response["code"] == 400
        assert response["data"] is None
        assert response["msg"] == "参数错误"
        assert "request_id" in response

    def test_create_error_response_with_data(self):
        """Test create_error_response with additional data."""
        error_data = {"field": "username", "message": "用户名不能为空"}
        response = create_error_response(400, "参数错误", data=error_data)

        assert response["code"] == 400
        assert response["data"] == error_data
        assert response["msg"] == "参数错误"

    def test_create_error_response_with_default_message(self):
        """Test create_error_response with default message."""
        response = create_error_response(500)

        assert response["code"] == 500
        assert response["data"] is None
        assert response["msg"] == "error"
