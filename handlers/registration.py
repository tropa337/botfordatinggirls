from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from dataBase.db import add_profile, get_profile, update_profile_field
from keyboards.default import main_menu_kb, switch_register_kb

router = Router()

# СТАНИ ДЛЯ FSM (реєстрації) 
class Registration(StatesGroup):
    name = State()
    age = State()
    gender = State()
    looking_for = State()
    faculty = State()
    specialty = State()
    accessibility = State()
    course = State()
    bio = State()
    photo = State()


#  СТАНИ ДЛЯ РЕДАГУВАННЯ 
class EditProfile(StatesGroup):
    field = State()
    new_value = State()


# СТАРТ РЕЄСТРАЦІЇ 
@router.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    existing_profile = get_profile(user_id)

    if existing_profile:
        await message.answer("👋 Ти вже зареєстрований!", reply_markup=main_menu_kb())
        return

    await state.set_state(Registration.name)
    await message.answer("👋 Привіт! Як тебе звати?")


# ІМ'Я 
@router.message(Registration.name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Registration.age)
    await message.answer("📅 Скільки тобі років?")


# ВІК 
@router.message(Registration.age)
async def reg_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Будь ласка, введи число 🙂")
        return
    await state.update_data(age=int(message.text))
    await state.set_state(Registration.gender)

    kb = ReplyKeyboardBuilder()
    kb.button(text="Чоловік")
    kb.button(text="Жінка")
    await message.answer("🧍 Обери свою стать:", reply_markup=kb.as_markup(resize_keyboard=True))


# СТАТЬ  
@router.message(Registration.gender)
async def reg_gender(message: types.Message, state: FSMContext):
    if message.text not in ["Чоловік", "Жінка"]:
        await message.answer("Оберіть зі списку 👇")
        return

    gender = message.text  # сохраняем как "Чоловік" или "Жінка"
    await state.update_data(gender=gender)
    await state.set_state(Registration.looking_for)

    kb = ReplyKeyboardBuilder()
    kb.button(text="Чоловіків")
    kb.button(text="Жінок")
    kb.button(text="Усі")  # убрали смайлик
    await message.answer("Кого хочеш бачити у пошуку?", reply_markup=kb.as_markup(resize_keyboard=True))


#  КОГО ШУКАЄШ  
@router.message(Registration.looking_for)
async def reg_looking_for(message: types.Message, state: FSMContext):
    valid = ["Чоловіків", "Жінок", "Усі"]
    if message.text not in valid:
        await message.answer("Оберіть зі списку 👇")
        return

    # Сохраняем нормализованное значение для поиска
    if message.text == "Чоловіків":
        looking_for = "Чоловіків"
    elif message.text == "Жінок":
        looking_for = "Жінок"
    else:
        looking_for = "Усі"

    await state.update_data(looking_for=looking_for)
    await state.set_state(Registration.faculty)
    await message.answer("🏫 Вкажи свій факультет:")


#  КОГО ШУКАЄШ 
@router.message(Registration.looking_for)
async def reg_looking_for(message: types.Message, state: FSMContext):
    valid = ["Чоловіків", "Жінок", "👥 Усіх"]
    if message.text not in valid:
        await message.answer("Оберіть зі списку 👇")
        return

    looking_for = message.text.replace("👨 ", "").replace("👩 ", "").replace("👥 ", "")
    await state.update_data(looking_for=looking_for)
    await state.set_state(Registration.faculty)
    await message.answer("🏫 Вкажи свій факультет:")


#  ФАКУЛЬТЕТ 
@router.message(Registration.faculty)
async def reg_faculty(message: types.Message, state: FSMContext):
    await state.update_data(faculty=message.text)
    await state.set_state(Registration.specialty)
    await message.answer("📘 Твоя спеціальність?")


#  СПЕЦІАЛЬНІСТЬ 
@router.message(Registration.specialty)
async def reg_specialty(message: types.Message, state: FSMContext):
    await state.update_data(specialty=message.text)
    await state.set_state(Registration.accessibility)
    await message.answer("🔥 Наскільки ти легкодоступний (1 – закритий, 10 – дуже відкритий)?")


# ЛЕГКОДОСТУПНІСТЬ 
@router.message(Registration.accessibility)
async def reg_accessibility(message: types.Message, state: FSMContext):
    if not message.text.isdigit() or not 1 <= int(message.text) <= 10:
        await message.answer("Введи число від 1 до 10 🙂")
        return
    await state.update_data(accessibility=int(message.text))
    await state.set_state(Registration.course)
    await message.answer("🎓 На якому ти курсі?")


# КУРС 
@router.message(Registration.course)
async def reg_course(message: types.Message, state: FSMContext):
    await state.update_data(course=message.text)
    await state.set_state(Registration.bio)
    await message.answer("✍️ Розкажи про себе (опис анкети):")


# ОПИС 
@router.message(Registration.bio)
async def reg_bio(message: types.Message, state: FSMContext):
    await state.update_data(bio=message.text)
    await state.set_state(Registration.photo)
    await message.answer("📸 Надішли фото для своєї анкети:")


# ФОТО 
@router.message(Registration.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("Будь ласка, надішли фото 📷")
        return

    data = await state.get_data()
    photo_id = message.photo[-1].file_id

    add_profile(
        message.from_user.id,
        data["name"],
        data["age"],
        data["gender"],
        data["looking_for"],
        data["faculty"],
        data["specialty"],
        data["accessibility"],
        data["course"],
        data["bio"],
        photo_id
    )

    await state.clear()
    await message.answer("✅ Анкету створено! Тепер можеш почати пошук 💬", reply_markup=main_menu_kb())

#  РЕДАГУВАННЯ АНКЕТИ 

@router.message(lambda msg: msg.text == "4🛠️")
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
        "5️⃣ Фото\n"
        "6️⃣ Стать\n"
        "7️⃣ Кого шукаєш\n\n"
        "Введи номер поля, яке хочеш оновити:",reply_markup=switch_register_kb()
    )

#  ВИБІР ПОЛЯ  
@router.message(EditProfile.field)
async def choose_field_to_edit(message: types.Message, state: FSMContext):
    mapping = {
        "1": "name",
        "2": "age",
        "3": "course",
        "4": "bio",
        "5": "photo_id",
        "6": "gender",
        "7": "looking_for"
    }

    choice = message.text.strip()
    if choice not in mapping:
        await message.answer("Будь ласка, введи число від 1 до 7 🙂")
        return

    field = mapping[choice]
    await state.update_data(field=field)
    await state.set_state(EditProfile.new_value)

    if field == "photo_id":
        await message.answer("📸 Надішли нове фото:")
    elif field == "gender":
        kb = ReplyKeyboardBuilder()
        kb.button(text="Чоловік")
        kb.button(text="Жінка")
        await message.answer("🧍 Обери свою стать:", reply_markup=kb.as_markup(resize_keyboard=True))
    elif field == "looking_for":
        kb = ReplyKeyboardBuilder()
        kb.button(text="Чоловіків")
        kb.button(text="Жінок")
        kb.button(text="Усі")
        await message.answer("Кого хочеш бачити у пошуку?", reply_markup=kb.as_markup(resize_keyboard=True))
    else:
        await message.answer("✍️ Введи нове значення:")

#  ОНОВЛЕННЯ ДАНИХ 
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
    elif field == "gender":
        if message.text not in ["Чоловік", "Жінка"]:
            await message.answer("Будь ласка, обери зі списку 👇")
            return
        new_value = message.text
    elif field == "looking_for":
        if message.text not in ["Чоловіків", "Жінок", "Усі"]:
            await message.answer("Будь ласка, обери зі списку 👇")
            return
        new_value = message.text
    else:
        new_value = message.text.strip()

    # 🔧 Оновлюємо поле в базі
    update_profile_field(user_id, field, new_value)
    await state.clear()

    await message.answer("✅ Дані оновлено!", reply_markup=main_menu_kb())
