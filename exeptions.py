class TokensException(Exception):
    """Ошибка токена."""

    pass


class APIResponseException(Exception):
    """Ошибка ответа от API."""

    pass


class APIAnswerException(Exception):
    """Ошибка запроса к  API."""

    pass


class ParseStatusException(Exception):
    """Ошибка в статусе домашней работы."""

    pass
