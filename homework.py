import requests, os, time
from dotenv import load_dotenv
import telegram

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRAKTIKUN_TOKEN')
TELEGRAM_TOKEN = os.getenv('TOKEN_BOT')
TELEGRAM_CHAT_ID = os.getenv('chat_id')

RETRY_TIME = 5
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message):
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)


def get_api_answer(current_timestamp):
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception:
        # тут добавить логирование
        print(f'Ошибка запроса')
        return False
    else:
        homework_status = response.json()
        return homework_status


def check_response(response):

    if type(response)==dict and 'homeworks' in response:
        return response.get('homeworks')
    return False


def parse_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    # ...

    verdict = HOMEWORK_STATUSES[homework_status]

    # ...

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True
    return False


def main():
    """Основная логика работы бота."""

    # ...

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    # current_timestamp = int(time.time())
    current_timestamp = '0'

    # ...

    while check_tokens():
        try:
            response = get_api_answer(current_timestamp)

            homework_dict = check_response(response)
            for hw in homework_dict:
                send_message(bot, parse_status(hw))

            current_timestamp = response.get('current_date')
            
            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            # ...
            time.sleep(RETRY_TIME)
        else:
            print('Я тут!')
            # ...


if __name__ == '__main__':
    main()
