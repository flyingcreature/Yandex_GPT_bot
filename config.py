from os import getenv

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = getenv("token")  # Токен бота

FOLDER_ID = getenv("folder_id")  # Folder_id для gpt

IAM_TOKEN = getenv("iam_token")  # Iam токен для gpt

HOME_DIR = "/home/student/Dev/Yandex_GPT_bot"  # путь к папке с проектом для удалённого сервера

LOGS_PATH = f"log_file.txt"  # Путь к файлу логов

ADMINS = [1645457137, 786540182]  # Список user_id админов

MAX_USERS = 10  # максимальное кол-во пользователей

MAX_MODEL_TOKENS = 120  # максимальное кол-во токенов в ответе GPT

COUNT_LAST_MSG = 4  # кол-во последних сообщений из диалога

MAX_USER_STT_BLOCKS = 10  # 10 аудиоблоков

MAX_USER_TTS_SYMBOLS = 5000  # 5 000 символов для расшифровок ГС

MAX_TTS_SYMBOLS = 200  # Максимальный размер ответа

MAX_USER_GPT_TOKENS = 5000  # 5 000 токенов для генерации текста

DB_NAME = f"db.sqlite"  # файл для базы данных

DB_TABLE_USERS_NAME = "users"  # Название таблицы

SYSTEM_PROMPT = [
    {
        "role": "system",
        "text": 'Ты веселый собеседник. Общайся с пользователем на "ты" и используй юмор. '
        "Поддерживай диалог. Не объясняй пользователю, что ты умеешь и можешь. "
        "Изображай человека, не включай в текст действий сделанных на фоне,"
        " например, как (смех)",
    }
]  # список с системным промтом

GPT_MODEL = "yandexgpt"  # Модель gpt

IAM_TOKEN_ENDPOINT = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"  # Адресс токена

IAM_TOKEN_PATH = f"{HOME_DIR}/token_data.json"  # Путь к json файлу с ключом

URL_TOKENS = "https://llm.api.cloud.yandex.net/foundationModels/v1/tokenizeCompletion"  # Ссылка на токены gpt

URL_GPT = (
    "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"  # Ссылка на gpt
)

URL_SPEECHKIT_VOICE = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"  # Ссылка на gpt которая преобразовывает текст в аудио

URL_SPEECHKIT_TEXT = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?"  # Ссылка на gpt которая преобразовывает аудио в текст

RUS = "ru-RU"  # Язык текста для ГС
