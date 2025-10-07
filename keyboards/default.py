from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


# --- Головне меню ---
def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Почати пошук")]
        ],
        resize_keyboard=True
    )

# --- Меню пошуку (лайк / дизлайк / сон) ---
def search_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="❤️"), KeyboardButton(text="❌"), KeyboardButton(text="😴")]
        ],
        resize_keyboard=True
    )

def switch_register_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1"), KeyboardButton(text="2"), KeyboardButton(text="3"),KeyboardButton(text="4"),KeyboardButton(text="5"), KeyboardButton(text="6"), KeyboardButton(text="7")]
        ],
        resize_keyboard=True
    )

# --- Меню сну ---
def sleep_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="1🚀"), KeyboardButton(text="2"), KeyboardButton(text="3"),KeyboardButton(text="4🛠️")]
        ],
        resize_keyboard=True
    )

# --- Меню видалення ---
def delete_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Назад")],
            [KeyboardButton(text="🚫 Вимкнути анкету")]
        ],
        resize_keyboard=True
    )
