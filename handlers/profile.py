import random

from aiogram import Router, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from dataBase.db import (disable_profile, get_active_profiles, get_profile,
                         like_profile)
from keyboards.default import delete_menu_kb, search_menu_kb, sleep_menu_kb

router = Router()

# ----------- МОЯ АНКЕТА -----------  
@router.message(lambda msg: msg.text == "2")
async def my_profile(message: types.Message):
    user = get_profile(message.from_user.id)
    if not user:
        await message.answer("😕 Ти ще не зареєстрований. Напиши /start")
        return

    user_id, name, age, course, bio, photo_id = user
    await message.answer_photo(
        photo=photo_id,
        caption=f"{name}, {age} років, {course} курс\n\n{bio}",
        reply_markup=sleep_menu_kb()
    )

# ----------- ВИДАЛЕННЯ / ВИМКНЕННЯ АНКЕТИ -----------  
@router.message(lambda msg: msg.text == "3")
async def delete_profile_menu(message: types.Message):
    await message.answer("⚠️ Хочеш вимкнути анкету?", reply_markup=delete_menu_kb())

@router.message(lambda msg: msg.text == "🚫 Вимкнути анкету")
async def disable_profile_handler(message: types.Message):
    disable_profile(message.from_user.id)
    await message.answer(
        "Анкету вимкнено 💤 Натисни 1🚀, щоб знову шукати 👇",
        reply_markup=sleep_menu_kb()
    )

# ----------- ПОВЕРНЕННЯ НАЗАД -----------  
@router.message(lambda msg: msg.text == "Назад")
async def back(message: types.Message):
    await message.answer("🔙 Повернувся в меню", reply_markup=sleep_menu_kb())

# ----------- МЕНЮ СНУ 😴 -----------  
@router.message(lambda msg: msg.text == "😴")
async def sleep_menu(message: types.Message):
    await message.answer(
        "😴 Меню:\n"
        "1. Дивитися анкети\n"
        "2. Моя анкета\n"
        "3. Я більше не хочу нікого шукати",
        reply_markup=sleep_menu_kb()
    )

# ----------- ПОШУК / АНКЕТИ -----------  
@router.message(lambda msg: msg.text in ["🔍 Почати пошук", "1🚀"])
async def show_random_profile(message: types.Message):
    candidates = get_active_profiles(exclude_user_id=message.from_user.id)
    if not candidates:
        await message.answer("😕 Немає доступних анкет.")
        return

    candidate = random.choice(candidates)
    user_id, name, age, course, bio, photo_id = candidate
    await message.answer_photo(
        photo=photo_id,
        caption=f"Знайомся: {name}\n\n{bio}",
        reply_markup=search_menu_kb()
    )

# ----------- ЛАЙК / ДИЗЛАЙК -----------  
@router.message(lambda msg: msg.text == "❤️")
async def like_profile_handler(message: types.Message):
    candidates = get_active_profiles(exclude_user_id=message.from_user.id)
    if not candidates:
        await message.answer("😕 Немає доступних анкет.")
        return

    candidate = random.choice(candidates)
    like_profile(message.from_user.id, candidate[0])
    await message.answer("❤️ Ти лайкнув анкету!")
    await show_random_profile(message)

@router.message(lambda msg: msg.text == "❌")
async def dislike_profile_handler(message: types.Message):
    await message.answer("❌ Пропустив анкету")
    await show_random_profile(message)



def start_chat_kb(user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Почати спілкування", callback_data=f"accept_chat_{user_id}"),
            InlineKeyboardButton(text="❌ Ні, дякую", callback_data=f"decline_chat_{user_id}")
        ]
    ])
