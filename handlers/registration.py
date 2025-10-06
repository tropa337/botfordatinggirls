from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from dataBase.db import add_profile, get_profile, update_profile_field
from keyboards.default import main_menu_kb

router = Router()

# ----------- СТАНИ ДЛЯ FSM (реєстрації) -----------
class Registration(StatesGroup):
    name = State()
    age = State()
    course = State()
    bio = State()
    photo = State()

# ----------- СТАНИ ДЛЯ РЕДАГУВАННЯ -----------
class EditProfile(StatesGroup):
    field = State()
    new_value = State()

# ----------- СТАРТ РЕЄСТРАЦІЇ -----------
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id

    # 🟢 Перевірка: якщо профіль уже є в базі — не запускаємо реєстрацію
    existing_profile = get_profile(user_id)
    if existing_profile:
        await message.answer(
            "👋 Ти вже зареєстрований!\nМожеш користуватись меню нижче:",
            reply_markup=main_menu_kb()
        )
        return

    # 🔵 Якщо профілю нема — запускаємо реєстрацію
    await state.set_state(Registration.name)
    await message.answer("👋 Привіт! Давай зареєструємо твою анкету.\nЯк тебе звати?")

# ----------- ІМ'Я -----------
@router.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.age)
    await message.answer("📅 Скільки тобі років?")

# ----------- ВІК -----------
@router.message(Registration.age)
async def reg_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введи число 🙂")
        return
    await state.update_data(age=int(message.text))
    await state.set_state(Registration.course)
    await message.answer("🎓 На якому ти курсі?")

# ----------- КУРС -----------
@router.message(Registration.course)
async def reg_course(message: types.Message, state: FSMContext):
    await state.update_data(course=message.text)
    await state.set_state(Registration.bio)
    await message.answer("✍️ Розкажи про себе (опис анкети):")

# ----------- ОПИС -----------
@router.message(Registration.bio)
async def reg_bio(message: types.Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await state.set_state(Registration.photo)
    await message.answer("📸 Надішли фото для своєї анкети:")

# ----------- ФОТО -----------
@router.message(Registration.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("Будь ласка, надішли фото 📷")
        return

    data = await state.get_data()
    photo_id = message.photo[-1].file_id

    # ---------- ДОБАВЛЯЄМО АНКЕТУ В БАЗУ ----------
    add_profile(
        user_id=message.from_user.id,
        name=data["name"],
        age=data["age"],
        course=data["course"],
        bio=data["bio"],
        photo_id=photo_id
    )

    await state.clear()

    # ---------- ПОВЕРТАЄМО ДО ГОЛОВНОГО МЕНЮ ----------
    await message.answer(
        "✅ Анкету створено!\nТепер ти можеш почати пошук 💬",
        reply_markup=main_menu_kb()
    )


# ======================= 🛠️ РЕДАГУВАННЯ АНКЕТИ =======================

@router.message(lambda msg: msg.text == "4")
async def edit_profile_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    profile = get_profile(user_id)

    if not profile:
        await message.answer("😕 У тебе ще немає анкети. Спочатку зареєструйся командою /start.")
        return

    await state.set_state(EditProfile.field)
    await message.answer(
        "Що хочеш змінити?\n\n"
        "1️⃣ Ім’я\n"
        "2️⃣ Вік\n"
        "3️⃣ Курс\n"
        "4️⃣ Опис\n"
        "5️⃣ Фото\n\n"
        "Введи номер поля, яке хочеш оновити:"
    )

# ----------- ВИБІР ПОЛЯ -----------
@router.message(EditProfile.field)
async def choose_field_to_edit(message: types.Message, state: FSMContext):
    mapping = {
        "1": "name",
        "2": "age",
        "3": "course",
        "4": "bio",
        "5": "photo_id"
    }

    choice = message.text.strip()
    if choice not in mapping:
        await message.answer("Будь ласка, введи число від 1 до 5 🙂")
        return

    field = mapping[choice]
    await state.update_data(field=field)
    await state.set_state(EditProfile.new_value)

    if field == "photo_id":
        await message.answer("📸 Надішли нове фото:")
    else:
        await message.answer("✍️ Введи нове значення:")

# ----------- ОНОВЛЕННЯ ДАНИХ -----------
@router.message(EditProfile.new_value)
async def update_profile_value(message: types.Message, state: FSMContext):
    data = await state.get_data()
    field = data["field"]
    user_id = message.from_user.id

    if field == "photo_id":
        if not message.photo:
            await message.answer("Будь ласка, надішли фото 📷")
            return
        new_value = message.photo[-1].file_id
    else:
        new_value = message.text.strip()

    # 🔧 Оновлюємо поле в базі
    update_profile_field(user_id, field, new_value)
    await state.clear()

    await message.answer("✅ Дані оновлено!", reply_markup=main_menu_kb())
