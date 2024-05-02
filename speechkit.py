import requests

from config import FOLDER_ID, RUS, URL_SPEECHKIT_TEXT, URL_SPEECHKIT_VOICE
from utils import logging
from iam_token import get_iam_token


def text_to_speech(text: str):
    """Функция для преобразования текста в ГС"""
    iam_token = get_iam_token()
    # Аутентификация через IAM-токен
    headers = {
        "Authorization": f"Bearer {iam_token}",
    }
    data = {
        "text": text,  # текст, который нужно преобразовать в голосовое сообщение
        "lang": RUS,
        "voice": "filipp",  # голос Филлипа
        "folderId": FOLDER_ID,
    }
    # Выполняем запрос
    response = requests.post(url=URL_SPEECHKIT_VOICE, headers=headers, data=data)

    if response.status_code == 200:
        return True, response.content  # Возвращаем голосовое сообщение
    else:
        logging.error("При запросе в SpeechKit возникла ошибка, функция text_to_speech")
        return False, "При запросе в SpeechKit возникла ошибка"


def speech_to_text(data):
    """Функция для преобразования ГС в текст"""
    iam_token = get_iam_token()

    # Указываем параметры запроса
    params = "&".join(
        [
            "topic=general",  # используем основную версию модели
            f"folderId={FOLDER_ID}",
            "lang=ru-RU",  # распознаём голосовое сообщение на русском языке
        ]
    )

    # Аутентификация через IAM-токен
    headers = {
        "Authorization": f"Bearer {iam_token}",
    }

    # Выполняем запрос
    response = requests.post(
        url=URL_SPEECHKIT_TEXT + params, headers=headers, data=data
    )

    # Читаем json в словарь
    decoded_data = response.json()
    # Проверяем, не произошла ли ошибка при запросе
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио
    else:
        logging.error("При запросе в SpeechKit возникла ошибка, функция speech_to_text")
        return False, "При запросе в SpeechKit возникла ошибка"
