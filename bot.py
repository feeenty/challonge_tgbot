import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv
from chyllonge.api import ChallongeApi

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHALLONGE_USER = os.getenv("CHALLONGE_USER")
CHALLONGE_KEY = os.getenv("CHALLONGE_KEY")

api = ChallongeApi()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Привет!")


@dp.message(Command("create_tournament"))
async def create_tournament(msg: types.Message):
    tournament = api.tournaments.create(name="T1", tournament_type="single elimination")
    tournament_url = tournament["full_challonge_url"]
    await msg.answer(f"{tournament_url}")


@dp.message(Command("tournaments"))
async def tournaments(msg: types.Message):
    tournaments_data = api.tournaments.get_all()
    for tournament in tournaments_data:
        state = tournament['state']
        status = None
        if state == "pending":
            status = "⏳Ожидает запуска"
        elif state == "underway":
            status = "🔄В процессе"
        elif state == "complete":
            status = "🏁Завершён"
        await msg.answer(f"**{tournament.name}**\n"
                         f"Статус - {status}\n"
                         f"[Ссылка]({tournament.full_challonge_url})")


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
