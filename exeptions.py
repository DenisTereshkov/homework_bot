class TokensException(Exception):
    """Ошибка токена."""


class APIResponseException(Exception):
    """Ошибка ответа от API."""


class APIAnswerException(Exception):
    """Ошибка запроса к  API."""


class ParseStatusException(Exception):
    """Ошибка в статусе домашней работы."""


class EndpointException(Exception):
    """Ошибка доступа в эндпоинт."""


class EmptyCurrentDateException(Exception):
    """Ошибка пустой переменной 'current date'."""
