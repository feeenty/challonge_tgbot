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

user_state = {}


def tournament_create_control_buttons(tournament_id):
    buttons = [
        [InlineKeyboardButton(text="Запустить турнир", callback_data=f"start_tournament_{tournament_id}")],
        [InlineKeyboardButton(text="Добавить участника", callback_data=f"add_player_{tournament_id}")],
        [InlineKeyboardButton(text="Настройки", callback_data=f"settings_{tournament_id}")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def add_player_buttons(tournament_id):
    buttons = [
        [InlineKeyboardButton(text="Добавить ещё", callback_data=f"add_more_{tournament_id}")],
        [InlineKeyboardButton(text="Закончить", callback_data=f"finish_adding_{tournament_id}")]
    ]

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@dp.message(Command("create_tournament"))
async def create_tournament(msg: types.Message):
    user_id = msg.from_user.id
    user_state[user_id] = "tournament_name"

    await msg.answer("Введите название турнира")


@dp.message()
async def handler(msg: types.Message):
    user_id = msg.from_user.id

    if user_id not in user_state:
        return

    if user_state[user_id] == "tournament_name":
        tournament_name = msg.text

        if len(tournament_name) > 60:
            await msg.answer("Название слишком длинное (максимум 60 символов)")
            return

        tournament = api.tournaments.create(
            name=tournament_name,
            tournament_type="single elimination"
        )

        tournament_id = tournament["id"]

        await msg.answer(f"Турнир [{tournament_name}]({tournament['full_challonge_url']}) успешно создан",
                         parse_mode="Markdown",
                         reply_markup=tournament_create_control_buttons(tournament_id))

        del user_state[user_id]

    elif user_state[user_id]["action"] == "nickname":
        nickname = msg.text
        tournament_id = user_state[user_id]["tournament_id"]

        participants = api.participants.get_all(tournament_id)
        participant_exists = False

        for p in participants:
            exits_nickname = p["participant"]["name"]
            if exits_nickname.lower() == nickname.lower():
                participant_exists = True
                break

        if participant_exists:
            await msg.answer(f"Участник с ником {nickname} уже есть в списках")
            return

        api.participants.add(tournament_id, name=nickname)

        await msg.answer(f"{nickname} добавлен, хотите добавить ещё участника?",
                         reply_markup=add_player_buttons(tournament_id))
        del user_state[user_id]


@dp.callback_query(F.data.startswith("add_player_"))
async def add_player(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    tournament_id = callback.data.split("_")[2]

    user_state[user_id] = {"action": "nickname", "tournament_id": tournament_id}

    await callback.message.answer("Введите ник участника")
    await callback.answer()


@dp.callback_query(F.data.startswith("add_more_"))
async def add_more(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    tournament_id = callback.data.split("_")[2]

    user_state[user_id] = {"action": "nickname", "tournament_id": tournament_id}

    await callback.message.answer("Введите имя следующего участника")
    await callback.answer()


@dp.callback_query(F.data.startswith("finish_adding_"))
async def finish_adding(callback: types.CallbackQuery):
    tournament_id = callback.data.split("_")[2]

    await callback.message.edit_text("Добавление участников завершено",
                                     reply_markup=tournament_create_control_buttons(tournament_id))


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
