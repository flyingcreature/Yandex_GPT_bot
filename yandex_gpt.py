import logging

import requests

from iam_token import get_iam_token

from config import (
    FOLDER_ID,
    GPT_MODEL,
    LOGS_PATH,
    MAX_MODEL_TOKENS,
    SYSTEM_PROMPT,
    URL_GPT,
    URL_TOKENS
)

logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.ERROR,
    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s",
    filemode="w",
)


def count_gpt_tokens(messages: list) -> int:
    """Функция для подсчёта токенов в сообщении"""
    iam_token = get_iam_token()

    headers = {
        "Authorization": f"Bearer {iam_token}",
        "Content-Type": "application/json",
    }
    data = {"modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}-lite", "messages": messages}
    try:
        return len(
            requests.post(url=URL_TOKENS, json=data, headers=headers).json()["tokens"]
        )

    except Exception as e:
        logging.error(
            f"Ошибка при подсчёте токенов{e}"
        )
        return 0


def ask_gpt_helper(messages):
    """
    Отправляет запрос к модели GPT с задачей и предыдущими ответами
    для получения ответа или следующего шага
    """
    iam_token = get_iam_token()

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {iam_token}",
        "x-folder-id": f"{FOLDER_ID}",
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}-lite",
        "completionOptions": {
            "stream": False,
            "temperature": 0.7,
            "maxTokens": MAX_MODEL_TOKENS,
        },
        "messages": SYSTEM_PROMPT
        + messages,  # добавляем к системному сообщению предыдущие сообщения
    }
    try:
        response = requests.post(url=URL_GPT, headers=headers, json=data)

    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}.")
        logging.error(f"Произошла непредвиденная ошибка: {e}.")
        return False, "Ошибка при обращении к GPT", None
    else:
        if response.status_code != 200:
            print("Не удалось получить ответ :(")
            logging.error(f"Получена ошибка: {response.json()}")
            return False, f"Ошибка GPT. Статус-код: {response.status_code}", None

        else:
            answer = response.json()["result"]["alternatives"][0]["message"]["text"]
            tokens_in_answer = count_gpt_tokens([{"role": "assistant", "text": answer}])
            return True, answer, tokens_in_answer
