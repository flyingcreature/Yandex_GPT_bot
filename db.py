import logging
import sqlite3

from config import DB_NAME, DB_TABLE_USERS_NAME, LOGS_PATH

logging.basicConfig(
    filename=LOGS_PATH,
    level=logging.ERROR,
    format="%(asctime)s FILE: %(filename)s IN: %(funcName)s MESSAGE: %(message)s",
    filemode="w",
)


def create_db():
    connection = sqlite3.connect(DB_NAME)
    connection.close()


def execute_query(query: str, data: tuple | None = None, db_name: str = DB_NAME):
    """
    Функция для выполнения запроса к базе данных.
    Принимает имя файла базы данных, SQL-запрос и опциональные данные для вставки.
    """
    try:
        connection = sqlite3.connect(db_name)
        cursor = connection.cursor()

        if data:
            cursor.execute(query, data)
            connection.commit()

        else:
            cursor.execute(query)

    except sqlite3.Error as e:
        print("Ошибка при выполнении запроса: ", e)
        logging.error("Ошибка при выполнении запроса: ", e)

    else:
        result = cursor.fetchall()
        connection.close()
        return result


def create_table():
    """
    Функция для создания таблицы.
    """
    try:
        sql_query = (
            f"CREATE TABLE IF NOT EXISTS {DB_TABLE_USERS_NAME} "
            f"(id INTEGER PRIMARY KEY, "
            f"user_id INTEGER, "
            f"message TEXT, "
            f"role TEXT, "
            f"total_gpt_tokens INTEGER, "
            f"tts_symbols INTEGER, "
            f"stt_blocks INTEGER);"
        )
        execute_query(sql_query)
        print("Таблица успешно создана")
        logging.info("Таблица успешно создана")

    except Exception as e:
        logging.error(
            f"Ошибка при создании таблицы: {e}"
        )


def add_new_user(user_id: int):
    """Функция добавления нового пользователя в базу"""
    if not is_user_in_db(user_id):
        sql_query = f"INSERT INTO {DB_TABLE_USERS_NAME} " f"(user_id) " f"VALUES (?);"

        execute_query(sql_query, (user_id,))
        print("Пользователь успешно добавлен")
        logging.info("Пользователь успешно добавлен")
    else:
        print("Пользователь уже существует!")
        logging.info("Пользователь уже существует!")


def update_row(user_id: int, column_name: str, new_value: str | int | None):
    """Функция для обновления значения таблицы"""
    if is_user_in_db(user_id):
        sql_query = (
            f"UPDATE {DB_TABLE_USERS_NAME} "
            f"SET {column_name} = ? "
            f"WHERE user_id = ?;"
        )

        execute_query(sql_query, (new_value, user_id))

    else:
        print("Пользователь не найден в базе")
        logging.info("Пользователь не найден в базе")


def get_all_users_data():
    """Функция для предоставления информации о пользователе"""
    sql_query = f"SELECT * " f"FROM {DB_TABLE_USERS_NAME};"

    result = execute_query(sql_query)
    return result


def is_user_in_db(user_id: int) -> bool:
    sql_query = f"SELECT user_id " f"FROM {DB_TABLE_USERS_NAME} " f"WHERE user_id = ?;"
    return bool(execute_query(sql_query, (user_id,)))


def add_message(user_id, full_message):
    """Функция, которая добавляет новое сообщение в таблицу"""
    if is_user_in_db(user_id):
        message, role, total_gpt_tokens, tts_symbols, stt_blocks = full_message
        # записываем в таблицу новое сообщение
        sql_query = (
            f"INSERT INTO {DB_TABLE_USERS_NAME} (user_id, message, role, total_gpt_tokens, tts_symbols, stt_blocks)"
            f"VALUES (?, ?, ?, ?, ?, ?)"
        )
        execute_query(
            sql_query,
            (user_id, message, role, total_gpt_tokens, tts_symbols, stt_blocks),
        )


def count_users(user_id):
    """Функция для подсчёта пользователей"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            sql_query = (
                f"SELECT COUNT(DISTINCT user_id) "
                f"FROM {DB_TABLE_USERS_NAME} "
                f"WHERE user_id <> ?"
            )
            cursor.execute(sql_query, (user_id,))
            count = cursor.fetchone()[0]
            return count
    except Exception as e:
        logging.error(
            f"Ошибка при подсчёте пользователей в бд: {e}"
        )


def select_n_last_messages(user_id, n_last_messages=4):
    """Функция для получения последних n сообщений пользователя"""
    messages = []  # список с сообщениями
    total_spent_tokens = 0  # количество потраченных токенов за всё время общения
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            sql_query = (
                f"SELECT message, role, total_gpt_tokens "
                f"FROM {DB_TABLE_USERS_NAME} "
                f"WHERE user_id=? "
                f"ORDER BY id DESC LIMIT ?"
            )
            cursor.execute(sql_query, (user_id, n_last_messages))
            data = cursor.fetchall()
            # проверяем data на наличие хоть какого-то полученного результата запроса
            # и на то, что в результате запроса есть хотя бы одно сообщение - data[0]
            if data and data[0]:
                # формируем список сообщений
                for message in reversed(data):
                    messages.append({"text": message[0], "role": message[1]})
                    total_spent_tokens = max(total_spent_tokens, message[2])
                    # находим максимальное количество потраченных токенов
            # если результата нет, так как у нас ещё нет сообщений - возвращаем значения по умолчанию
            return messages, total_spent_tokens
    except Exception as e:
        logging.error(
            f"Ошибка при получении последних n сообщений: {e}"
        )  # если ошибка - записываем её в логи
        return messages, total_spent_tokens


# подсчитываем количество потраченных пользователем ресурсов (<limit_type> - символы или аудиоблоки)
def count_all_limits(user_id, limit_type):
    """Функция для подсчёта потраченных ресурсов (<limit_type> - символы или аудиоблоки)"""
    try:
        with sqlite3.connect(DB_NAME) as conn:
            cursor = conn.cursor()
            # считаем лимиты по <limit_type>, которые использовал пользователь
            sql_query = (
                f"SELECT SUM({limit_type}) "
                f"FROM {DB_TABLE_USERS_NAME} "
                f"WHERE user_id=?"
            )
            cursor.execute(sql_query, (user_id,))
            data = cursor.fetchone()
            # проверяем data на наличие хоть какого-то полученного результата запроса
            # и на то, что в результате запроса мы получили какое-то число в data[0]
            if data and data[0]:
                # если результат есть и data[0] == какому-то числу, то:
                logging.info(
                    f"DATABASE: У user_id={user_id} использовано {data[0]} {limit_type}"
                )
                return data[
                    0
                ]  # возвращаем это число - сумму всех потраченных <limit_type>
            else:
                # результата нет, так как у нас ещё нет записей о потраченных <limit_type>
                return 0  # возвращаем 0

    except Exception as e:
        logging.error(
            f"Ошибка при подсчёте потраченных ресурсов: {e}"
        )  # если ошибка - записываем её в логи
        return 0
