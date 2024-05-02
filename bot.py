import logging

import telebot
from telebot.types import Message

import db
from config import ADMINS, BOT_TOKEN, COUNT_LAST_MSG, LOGS_PATH, MAX_USERS
from speechkit import speech_to_text, text_to_speech
from utils import (
    check_number_of_users,
    is_gpt_token_limit,
    is_stt_block_limit,
    is_tts_symbol_limit,
)
from yandex_gpt import ask_gpt_helper

logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.DEBUG,
    format="%(asctime)s %(message)s",
    filemode="w",
)

bot = telebot.TeleBot(BOT_TOKEN)

# Создаем базу и табличку в ней
db.create_db()
db.create_table()


@bot.message_handler(commands=["start"])
def start(message):
    user_name = message.from_user.first_name
    user_id = message.from_user.id

    if not db.is_user_in_db(user_id):  # Если пользователя в базе нет
        if (
            len(db.get_all_users_data()) < MAX_USERS
        ):  # Если число зарегистрированных пользователей меньше допустимого
            db.add_new_user(user_id)  # Регистрируем нового пользователя
        else:
            text = "К сожалению, лимит пользователей исчерпан🙅‍♂️. Вы не сможете воспользоваться ботом😔"

            bot.send_message(chat_id=user_id, text=text)
            return

    # Этот блок срабатывает только для зарегистрированных пользователей
    text = (
        f"Привет👋🏿, {user_name}! Я бот собеседник, и мы вместе можем решить любой твой вопрос,"
        f" или просто поговорить 🎇.\n\n"
        "Так же я могу работать с голосовыми сообщениями просто запиши мне ГС🔊, "
        "и я c  удовольствием поговорю с тобой🗣️.\n\n"
        "Если возникнут вопросы используй команду /help\n"
        f"Ну что, начнём?"
    )

    bot.send_message(
        chat_id=user_id,
        text=text,
    )


@bot.message_handler(commands=["kill_my_session"])
def kill_session(message: Message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        try:
            db.update_row(user_id, "total_gpt_tokens", 0)
            db.update_row(user_id, "tts_symbols", 0)
            db.update_row(user_id, "stt_blocks", 0)
        except Exception as e:
            print(f"Произошла ошибка {e}, сессии не обновлены")
            logging.error(f"Произошла ошибка {e}, сессии не обновлены")
    else:
        print(f"{user_id} попытался обновить сессии")
        logging.info(f"{user_id} попытался обновить сессии")


@bot.message_handler(commands=["debug"])
def send_logs(message):
    user_id = message.from_user.id
    if user_id in ADMINS:
        try:
            with open(LOGS_PATH, "rb") as f:
                bot.send_document(message.chat.id, f)
        except telebot.apihelper.ApiTelegramException:
            bot.send_message(chat_id=message.chat.id, text="Логов нет!")
    else:
        print(f"{user_id} захотел посмотреть логи")
        logging.info(f"{user_id} захотел посмотреть логи")


@bot.message_handler(commands=["help"])
def help_command(message: Message):
    text = (
        "👋 Я твой цифровой собеседник.\n\n"
        "Что бы воспользоваться функцией gpt помощника 🕵‍♀️ следуй инструкциям бота .\n\n"
        "Этот бот сделан на базе нейронной сети YandexGPT Lite. \n"
        "Это мой первый опыт знакомства с gpt, "
        "поэтому не переживай если возникла какая-то ошибка. Просто сообщи мне об этом)\n"
        "И я постараюсь её решить.\n\n"
        " P.S. мои контакты можно найти в описании бота"
    )
    bot.send_message(chat_id=message.chat.id, text=text)


def filter_hello(message):
    word = "привет"
    return word in message.text.lower()


@bot.message_handler(content_types=["text"], func=filter_hello)
def say_hello(message: Message):
    user_name = message.from_user.first_name
    bot.send_message(chat_id=message.chat.id, text=f"{user_name}, приветики 👋!")


def filter_bye(message):
    word = "пока"
    return word in message.text.lower()


@bot.message_handler(content_types=["text"], func=filter_bye)
def say_bye(message: Message):
    bot.send_message(chat_id=message.chat.id, text="Пока, заходи ещё!")


# Декоратор для обработки голосовых сообщений, полученных ботом
@bot.message_handler(content_types=["voice"])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.from_user.id
        # Проверка на максимальное количество пользователей
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(chat_id=user_id, text=error_message)
            return

        # Проверка на доступность аудиоблоков
        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(chat_id=user_id, text=error_message)
            return

        # Обработка голосового сообщения
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        status_stt, stt_text = speech_to_text(file)
        if not status_stt:
            bot.send_message(chat_id=user_id, text=stt_text)
            return

        # Запись в БД
        db.add_message(
            user_id=user_id, full_message=[stt_text, "user", 0, 0, stt_blocks]
        )

        # Проверка на доступность GPT-токенов
        last_messages, total_spent_tokens = db.select_n_last_messages(
            user_id, COUNT_LAST_MSG
        )
        total_gpt_tokens, error_message = is_gpt_token_limit(
            last_messages, total_spent_tokens
        )
        if error_message:
            bot.send_message(chat_id=user_id, text=error_message)
            return

        # Запрос к GPT и обработка ответа
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt_helper(last_messages)
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer

        # Проверка на лимит символов для SpeechKit
        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)

        # Запись ответа GPT в БД
        db.add_message(
            user_id=user_id,
            full_message=[answer_gpt, "assistant", total_gpt_tokens, tts_symbols, 0],
        )

        if error_message:
            bot.send_message(chat_id=user_id, text=error_message)
            return

        # Преобразование ответа в аудио и отправка
        status_tts, voice_response = text_to_speech(answer_gpt)

        if status_tts:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
        else:
            bot.send_message(
                chat_id=user_id, text=answer_gpt, reply_to_message_id=message.id
            )

    except Exception as e:
        user_id = message.from_user.id
        logging.error(f"Ошибка при отправке ГС в функции handle_voice: {e}")
        bot.send_message(
            chat_id=user_id,
            text="Не получилось ответить. Попробуй записать другое сообщение",
        )


@bot.message_handler(content_types=["text"])
def handle_text(message):
    try:
        user_id = message.from_user.id
        # ВАЛИДАЦИЯ: проверяем, есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = check_number_of_users(user_id)

        if not status_check_users:
            bot.send_message(user_id, error_message)  # мест нет =(
            return

        # БД: добавляем сообщение пользователя и его роль в базу данных
        full_user_message = [message.text, "user", 0, 0, 0]

        db.add_message(user_id=user_id, full_message=full_user_message)

        # ВАЛИДАЦИЯ: считаем количество доступных пользователю GPT-токенов
        # получаем последние 4 (COUNT_LAST_MSG) сообщения и количество уже потраченных токенов
        last_messages, total_spent_tokens = db.select_n_last_messages(
            user_id, COUNT_LAST_MSG
        )

        # получаем сумму уже потраченных токенов + токенов в новом сообщении и оставшиеся лимиты пользователя
        total_gpt_tokens, error_message = is_gpt_token_limit(
            last_messages, total_spent_tokens
        )

        if error_message:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(chat_id=user_id, text=error_message)
            return

        # GPT: отправляем запрос к GPT
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt_helper(last_messages)

        # GPT: обрабатываем ответ от GPT
        if not status_gpt:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(chat_id=user_id, text=answer_gpt)
            return
        # сумма всех потраченных токенов + токены в ответе GPT
        total_gpt_tokens += tokens_in_answer

        # БД: добавляем ответ GPT и потраченные токены в базу данных
        full_gpt_message = [answer_gpt, "assistant", total_gpt_tokens, 0, 0]
        db.add_message(user_id=user_id, full_message=full_gpt_message)

        bot.send_message(
            chat_id=user_id, text=answer_gpt, reply_to_message_id=message.id
        )  # отвечаем пользователю текстом
    except Exception as e:
        logging.error(e)  # если ошибка — записываем её в логи
        bot.send_message(
            message.from_user.id,
            "Не получилось ответить. Попробуй написать другое сообщение",
        )


# обрабатываем все остальные типы сообщений
@bot.message_handler(
    func=lambda message: True,
    content_types=[
        "audio",
        "photo",
        "voice",
        "video",
        "document",
        "text",
        "location",
        "contact",
        "sticker",
    ],
)
def send_echo(message: Message):
    text = (
        f"Вы отправили ({message.text}).\n"
        f"Но к сожалению я вас не понял😔, Отправь мне голосовое или текстовое сообщение, и я тебе отвечу🤗"
    )
    bot.send_message(chat_id=message.chat.id, text=text)


logging.info("Бот запущен")
bot.infinity_polling(timeout=60, long_polling_timeout=5)
