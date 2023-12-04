from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response

def fail(error):
    error_response = {
        'status': False,
        'message': "fail",
        'error': error
    }
    return error_response

def success(data):
    success_message = {
        'status': True,
        'message': 'success',
        'data': data
    }
    return success_message

class CustomException(APIException):
    status_code = 404
    default_detail = "Not Found"

def custom_exception_handler(exc, context):
    if isinstance(exc, APIException):
        status_code = exc.status_code
    else:
        status_code = 500  # Default to 500 for other exceptions

    return Response(fail(str(exc)), status=status_code)
