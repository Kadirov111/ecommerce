from rest_framework.response import Response
from rest_framework import status


def create_success_response(data=None, message=None, status_code=status.HTTP_200_OK, meta=None):
    response_data = {"success": True}

    if data is not None:
        response_data["data"] = data

    if message:
        response_data["message"] = message

    if meta:
        response_data["meta"] = meta

    return Response(response_data, status=status_code)


def create_error_response(code, message, details=None, status_code=status.HTTP_400_BAD_REQUEST):
    response_data = {
        "success": False,
        "error": {
            "code": code,
            "message": message
        }
    }

    if details:
        response_data["error"]["details"] = details

    return Response(response_data, status=status_code)