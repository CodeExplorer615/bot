import telebot
import sqlite3
from datetime import datetime
import logging
import math

# -------------------- Логирование --------------------
logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

ALLOWED_USERS = [101010101]   # список пользователей, кому можно заходить

# -------------------- Инициализация бота --------------------
bot = telebot.TeleBot('8352449890:AAHKY9rblZSYQv1GRfqj7Nn2lYIftv_gHc0')

# -------------------- Работа с БД --------------------
def init_db():
    conn = sqlite3.connect('chat_messagesq.db')
    c = conn.cursor()
    # Таблица сообщений с колонкой deleted
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT,
                 message_link TEXT,
                 is_newbie INTEGER,
                 timestamp TEXT,
                 del_id 
                 )''')
    # Таблица связей пользователей и сообщений
    c.execute('''CREATE TABLE IF NOT EXISTS user_data (
                    user_id INTEGER,
                    message_id INTEGER,
                    FOREIGN KEY(message_id) REFERENCES messages(id)
                 )''')
    conn.commit()
    conn.close()
    logging.info("База данных инициализирована")


def mark_deleted(message_id: int) -> bool:
    """Помечаем сообщение как удалённое"""
    try:
        conn = sqlite3.connect('chat_messagesq.db')
        c = conn.cursor()
        c.execute('UPDATE messages SET is_newbie = 1 WHERE id = ?', (message_id,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Ошибка при пометке deleted для {message_id}: {e}")
        return False


def clear_all_data() -> bool:
    """Полностью очищает БД"""
    try:
        conn = sqlite3.connect('chat_messagesq.db')
        c = conn.cursor()
        c.execute('DELETE FROM messages')
        c.execute('DELETE FROM user_data')
        conn.commit()
        conn.close()
        logging.info("БД полностью очищена админом")
        return True
    except Exception as e:
        logging.error(f"Ошибка при очистке БД: {e}")
        return False


def split_text(text, limit=4000):
    """Разбивает текст на части для удобного вывода"""
    parts = []
    lines = text.split('\n')
    buffer = ''
    for line in lines:
        if len(buffer) + len(line) + 1 > limit:
            parts.append(buffer)
            buffer = line + '\n'
        else:
            buffer += line + '\n'
    if buffer:
        parts.append(buffer)
    return parts


# -------------------- Команды --------------------
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
📖 *Инструкция по боту:*

1️⃣ /start — Приветствие и информация  
2️⃣ /lk <ваш_id> — Войти в личный кабинет и посмотреть свои сообщения  
3️⃣ /rm <id> — Пометить сообщение как удалённое  
4️⃣ /help — Показать инструкцию  
5️⃣ /lk_admin — Админ: показать всю БД  
6️⃣ /rm_admin — Админ: очистить всю БД
"""
    bot.send_message(message.chat.id, help_text)


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id,
                     "Привет! Чтобы войти в личный кабинет, используй команду /lk <ваш_id>. "
                     "Для помощи — /help")


@bot.message_handler(commands=['lk'])
def lk_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❗ Используй формат: /lk <твой_id>")
        return
    try:
        user_id = int(parts[1])
        if user_id not in ALLOWED_USERS:
            bot.send_message(message.chat.id, "⛔ Доступ запрещён! ID не найден.")
            return

        conn = sqlite3.connect('chat_messagesq.db')
        c = conn.cursor()
        # Берём только активные сообщения
        c.execute('''SELECT m.id, m.username, m.message_link, m.timestamp
                     FROM messages m
                     JOIN user_data u ON m.id = u.message_id
                     WHERE u.user_id = ? AND m.deleted = 0''', (user_id,))
        rows = c.fetchall()
        conn.close()

        if rows:
            formatted = []
            for r in rows:
                formatted.append(
                    f"🆔 ID: {r[0]}\n"
                    f"👤 Юзер: {r[1]}\n"
                    f"🔗 Ссылка: {r[2]}\n"
                    f"🕒 Дата: {r[3]}\n"
                    + "-"*30
                )
            full_text = "\n".join(formatted)
            for part in split_text(full_text):
                bot.send_message(message.chat.id, part)
        else:
            bot.send_message(message.chat.id, "❗ У вас пока нет активных сообщений.")
    except ValueError:
        bot.send_message(message.chat.id, "❗ Айди должен быть числом.")


@bot.message_handler(commands=['rm'])
def rm_command(message):
    parts = message.text.split()
    if len(parts) < 2:
        bot.send_message(message.chat.id, "❗ Используй: /rm <id_сообщения>")
        return
    try:
        message_id = int(parts[1])
        success = mark_deleted(message_id)
        if success:
            bot.send_message(message.chat.id, f"✅ Сообщение с ID {message_id} помечено как удалённое.")
        else:
            bot.send_message(message.chat.id, f"❌ Ошибка при удалении сообщения {message_id}.")
    except ValueError:
        bot.send_message(message.chat.id, "❗ ID должен быть числом.")


# -------------------- Админские --------------------
@bot.message_handler(commands=['lk_admin'])
def lkadminq_command(message):
    conn = sqlite3.connect('chat_messagesq.db')
    c = conn.cursor()
    c.execute('SELECT * FROM messages ORDER BY id DESC')
    rows = c.fetchall()
    conn.close()
    if not rows:
        bot.send_message(message.chat.id, "❗ База пуста.")
        return

    formatted = []
    for r in rows:
        formatted.append(
            f"🆔 ID: {r[0]}\n"
            f"👤 Юзер: {r[1]}\n"
            f"🔗 Ссылка: {r[2]}\n"
            f"📌 Новичок: {'Да' if r[3] else 'Нет'}\n"
            f"🕒 Дата: {r[4]}\n"
            + "-"*30
        )
    full_text = "\n".join(formatted)
    for part in split_text(full_text):
        bot.send_message(message.chat.id, part)


@bot.message_handler(commands=['rm_admin'])
def rmadmin_command(message):
    if message.from_user.id not in ADMINS:
        bot.send_message(message.chat.id, "⛔ Доступ запрещён!")
        return
    success = clear_all_data()
    if success:
        bot.send_message(message.chat.id, "✅ База данных полностью очищена.")
    else:
        bot.send_message(message.chat.id, "❌ Ошибка при очистке базы.")


# Удаление диапазона сообщений (рмб)
@bot.message_handler(commands=['rmb'])
def handle_bulk_remove(message):
    try:
        # команда в формате: /rmb 100 200
        parts = message.text.split()
        if len(parts) != 3:
            bot.reply_to(message, "Используй так: /rmb 100 200")
            return

        start_id = int(parts[1])
        end_id = int(parts[2])

        conn = sqlite3.connect("chat_messagesq.db")
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE messages SET is_newbie = 0 WHERE id BETWEEN ? AND ?",
            (start_id, end_id)
        )

        conn.commit()
        conn.close()

        bot.reply_to(
            message,
            f"Сообщения с ID {start_id} по {end_id} помечены как удалённые"
        )

    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}")

# -------------------- Запуск --------------------
if __name__ == '__main__':
    init_db()
    try:
        logging.info("Бот запущен...")
        bot.infinity_polling()
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")
