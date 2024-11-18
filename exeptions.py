import requests


class TokensException(Exception):
    """Ошибка токена."""


class APIResponseException(Exception):
    """Ошибка ответа от API."""


class APIAnswerException(Exception):
    """Ошибка запроса к  API."""


class ParseStatusException(Exception):
    """Ошибка в статусе домашней работы."""


class EndpointException(requests.RequestException):
    """Ошибка доступа в эндпоинт."""
