
import asyncio
import json
from aiogram import Bot, Dispatcher
from aiogram.exceptions import TelegramForbiddenError
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.base import StorageKey
from states import Form
import app.models as db
from app.handlers import router

async def main():
    try:
        with open('Token.json', 'r', encoding='utf-8') as file:
            TOKEN = json.load(file)['token']
    except FileNotFoundError:
        raise Exception("Файл с токеном не существует")

    bot = Bot(token=TOKEN)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(router)

    await db.connection_start()

    users = await db.get_all_users()

    for user_id in users:
        try:
            new_user_storage_key = StorageKey(chat_id=user_id, user_id=user_id, bot_id=bot.id)
            new_user_context = FSMContext(storage=storage, key=new_user_storage_key)
            await new_user_context.set_state(Form.message)

        except TelegramForbiddenError:
            await db.unsubscribe(user_id)

    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"Конец работы программы: {e}")
