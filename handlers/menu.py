import random

from aiogram import Router, types
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Імпорт функцій з твоєї бази даних PostgreSQL
from dataBase.db import has_liked  # Додамо цю функцію в db.py
from dataBase.db import (disable_profile, enable_profile, get_active_profiles,
                         get_profile, is_mutual_like, like_profile,
                         set_mutual_like)
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
    """Функція для перевірки лайків (додай її в db.py)"""
    from dataBase.db import get_connection
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT 1 FROM likes WHERE user_id = %s AND liked_user_id = %s",
                (user_id, liked_user_id)
            )
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        print(f"Помилка перевірки лайка: {e}")
        return False
    finally:
        conn.close()


# ПОЧАТОК ПОШУКУ 
@router.message(lambda msg: msg.text in ["🔍 Почати пошук", "1🚀"])
async def show_profile(message: types.Message):
    try:
        user_id = message.from_user.id
        print(f"🟢 Початок пошуку для user_id: {user_id}")
        
        enable_profile(user_id)
        in_search.add(user_id)

        # Отримуємо мій профіль
        my_profile = get_profile(user_id)
        if not my_profile:
            await message.answer("⚠️ Спочатку створи свою анкету.")
            return

        print(f"🔍 Мій профіль: {my_profile}")
        
        # Отримуємо список активних профілів
        candidates = get_active_profiles(exclude_user_id=user_id)
        print(f"🔍 Знайдено кандидатів: {len(candidates)}")
        
        # Виводимо інформацію про кандидатів для дебагу
        for i, candidate in enumerate(candidates):
            print(f"🔍 Кандидат {i+1}: {candidate.get('name')}, {candidate.get('gender')}, ID: {candidate.get('user_id')}")
        
        profiles = []
        my_looking_for = my_profile.get('looking_for', 'Усі')
        print(f"🔍 Я шукаю: '{my_looking_for}'")

        for candidate in candidates:
            candidate_id = candidate['user_id']
            candidate_gender = candidate.get('gender', '')
            candidate_name = candidate.get('name', '')
            
            print(f"🔍 Перевіряємо кандидата: {candidate_name} ({candidate_gender})")

            # Перевіряємо чи вже лайкали
            if has_liked(user_id, candidate_id):
                print(f"⏩ Пропускаємо вже лайкнутого: {candidate_id}")
                continue

            # Фільтруємо за бажаною статтю
            if my_looking_for.lower() == "усі":
                profiles.append(candidate)
                print(f"✅ Додано кандидата {candidate_name} (всі)")
            elif my_looking_for.lower() == "чоловіків" and candidate_gender.lower() == "чоловік":
                profiles.append(candidate)
                print(f"✅ Додано кандидата {candidate_name} (чоловік)")
            elif my_looking_for.lower() == "жінок" and candidate_gender.lower() == "жінка":
                profiles.append(candidate)
                print(f"✅ Додано кандидата {candidate_name} (жінка)")
            else:
                print(f"❌ Не підходить по фільтру: {candidate_gender} != {my_looking_for}")

        print(f"🔍 Після фільтрації залишилось: {len(profiles)}")

        if not profiles:
            await message.answer("😕 Немає нових анкет, які відповідають твоїм критеріям.")
            return

        # Вибираємо випадкового кандидата
        candidate = random.choice(profiles)
        candidate_id = candidate['user_id']
        last_candidates[user_id] = candidate_id
        
        print(f"🎯 Обрано кандидата: {candidate['name']} (ID: {candidate_id})")
        print(f"📸 Photo ID кандидата: {candidate.get('photo_id')}")

        # Формуємо опис
        caption = (
            f"👤 {candidate['name']}, {candidate['age']} років\n"
            f"🏫 Факультет: {candidate.get('faculty', 'Не вказано')}\n"
            f"📘 Спеціальність: {candidate.get('specialty', 'Не вказано')}\n"
            f"📊 Доступність: {candidate.get('accessibility', 'Не вказано')}/10\n"
            f"🧭 Курс: {candidate.get('course', 'Не вказано')}\n\n"
            f"{candidate.get('bio', 'Опис відсутній')}"
        )

        photo_id = candidate.get('photo_id')
        print(f"🔍 Photo ID для відправки: {photo_id}")
        
        if not photo_id:
            await message.answer("❌ Цей користувач не додав фото")
            return

        # Спроба відправити фото
        try:
            await message.answer_photo(
                photo=photo_id,
                caption=caption,
                reply_markup=search_menu_kb(),
            )
            print("✅ Анкету успішно показано")
        except Exception as e:
            print(f"❌ Помилка при відправці фото: {e}")
            await message.answer(f"❌ Помилка при завантаженні анкети: {e}")

    except Exception as e:
        print(f"❌ Критична помилка в show_profile: {e}")
        import traceback
        traceback.print_exc()
        await message.answer("❌ Сталася помилка при пошуку. Спробуй ще раз.")
# ЛАЙК 
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
        # Для PostgreSQL нам не потрібно перевіряти accepted окремо
        # тому що set_mutual_like вже оновлює обидва записи
        
        set_mutual_like(user_id, candidate_id)

        candidate = get_profile(candidate_id)
        if candidate:
            candidate_user = await message.bot.get_chat(candidate_id)

            if candidate_user.username:
                kb = open_tg_profile_kb(candidate_user.username)

                await message.answer_photo(
                    photo=candidate['photo_id'],
                    caption=f"🎉 У вас взаємний лайк із {candidate['name']}! 💕\n"
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
                except Exception as e:
                    print(f"Помилка відправки повідомлення про метч: {e}")
            else:
                await message.answer(
                    "🎉 У вас взаємний лайк, але користувач не має @username 😔",
                    reply_markup=sleep_menu_kb(),
                )
    else:
        await message.answer("❤️ Лайк додано! Очікуємо на взаємність 😉")
        await show_profile(message)


# ДИЗЛАЙК 
@router.message(lambda msg: msg.text == "❌")
async def dislike_handler(message: types.Message):
    user_id = message.from_user.id

    if user_id not in in_search:
        await message.answer("⚠️ Цю кнопку можна використовувати лише під час пошуку анкет.")
        return

    await message.answer("❌ Пропущено анкету.")
    await show_profile(message)


# МЕНЮ СНУ 
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


# ОБРОБКА ВИБОРУ ПОЧАТКУ ЧАТУ  
@router.callback_query(lambda c: c.data.startswith("chat:"))
async def start_chat(callback: types.CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    target_profile = get_profile(target_id)

    if not target_profile:
        await callback.message.answer("⚠️ Користувач недоступний.")
        return

    await callback.message.answer_photo(
        photo=target_profile['photo_id'],
        caption=f"💬 Ти почав(-ла) спілкування з {target_profile['name']}!"
    )
    await callback.answer("Чат відкрито!")


# МОЯ АНКЕТА 
@router.message(lambda msg: msg.text == "2")
async def my_profile(message: types.Message):
    user = get_profile(message.from_user.id)
    if not user:
        await message.answer("😕 Ти ще не зареєстрований. Напиши /start")
        return

    caption = (
        f"👤 {user['name']}, {user['age']} років\n"
        f"🧍 Стать: {user['gender']}\n"
        f"🏫 Факультет: {user['faculty']}\n"
        f"📘 Спеціальність: {user['specialty']}\n"
        f"📊 Доступність: {user['accessibility']}/10\n"
        f"🧭 Курс: {user['course']}\n\n"
        f"{user['bio']}"
    )

    await message.answer_photo(
        photo=user['photo_id'],
        caption=caption,
        reply_markup=sleep_menu_kb()
    )


# ВИДАЛЕННЯ / ВИМКНЕННЯ АНКЕТИ 
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


# ПОВЕРНЕННЯ НАЗАД 
@router.message(lambda msg: msg.text == "Назад")
async def back(message: types.Message):
    await message.answer("🔙 Повернувся в меню", reply_markup=sleep_menu_kb())