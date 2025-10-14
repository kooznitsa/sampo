from rest_framework import status
from rest_framework.exceptions import APIException


class MenuNotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = {'message': 'Menu not found'}
