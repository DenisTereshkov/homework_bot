import logging
import os
import sys
import time
from http import HTTPStatus

import requests
from dotenv import load_dotenv
from telebot import TeleBot
from telebot.apihelper import ApiException

import exeptions


load_dotenv()

TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверяет доступность переменных окружения."""
    logger = logging.getLogger(__name__)
    tokens = {
        'TELEGRAM_CHAT_ID': TELEGRAM_CHAT_ID,
        'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
        'PRACTICUM_TOKEN': PRACTICUM_TOKEN
    }
    problem_with_token = False
    for token in tokens:
        if tokens[token] is None:
            problem_with_token = True
            logger.critical(
                f'Отсутствует обязательная переменная окружения {token}'
                'Программа принудительно остановлена.'
            )
    if problem_with_token:
        raise exeptions.TokensException(
            'Отсутствует обязательная переменная окружения. '
            'Проверьте логи.'
        )


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    logger = logging.getLogger(__name__)
    logger.debug(
        'Начало процесса отправки сообщения в Telegram. '
        f'Текст: {message}'
    )
    message_sent = False
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except ApiException as error:
        logger.error(f'Неудачная отправка сообщения в Telegram. {error}')
    else:
        message_sent = True
        logger.debug(f'Отправка сообщения в Telegram. Текст: {message}')
    finally:
        return message_sent


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API."""
    logger = logging.getLogger(__name__)
    payload = {'from_date': timestamp}
    api_data = {
        'url': ENDPOINT,
        'params': payload,
        'headers': HEADERS,
    }
    logger.debug(msg=(
        'Делаем запрос к API. Endpoint: {url}, '
        'Params: {params}, Headers: {headers}.'
    ).format(**api_data))
    try:
        response = requests.get(
            api_data['url'],
            params=api_data['params'],
            headers=api_data['headers']
        )
    except requests.RequestException as error:
        error_message = (
            f'Проблема с доступом в эндпоит. {error} '
            'Программа принудительно остановлена.'
        )
        raise exeptions.APIAnswerException(error_message)
    if response.status_code != HTTPStatus.OK:
        error_message = f'Код ответа API {response.status_code}'
        raise exeptions.APIAnswerException(error_message)
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    if not isinstance(response, dict):
        error_message = (
            f'Передан неверный тип данный: {type(response)}. '
            'Ожидаемый тип: dict'
        )
        raise TypeError(error_message)
    if 'homeworks' not in response:
        error_message = 'API не соответствует документации'
        raise exeptions.ApiResponseException(error_message)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        error_message = 'Передан неверный тип данный'
        raise TypeError(error_message)
    return homeworks


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    if 'homework_name' not in homework:
        error_message = 'Переменная homework_name отсутствует'
        raise exeptions.ParseStatusException(error_message)
    if 'status' not in homework:
        error_message = 'Переменная homework_name отсутствует'
        raise exeptions.ParseStatusException(error_message)
    if homework['status'] not in HOMEWORK_VERDICTS:
        error_message = 'Неожиданный status'
        raise exeptions.ParseStatusException(error_message)
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_error_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            homework = check_response(response)
            if not homework:
                logger.debug('Новый ревью нет.')
            else:
                homework_statuse = parse_status(homework[0])
                sending_message = send_message(bot, homework_statuse)
                if sending_message:
                    if response.get('current_date', None):
                        timestamp = response.get('current_date')
                    else:
                        raise exeptions.EmptyCurrentDateException(
                            current_error_message
                        )
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message, exc_info=True)
            if message != current_error_message:
                send_message(bot, message)
                current_error_message = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        encoding='utf-8',
        filename='event_journal.log',
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.DEBUG,
        filemode='w'
    )
    logger = logging.getLogger(__name__)
    handler = logging.StreamHandler(stream=sys.stdout)
    logger.addHandler(handler)
    logger.info('Бот запущен')
    main()
