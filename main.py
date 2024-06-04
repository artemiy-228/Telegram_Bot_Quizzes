import asyncio
import json
from aiogram import Bot, Dispatcher
from app import models as db
from app.handlers import router

async def main():
    try:
        with open('Token.json', 'r', encoding='utf-8') as file:
             TOKEN = json.load(file)['token']
    except:
        raise "Token's file doesn't exist"


    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.include_router(router)

    await db.connection_start()
    await dp.start_polling(bot)

    router.process_name.func.__annotations__['bot'] = Bot


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        print("Конец работы программы")