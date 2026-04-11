import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram import F
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
from chyllonge.api import ChallongeApi

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHALLONGE_USER = os.getenv("CHALLONGE_USER")
CHALLONGE_KEY = os.getenv("CHALLONGE_KEY")

api = ChallongeApi()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def create_button():
    buttons = [[InlineKeyboardButton(text="Создать турнир", callback_data="create_tournament")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(Command("create_tournament"))
async def create_tournament(msg: types.Message):
    await msg.answer("Создание турнира", reply_markup=create_button())


@dp.callback_query(F.data == "create_tournament")
async def on_create(callback: types.CallbackQuery):
    await callback.answer()

    tournament = api.tournaments.create(
        name="TP1",
        tournament_type="single elimination"
    )

    await callback.message.edit_text(
        f"Турнир [ТР1]({tournament["full_challonge_url"]}) создан",
        parse_mode="Markdown"
    )


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
        await msg.answer(f"[{tournament['name']}]({tournament['full_challonge_url']})\n"
                         f"Статус - {status}\n",
                         parse_mode="Markdown")


async def main():
    print("Бот запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
