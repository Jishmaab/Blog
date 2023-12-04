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

def custom_exception_handler(exc, context):
    if isinstance(exc, APIException):
        return Response(fail(exc.detail), exc.status_code)
    else:
        return Response(fail(str(exc)),500)