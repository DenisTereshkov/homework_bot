import time
import logging
import os
import sys
import requests
from http import HTTPStatus

from dotenv import load_dotenv
from telebot import TeleBot

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
    for token in TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, PRACTICUM_TOKEN:
        if token is None:
            logger.critical(
                'Отсутствует обязательная переменная окружения. '
                'Программа принудительно остановлена.'
            )
            raise exeptions.TokensException(
                'Отсутствует обязательная переменная окружения'
            )


def send_message(bot, message):
    """Отправляет сообщение в Telegram-чат."""
    logger = logging.getLogger(__name__)
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Неудачная отправка сообщения в Telegram. {error}')
    else:
        logger.debug(f'Отправка сообщения в Telegram. Текст: {message}')


def get_api_answer(timestamp):
    """Делает запрос к единственному эндпоинту API."""
    payload = {'from_date': timestamp - (2629743)}
    logger = logging.getLogger(__name__)
    try:
        response = requests.get(ENDPOINT, params=payload, headers=HEADERS)
    except Exception as error:
        logger.error(
            f'Проблема с доступом в эндпоит. {error} '
            'Программа принудительно остановлена.'
        )
    if response.status_code != HTTPStatus.OK:
        error_massage = f'Код ответа API {response.status_code}'
        logger.error(error_massage, exc_info=True)
        raise exeptions.APIAnswerException(error_massage)
    return response.json()


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    logger = logging.getLogger(__name__)
    if type(response) is not dict:
        error_massage = 'Передан неверный тип данный'
        logger.error(error_massage, exc_info=True)
        raise TypeError(error_massage)
    if 'homeworks' not in response:
        error_massage = 'API не соответствует документации'
        logger.error(error_massage, exc_info=True)
        raise exeptions.ApiResponseException(error_massage)
    if type(response['homeworks']) is not list:
        error_massage = 'Передан неверный тип данный'
        logger.error(error_massage, exc_info=True)
        raise TypeError(error_massage)


def parse_status(homework):
    """Извлекает из информации о домашней работе статус этой работы."""
    logger = logging.getLogger(__name__)
    if 'homework_name' not in homework:
        error_massage = 'Переменная homework_name отсутствует'
        logger.error(error_massage, exc_info=True)
        raise exeptions.ParseStatusException(error_massage)
    if 'status' not in homework:
        error_massage = 'Переменная homework_name отсутствует'
        logger.error(error_massage, exc_info=True)
        raise exeptions.ParseStatusException(error_massage)
    if homework['status'] not in HOMEWORK_VERDICTS:
        error_massage = 'Неожиданный status'
        logger.error(error_massage, exc_info=True)
        raise exeptions.ParseStatusException(error_massage)
    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = TeleBot(TELEGRAM_TOKEN)
    timestamp = int(time.time())
    current_status_message = ''
    current_error_message = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            homework = response['homeworks'][0]
            homework_statuse = parse_status(homework)
            if homework_statuse != current_status_message:
                current_status_message = homework_statuse
                send_message(bot, current_status_message)
            time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != current_error_message:
                send_message(bot, message)
                current_error_message = message
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
