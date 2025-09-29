import asyncio
import aiosqlite
from telethon import TelegramClient, events
from datetime import datetime
import logging

logging.basicConfig(filename='bot.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# -------------------- Константы --------------------
api_id = 26729995
api_hash = 'd1b11cf6d08a6bb02668ea88c1fba886'
session_name = 'userbot_session'

NEWBIE_KEYWORDS = [
    'новичок', 'начинающий', 'не понимаю', 'помогите',
    'помощь', 'вопрос', 'первый раз', 'фз'
]

EXPERIENCED_KEYWORDS = [
    'продам', 'куплю', 'анализ', 'стратегия', 'сигнал', 
    'портфель', 'индикатор', 'трейдю', 'шорчу', 'лонг', 'шорт',
    'маркетмейкер', 'арбитражу', 'профитнул', 'закрыл позицию', 'тф',
    "помогу"
]

# -------------------- Инициализация --------------------
client = TelegramClient(session_name, api_id, api_hash)

# -------------------- Работа с БД --------------------
async def init_db():
    async with aiosqlite.connect('chat_messagesq.db') as db:
        await db.execute('''CREATE TABLE IF NOT EXISTS messages (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE,
                            message_link TEXT,
                            is_newbie INTEGER,
                            timestamp TEXT,
                            del_id INTEGER UNIQUE
                            )''')
        await db.commit()
    logging.info("База данных инициализирована")


async def save_message(username, link, is_newbie):
    async with aiosqlite.connect('chat_messagesq.db') as db:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        del_id = abs(hash(username)) % (10**9)  # генерируем уникальный ID для удаления

        # вставка или обновление (чтобы один юзер = одна строка)
        await db.execute('''INSERT INTO messages (username, message_link, is_newbie, timestamp, del_id)
                            VALUES (?, ?, ?, ?, ?)
                            ON CONFLICT(username) DO UPDATE SET 
                                message_link=excluded.message_link,
                                is_newbie=excluded.is_newbie,
                                timestamp=excluded.timestamp,
                                del_id=excluded.del_id
                         ''',
                         (username, link, int(is_newbie), timestamp, del_id))
        await db.commit()


# -------------------- Фильтры --------------------
def is_newbie(text: str) -> bool:
    text = text.lower()
    return any(k in text for k in NEWBIE_KEYWORDS) and not any(k in text for k in EXPERIENCED_KEYWORDS)


# -------------------- Обработка сообщений --------------------
@client.on(events.NewMessage)
async def new_message_handler(event):
    try:
        sender = await event.get_sender()
        username = sender.username or f"id{sender.id}"
        text = event.message.message or ''
        link = f"https://t.me/c/{str(event.chat_id)[4:]}/{event.message.id}"

        if is_newbie(text):
            await save_message(username, link, True)
            logging.info(f"Новое сообщение сохранено/обновлено: {username} -> {link}")
    except Exception as e:
        logging.error(f"Ошибка обработки нового сообщения: {e}")


# -------------------- Обработка истории --------------------
async def process_history(dialog):
    try:
        async for message in client.iter_messages(dialog.id, limit=1000):
            sender = await message.get_sender()
            username = sender.username or f"id{sender.id}"
            link = f"https://t.me/c/{str(dialog.id)[4:]}/{message.id}"
            text = message.message or ''
            if is_newbie(text):
                await save_message(username, link, True)
    except Exception as e:
        logging.error(f"Ошибка при обработке истории чата {dialog.name}: {e}")


# -------------------- Обработка всех групп --------------------
async def process_all_groups():
    dialogs = await client.get_dialogs()
    tasks = []
    for dialog in dialogs:
        if dialog.is_group or dialog.is_channel:
            tasks.append(process_history(dialog))
    await asyncio.gather(*tasks)


# -------------------- Основная функция --------------------
async def main():
    await init_db()
    logging.info("Userbot запущен, обрабатывает историю и новые сообщения...")
    await process_all_groups()
    print("Userbot готов и сканирует новые сообщения...")
    await client.run_until_disconnected()


# -------------------- Запуск --------------------
if __name__ == '__main__':
    with client:
        client.loop.run_until_complete(main())
