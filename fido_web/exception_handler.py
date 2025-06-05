from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.db import IntegrityError
from rest_framework.exceptions import ValidationError


def custom_exception_handler(exc, context):
    # Handle Django IntegrityError (e.g., unique constraint)
    if isinstance(exc, IntegrityError):
        return Response(
            {
                "error": "Integrity error",
                "message": "A record with the same unique field already exists. Please use a different value.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Handle DRF ValidationError
    if isinstance(exc, ValidationError):
        return Response(
            {"error": "Validation error", "message": exc.detail},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Let DRF handle the rest
    response = drf_exception_handler(exc, context)
    if response is not None:
        # Standardize the error response format
        response.data = {"error": response.status_code, "message": response.data}
    else:
        # Unhandled errors (e.g., 500)
        return Response(
            {
                "error": "Server error",
                "message": "An unexpected error occurred. Please try again later.",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return response
