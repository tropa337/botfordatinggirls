import random
import sqlite3

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

from dataBase.db import (DB_NAME, disable_profile, enable_profile,
                         get_active_profiles, get_profile, is_mutual_like,
                         like_profile, set_mutual_like)
from keyboards.default import delete_menu_kb, search_menu_kb, sleep_menu_kb

router = Router()
last_candidates = {}
in_search = set()


# Кнопка переходу у TG 
def open_tg_profile_kb(username):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔗 Відкрити профіль у Telegram", url=f"https://t.me/{username}")
    return kb.as_markup()


# Перевірка, чи вже лайкав користувач 
def has_liked(user_id, liked_user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM likes WHERE user_id=? AND liked_user_id=?",
        (user_id, liked_user_id),
    )
    result = cursor.fetchone()
    conn.close()
    return result is not None


#  ПОЧАТОК ПОШУКУ 
@router.message(lambda msg: msg.text in ["🔍 Почати пошук", "1🚀"])
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    enable_profile(user_id)
    in_search.add(user_id)

    # Отримуємо мій профіль, щоб знати кого шукати
    my_profile = get_profile(user_id)
    if not my_profile:
        await message.answer("⚠️ Спочатку створи свою анкету.")
        return

    (
        _,
        my_name,
        my_age,
        my_gender,
        my_looking_for,
        my_faculty,
        my_specialty,
        my_accessibility,
        my_course,
        my_bio,
        my_photo,
        _,
    ) = my_profile

    # Отримуємо список активних профілів, яких ще не лайкав
    candidates = get_active_profiles(exclude_user_id=user_id)
    profiles = []

    for p in candidates:
        candidate_id, name, age, gender, looking_for, faculty, specialty, accessibility, course, bio, photo_id, active = p
        if has_liked(user_id, candidate_id):
            continue  # пропускаємо вже лайкнуті анкети

        # Фільтруємо за бажаною статтю
        if my_looking_for == "Усі":
            profiles.append(p)
        elif my_looking_for == "Чоловіків" and gender == "Чоловік":
            profiles.append(p)
        elif my_looking_for == "Жінок" and gender == "Жінка":
            profiles.append(p)

    if not profiles:
        await message.answer("😕 Немає нових анкет, які відповідають твоїм критеріям.")
        return

    # Випадковий кандидат
    candidate = random.choice(profiles)
    (
        candidate_id,
        name,
        age,
        gender,
        looking_for,
        faculty,
        specialty,
        accessibility,
        course,
        bio,
        photo_id,
        active,
    ) = candidate

    last_candidates[user_id] = candidate_id

    caption = (
        f"👤 {name}, {age} років\n"
        f"🏫 Факультет: {faculty}\n"
        f"📘 Спеціальність: {specialty}\n"
        f"📊 Доступність: {accessibility}/10\n"
        f"🧭 Курс: {course}\n\n"
        f"{bio}"
    )

    if not photo_id:
        await message.answer("❌ Цей користувач не додав фото")
        return

    await message.answer_photo(
        photo=photo_id,
        caption=caption,
        reply_markup=search_menu_kb(),
    )

#  ЛАЙК 
@router.message(lambda msg: msg.text == "❤️")
async def like_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id not in in_search:
        await message.answer("⚠️ Почни пошук, щоб ставити лайки. Натисни '🔍 Почати пошук'")
        return

    candidate_id = last_candidates.get(user_id)
    if not candidate_id:
        await message.answer("⚠️ Спочатку почни пошук (1🚀).")
        return

    if has_liked(user_id, candidate_id):
        await message.answer("❤️ Ти вже лайкав цього користувача 😉")
        await show_profile(message)
        return

    like_profile(user_id, candidate_id)

    # Перевіряємо, чи це взаємний лайк
    if is_mutual_like(user_id, candidate_id):
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT accepted FROM likes WHERE user_id=? AND liked_user_id=?",
            (user_id, candidate_id),
        )
        accepted = cursor.fetchone()
        conn.close()

        # Якщо вже є метч — не дублюємо повідомлення
        if accepted and accepted[0] == 1:
            await message.answer("💞 Ви вже маєте метч із цим користувачем!")
            await show_profile(message)
            return

        set_mutual_like(user_id, candidate_id)

        candidate = get_profile(candidate_id)
        if candidate:
            _, name, age, gender, looking_for, faculty, specialty, accessibility, course, bio, photo_id, _ = candidate
            candidate_user = await message.bot.get_chat(candidate_id)

            if candidate_user.username:
                username_link = candidate_user.username
                kb = open_tg_profile_kb(username_link)

                await message.answer_photo(
                    photo=photo_id,
                    caption=f"🎉 У вас взаємний лайк із {name}! 💕\n"
                            f"Натисни нижче, щоб перейти у Telegram 👇",
                    reply_markup=kb,
                )

                try:
                    user_info = await message.bot.get_chat(user_id)
                    if user_info.username:
                        await message.bot.send_message(
                            chat_id=candidate_id,
                            text=f"💌 У тебе взаємний лайк із @{user_info.username}! "
                                 f"Натисни нижче, щоб написати 👇",
                            reply_markup=open_tg_profile_kb(user_info.username),
                        )
                except Exception:
                    pass
            else:
                await message.answer(
                    "🎉 У вас взаємний лайк, але користувач не має @username 😔",
                    reply_markup=sleep_menu_kb(),
                )
    else:
        await message.answer("❤️ Лайк додано! Очікуємо на взаємність 😉")
        await show_profile(message)


#  ДИЗЛАЙК 
@router.message(lambda msg: msg.text == "❌")
async def dislike_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id not in in_search:
        await message.answer("⚠️ Цю кнопку можна використовувати лише під час пошуку анкет.")
        return

    await message.answer("❌ Пропущено анкету.")
    await show_profile(message)


#  МЕНЮ СНУ 
@router.message(lambda msg: msg.text == "😴")
async def sleep_menu_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id in in_search:
        in_search.remove(user_id)

    await message.answer(
        "😴 Меню:\n"
        "1. Дивитися анкети\n"
        "2. Моя анкета\n"
        "3. Я більше не хочу нікого шукати\n"
        "4. Редагувати анкету\n",
        reply_markup=sleep_menu_kb(),
    )

#  ОБРОБКА ВИБОРУ ПОЧАТКУ ЧАТУ  
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

#  МОЯ АНКЕТА 
@router.message(lambda msg: msg.text == "2")
async def my_profile(message: types.Message):
    user = get_profile(message.from_user.id)
    if not user:
        await message.answer("😕 Ти ще не зареєстрований. Напиши /start")
        return

    (
        user_id,
        name,
        age,
        gender,
        looking_for,
        faculty,
        specialty,
        accessibility,
        course,
        bio,
        photo_id,
        active
    ) = user

    caption = (
        f"👤 {name}, {age} років\n"
        f"🧍 Стать: {gender}\n"
        f"🏫 Факультет: {faculty}\n"
        f"📘 Спеціальність: {specialty}\n"
        f"📊 Доступність: {accessibility}/10\n"
        f"🧭 Курс: {course}\n\n"
        f"{bio}"
    )

    await message.answer_photo(
        photo=photo_id,
        caption=caption,
        reply_markup=sleep_menu_kb()
    )

#  ВИДАЛЕННЯ / ВИМКНЕННЯ АНКЕТИ 
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

#  ПОВЕРНЕННЯ НАЗАД 
@router.message(lambda msg: msg.text == "Назад")
async def back(message: types.Message):
    await message.answer("🔙 Повернувся в меню", reply_markup=sleep_menu_kb())

