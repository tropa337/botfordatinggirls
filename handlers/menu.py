import random

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from dataBase.db import (get_active_profiles, get_profile, is_mutual_like,
                         like_profile, set_mutual_like)
from keyboards.default import search_menu_kb, sleep_menu_kb

router = Router()

# 🔹 Глобальний словник для збереження останніх анкет
last_candidates = {}

# --- Функція для створення кнопок при матчі ---
def match_kb(user_id):
    kb = InlineKeyboardBuilder()
    kb.button(text="💬 Почати спілкування", callback_data=f"chat:{user_id}")
    kb.button(text="❌ Не зараз", callback_data="skip")
    kb.adjust(1)
    return kb.as_markup()


# ----------- ПОКАЗ ПРОФІЛЮ / ПОШУК -----------  
@router.message(lambda msg: msg.text in ["🔍 Почати пошук", "❤️", "❌", "1🚀"])
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    profiles = get_active_profiles(exclude_user_id=user_id)

    if not profiles:
        await message.answer("😕 Поки що немає інших анкет для перегляду.")
        return

    candidate = random.choice(profiles)
    candidate_id, name, age, course, bio, photo_id, _ = candidate

    # 🔹 Записуємо останню анкету для користувача
    last_candidates[user_id] = candidate_id

    await message.answer_photo(
        photo=photo_id,
        caption=f"Знайомся: {name}, {age} років, {course} курс\n\n{bio}",
        reply_markup=search_menu_kb()
    )


# ----------- ЛАЙК -----------  
@router.message(lambda msg: msg.text == "❤️")
async def like_handler(message: types.Message):
    user_id = message.from_user.id
    candidate_id = last_candidates.get(user_id)

    if not candidate_id:
        await message.answer("⚠️ Спочатку почни пошук (1🚀).")
        return

    like_profile(user_id, candidate_id)

    if is_mutual_like(user_id, candidate_id):
        set_mutual_like(user_id, candidate_id)
        candidate = get_profile(candidate_id)
        if candidate:
            _, name, age, course, bio, photo_id = candidate

            await message.answer_photo(
                photo=photo_id,
                caption=f"🎉 У вас взаємний лайк із {name}! 💕",
                reply_markup=match_kb(candidate_id)
            )

            try:
                await message.bot.send_message(
                    chat_id=candidate_id,
                    text=f"💌 {message.from_user.first_name} також лайкнув(-ла) тебе! "
                         "Хочеш почати спілкування?",
                    reply_markup=match_kb(user_id)
                )
            except Exception:
                pass
    else:
        await message.answer("❤️ Лайк додано! Очікуємо на взаємність 😉")
        await show_profile(message)


# ----------- ДИЗЛАЙК -----------  
@router.message(lambda msg: msg.text == "❌")
async def dislike_handler(message: types.Message):
    await message.answer("❌ Пропустив анкету")
    await show_profile(message)


# ----------- МЕНЮ СНУ 😴 -----------  
@router.message(lambda msg: msg.text == "😴")
async def sleep_menu_handler(message: types.Message):
    await message.answer(
        "😴 Меню:\n"
        "1. Дивитися анкети\n"
        "2. Моя анкета\n"
        "3. Я більше не хочу нікого шукати"
        "4. Редагувати анкету\n",
        reply_markup=sleep_menu_kb()
    )


# ----------- ОБРОБКА ВИБОРУ ПОЧАТКУ ЧАТУ -----------  
@router.callback_query(lambda c: c.data.startswith("chat:"))
async def start_chat(callback: types.CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    target_profile = get_profile(target_id)

    if not target_profile:
        await callback.message.answer("⚠️ Користувач недоступний.")
        return

    _, name, age, course, bio, photo_id = target_profile
    await callback.message.answer_photo(
        photo=photo_id,
        caption=f"💬 Ти почав(-ла) спілкування з {name}!"
    )
    await callback.answer("Чат відкрито!")
