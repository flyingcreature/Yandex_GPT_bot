import json
import logging
import math

from config import (
    LOGS_PATH,
    MAX_USER_GPT_TOKENS,
    MAX_USER_STT_BLOCKS,
    MAX_USER_TTS_SYMBOLS,
    MAX_USERS,
)
from db import count_all_limits, count_users
from yandex_gpt import count_gpt_tokens

logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.ERROR,
    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s",
    filemode="w",
)


def load_data(path: str) -> dict:
    """
    Загружает данные из json по переданному пути и возвращает
    преобразованные данные в виде словаря.

    Если json по переданному
    пути не найден или его структура некорректна, то возвращает
    пустой словарь.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}


def save_data(data: dict, path: str) -> None:
    """
    Сохраняет переданный словарь в json по переданному пути.
    """
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def check_number_of_users(user_id: int) -> tuple[bool | None, str]:
    """Функция для получения количества уникальных пользователей, кроме самого пользователя"""
    count = count_users(user_id)
    if count is None:
        return None, "Ошибка при работе с БД"
    if count > MAX_USERS:
        return None, "Превышено максимальное количество пользователей"
    return True, ""


def is_gpt_token_limit(
    messages: list, total_spent_tokens: int
) -> tuple[int | None, str]:
    """Функция для проверки не превысил ли пользователь лимиты на общение с GPT"""
    all_tokens = count_gpt_tokens(messages) + total_spent_tokens
    if all_tokens > MAX_USER_GPT_TOKENS:
        return None, f"Превышен общий лимит GPT-токенов {MAX_USER_GPT_TOKENS}"
    return all_tokens, ""


def is_stt_block_limit(user_id: int, duration: int) -> tuple[int | None, str]:
    """Функция для проверки не превысил ли пользователь лимиты на преобразование аудио в текст"""

    # Переводим секунды в аудиоблоки
    audio_blocks = math.ceil(duration / 15)  # округляем в большую сторону
    # Функция из БД для подсчёта всех потраченных пользователем аудиоблоков
    all_blocks = count_all_limits(user_id, "stt_blocks") + audio_blocks

    # Проверяем, что аудио длится меньше 30 секунд
    if duration >= 30:
        return None, "SpeechKit STT работает с голосовыми сообщениями меньше 30 секунд"

    # Сравниваем all_blocks с количеством доступных пользователю аудиоблоков
    if all_blocks >= MAX_USER_STT_BLOCKS:
        msg = (
            f"Превышен общий лимит SpeechKit STT {MAX_USER_STT_BLOCKS}."
            f" Использовано {all_blocks} блоков. Доступно: {MAX_USER_STT_BLOCKS - all_blocks}"
        )
        return None, msg
    return all_blocks, ""


def is_tts_symbol_limit(user_id: int, text: str) -> tuple[int | None, str]:
    """Функция для проверки не превысил ли пользователь лимиты на преобразование текста в аудио"""
    text_symbols = len(text)

    # Функция из БД для подсчёта всех потраченных пользователем символов
    all_symbols = count_all_limits(user_id, "tts_symbols") + text_symbols

    # Сравниваем all_symbols с количеством доступных пользователю символов
    if all_symbols >= MAX_USER_TTS_SYMBOLS:
        msg = (
            f"Превышен общий лимит SpeechKit TTS {MAX_USER_TTS_SYMBOLS}."
            f" Использовано: {all_symbols} символов. Доступно: {MAX_USER_TTS_SYMBOLS - all_symbols}"
        )

        return None, msg

    return all_symbols, ""
