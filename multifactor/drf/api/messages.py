from django.contrib.messages import constants

from rest_framework import status as http_status
from rest_framework.response import Response


class Message(Response):
    level = constants.INFO

    def __init__(self, message, status=http_status.HTTP_200_OK, *args, **kwargs):
        super().__init__(
            data={
                "message": message,
                "level": self.level
            },
            status=status,
            *args,
            **kwargs
        )


class Info(Message):
    level = constants.INFO


class Success(Message):
    level = constants.SUCCESS


class Warn(Message):
    level = constants.WARNING


class Error(Message):
    level = constants.ERROR

    def __init__(self, message, status=http_status.HTTP_500_INTERNAL_SERVER_ERROR, *args, **kwargs):
        super().__init__(message=message, status=status, *args, **kwargs)
