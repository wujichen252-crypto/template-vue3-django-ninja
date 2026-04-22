"""Custom middleware."""
import uuid
from django.http import HttpRequest, HttpResponse


class RequestIDMiddleware:
    """Middleware to generate or propagate request_id for logging."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id

        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response
