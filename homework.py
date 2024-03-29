import requests
import os
import time
from dotenv import load_dotenv
import telegram
import logging
import sys

load_dotenv()
logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv('PRAKTIKUN_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN_BOT')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 300
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    """отправляет сообщение в Telegram чат.
    определяемый переменной окружения TELEGRAM_CHAT_ID.

    Args:
        bot (_type_): экземпляр класса Bot
        message (_type_): строка с текстом сообщения.
    """
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except Exception:
        logger.error('Сообщение в Telegramm не отправлено')
    else:
        logger.info('Успешная отправка сообщения в Telegramm')


def get_api_answer(current_timestamp):
    """делает запрос к единственному эндпоинту API-сервиса.

    Args:
        current_timestamp (_type_): получает временную метку.

    Returns:
        dict: должна вернуть ответ от API по форме JSON в видео словаря
    """
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != 200:
            logger.error('Вернут не 200 код')
            raise
        return response.json()
    except requests.exceptions.RequestException:
        logger.error('Ошибка при запросе ответа от API')


def check_response(response):
    """проверяет ответ API на корректность.

    Args:
        response (dict): получает ответ API, приведенный к типам данных Python

    Raises:
        TypeError: Ответ пришел не в виде словаря
        Exception: В ответе API нет ключа "homeworks"
        TypeError: Ответ пришел не в виде списка

    Returns:
        list: функция должна вернуть список домашних работ
        (он может быть и пустым), доступный в ответе API по ключу 'homeworks'.
    """
    logger.debug('Запуск функции для проверки ответа API на корректность')
    if not isinstance(response, dict):
        logger.error('Ответ пришел не в виде словаря')
        raise TypeError('Ответ пришел не в виде словаря')
    if ('homeworks' not in response) or ('current_date' not in response):
        raise Exception
    if not isinstance(response.get('homeworks'), list):
        logger.error('Ответ пришел не в виде списка')
        raise TypeError('Ответ пришел не в виде списка')
    return response.get('homeworks')


def parse_status(homework):
    """извлекает из информации о конкретной домашней работе статус этой работы.

    Args:
        homework (list): один элемент из списка домашних работ.

    Raises:
        KeyError: Обнаружен недокументированный статус домашней работы

    Returns:
        str:  подготовленная для отправки в Telegram строка,
        содержащая один из вердиктов словаря HOMEWORK_STATUSES.
    """
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise KeyError('Обнаружен недокументированный статус домашней работы')
    verdict = HOMEWORK_VERDICTS[homework_status]
    message = f'Изменился статус проверки работы "{homework_name}" - {verdict}'
    return message


def check_tokens():
    """проверяет доступность переменных окружения.
    Переменные необходимы для работы программы.

    Returns:
        boolean: Если отсутствует хотя бы одна переменная окружения
        — функция должна вернуть False, иначе — True.
    """
    if all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)):
        return True
    logger.critical('Отсутствие переменных окружения во время запуска бота')
    return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while check_tokens():
        try:
            response = get_api_answer(current_timestamp)

            homework_dict = check_response(response)

            if len(homework_dict) == 0:
                logger.debug('Нет новых статусов')
            else:
                for hw in homework_dict:
                    send_message(bot, parse_status(hw))
            current_timestamp = response.get('current_date')
        except Exception as error:
            logger.critical(f'Сбой в работе программы: {error}')
            time.sleep(RETRY_TIME)
        else:
            logger.info('Все прошло удачно!')
            time.sleep(RETRY_TIME)


if __name__ == '__main__':

    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(stream=sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s  - %(message)s'
    )
    handler.formatter = formatter
    logger.addHandler(handler)
    main()
