import sqlite3
import random
import string
from datetime import datetime

# Функция генерации случайного username
def random_username():
    letters = ''.join(random.choices(string.ascii_lowercase, k=3))
    digits = ''.join(random.choices(string.digits, k=3))
    return f"user_{letters}{digits}"

# Функция для создания базы и таблицы
def init_and_fill_db(num_messages=300):
    conn = sqlite3.connect('chat_messages.db')
    c = conn.cursor()

    # Создаём таблицу messages, если не существует
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT,
                    message_text TEXT,
                    is_newbie INTEGER,
                    timestamp TEXT
                 )''')

    # Примерные тексты сообщений новичков
    sample_texts = [
        "Не понимаю как это работает",
        "Помогите, я новичок",
        "Что делать в этой ситуации?",
        "Как снять деньги?",
        "Первый раз пытаюсь арбитраж",
        "Не знаю что выбрать",
        "Поясните, пожалуйста",
        "Как это работает?",
        "Фз как дальше действовать",
        "Живёт ли кто-то тут?"
    ]

    # Добавляем num_messages записей
    for _ in range(num_messages):
        username = random_username()
        message_text = random.choice(sample_texts)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('INSERT INTO messages (username, message_text, is_newbie, timestamp) VALUES (?, ?, ?, ?)',
                  (username, message_text, 1, timestamp))

    conn.commit()
    conn.close()
    print(f"База успешно создана и заполнена {num_messages} сообщениями!")

# Вызов функции
if __name__ == "__main__":
    init_and_fill_db()
