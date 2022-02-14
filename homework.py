import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv
# from exceptions import MyError
import exceptions

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = 250956699

RETRY_TIME = 10
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def create_logger(name):
    """Инициализируем логгер."""
    logger = logging.getLogger(name)
    FORMAT = '%(asctime)s - %(lineno)s:%(levelname)s - %(message)s'
    logger.setLevel(logging.DEBUG)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(logging.Formatter(FORMAT))
    logger.addHandler(stream_handler)
    return logger


logger = create_logger(__name__)


def send_message(bot, message):
    """Отправляет сообщение в телеграм."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.info(f'Сообщение "{message}" отправлено')
    except Exception as error:
        logger.error(
            f'Сообщение "{message}" не отправлено по причине: "{error}"'
        )


def get_api_answer(current_timestamp):
    """Делает запрос к эндопоинту API яндекс практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        logger.error('Эндпоинт недоступен')
        raise exceptions.MyError('Эндпоинт недоступен')
    if response.status_code != 200:
        logger.error('Код ответа сервера не соответствует ожидаемому')
        raise ValueError('Код ответа сервера не соответствует ожидаемому')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    key = 'homeworks'
    if type(response) != dict:
        logger.error('Некотректный формат ответа от API')
        raise TypeError(f'{type(response)} не соответстует "dict"')
    if key not in response:
        logger.error(f'Ключ "{key}" отсутствует в ответе API')
        raise KeyError(f'Ключ "{key}" отсутствует в ответе API')
    homework = response.get(key)
    if type(homework) != list:
        logger.error('Домашки приходят не в виде списка')
        raise TypeError('Домашки приходят не в виде списка')
    return homework


def parse_status(homework):
    """Извлекает стаус работы из ответа."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_STATUSES:
        logger.error(f'Статуc "{homework_status}" недокументирован')
        raise KeyError(
            'недокументированный статус домашней работы в ответе API'
        )
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    else:
        logger.critical('Проблема с токенами!')
        SystemExit


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logger.info('Бот запущен')
    sended_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if len(homework) >= 1:
                status = parse_status(homework[0])
                send_message(bot, status)
                current_timestamp = int(time.time())
            else:
                logger.debug('Новых статусов нет')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != sended_message:
                send_message(bot, message)
                sended_message = message
            time.sleep(RETRY_TIME)
        else:
            logger.info(
                'Цикл прошёл успешно'
            )


if __name__ == '__main__':
    main()
