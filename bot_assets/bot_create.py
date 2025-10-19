from aiogram import Bot
from aiogram.dispatcher.dispatcher import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
import asyncio

from .handlers import start
from utils import fetch_regions
from configuration.config import TOKEN


def _init_routers(dp: Dispatcher):
    dp.include_router(start.router)

async def main():
    storage = MemoryStorage()
    bot = Bot(token=TOKEN)
    dp = Dispatcher(bots=bot, storage=storage)

    _init_routers(dp)
    await fetch_regions()
    await dp.start_polling(bot)