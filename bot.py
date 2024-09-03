import os
import sqlite3
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from database import (
    create_db, add_or_update_user, get_user, get_all_users,
    add_like, check_match, add_viewed_profile, get_viewed_profiles,
    get_user_likes, set_user_like_status, add_match,
    get_user_profile, get_user_profile_photo, get_user_name,
    get_user_age, get_user_group, get_user_description,
    get_user_telegram_id
)

# Логирование
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
API_TOKEN = '7212146041:AAG_HSE8EDrRLprazJvMeQBW5fRVpjixQGE'  # Замените на ваш реальный токен
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

# Указание ID администратора
ADMIN_ID = 5066208897  # Замените на ваш ID

# Путь к базе данных
DB_PATH = 'database.db'

# Создание базы данных
create_db()

# Состояния для FSM (форм анкеты)
class Form(StatesGroup):
    name = State()
    age = State()
    student_group = State()
    description = State()
    photo = State()
    gender = State()
    telegram_id = State()

# Главное меню
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add(KeyboardButton("Моя анкета"), KeyboardButton("Смотреть анкеты"), KeyboardButton("Редактировать анкету"))

# Половые кнопки для выбора пола при создании и редактировании анкеты
gender_menu = ReplyKeyboardMarkup(resize_keyboard=True)
gender_menu.add(KeyboardButton("Мужской"), KeyboardButton("Женский"))

# Половые кнопки для выбора пола при поиске анкет
search_gender_menu = ReplyKeyboardMarkup(resize_keyboard=True)
search_gender_menu.add(KeyboardButton("Мужской"), KeyboardButton("Женский"), KeyboardButton("Неважно"))

# Команда /start
@dp.message_handler(commands='start')
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        await message.answer("Вы уже зарегистрированы! Введите /menu для просмотра анкет.", reply_markup=main_menu)
    else:
        await message.answer("Добро пожаловать в бот знакомств! Для начала создайте анкету. Введите своё имя:")
        await Form.name.set()

# Получение имени
@dp.message_handler(state=Form.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш возраст:")
    await Form.next()

# Получение возраста
@dp.message_handler(state=Form.age)
async def process_age(message: types.Message, state: FSMContext):
    age = message.text.strip()
    if not age.isdigit():
        await message.answer("Возраст должен быть числом. Пожалуйста, введите возраст снова:")
        return
    await state.update_data(age=int(age))
    await message.answer("Введите вашу группу в колледже:")
    await Form.next()

# Получение группы
@dp.message_handler(state=Form.student_group)
async def process_group(message: types.Message, state: FSMContext):
    await state.update_data(student_group=message.text.strip())
    await message.answer("Введите описание себя:")
    await Form.next()

# Получение описания
@dp.message_handler(state=Form.description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("Отправьте ваше фото.")
    await Form.next()

# Получение фото
@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=Form.photo)
async def process_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    file_info = await bot.get_file(photo_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)
    
    if not os.path.exists('photos'):
        os.makedirs('photos')
    
    photo_path = f"photos/{message.from_user.id}.jpg"
    with open(photo_path, 'wb') as new_file:
        new_file.write(file.read())

    await state.update_data(photo_path=photo_path)
    await message.answer("Выберите ваш пол:", reply_markup=gender_menu)
    await Form.next()

# Получение пола
@dp.message_handler(state=Form.gender)
async def process_gender(message: types.Message, state: FSMContext):
    gender = message.text.strip()
    if gender not in ["Мужской", "Женский"]:
        await message.answer("Пожалуйста, выберите правильный пол.")
        return
    
    await state.update_data(gender=gender)
    await message.answer("Введите ваш Telegram ID (например, @username):")
    await Form.next()

# Получение Telegram ID
@dp.message_handler(state=Form.telegram_id)
async def process_telegram_id(message: types.Message, state: FSMContext):
    telegram_id = message.text.strip()
    if not telegram_id.startswith('@'):
        await message.answer("Telegram ID должен начинаться с символа '@'. Пожалуйста, введите снова:")
        return
    
    user_data = await state.get_data()

    try:
        add_or_update_user(
            message.from_user.id,
            user_data['name'],
            user_data['age'],
            user_data['student_group'],
            user_data['description'],
            user_data['photo_path'],
            telegram_id,
            user_data['gender']
        )
        await message.answer("Ваша анкета успешно сохранена!", reply_markup=main_menu)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных анкеты: {e}")
        await message.answer("Ошибка сохранения данных анкеты. Пожалуйста, вернитесь и попробуйте снова.")

    await state.finish()

# Команда /menu
@dp.message_handler(commands='menu')
async def cmd_menu(message: types.Message):
    await message.answer("Главное меню:", reply_markup=main_menu)

# Команда "Моя анкета"
@dp.message_handler(text="Моя анкета")
async def my_profile(message: types.Message):
    user = get_user(message.from_user.id)
    if user:
        user_id, name, age, student_group, description, photo_path, telegram_id, gender = user
        photo = open(photo_path, 'rb') if os.path.exists(photo_path) else None
        await bot.send_photo(message.chat.id, photo, caption=f"""
        Имя: {name}
        Возраст: {age}
        Группа: {student_group}
        Описание: {description}
        Пол: {gender}
        """)
    else:
        await message.answer("Ваша анкета не найдена. Пожалуйста, создайте анкету, используя команду /start.")

# Команда "Редактировать анкету"
@dp.message_handler(text="Редактировать анкету")
async def edit_profile(message: types.Message):
    await message.answer("Для редактирования анкеты отправьте новую информацию о себе. Введите ваше новое имя:")
    await Form.name.set()

# Обработка ввода нового значения для полей анкеты
@dp.message_handler(state=Form.name)
async def edit_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Введите ваш новый возраст:")
    await Form.next()

@dp.message_handler(state=Form.age)
async def edit_age(message: types.Message, state: FSMContext):
    age = message.text.strip()
    if not age.isdigit():
        await message.answer("Возраст должен быть числом. Пожалуйста, введите возраст снова:")
        return
    await state.update_data(age=int(age))
    await message.answer("Введите вашу новую группу в колледже:")
    await Form.next()

@dp.message_handler(state=Form.student_group)
async def edit_group(message: types.Message, state: FSMContext):
    await state.update_data(student_group=message.text.strip())
    await message.answer("Введите новое описание себя:")
    await Form.next()

@dp.message_handler(state=Form.description)
async def edit_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await message.answer("Отправьте новое фото.")
    await Form.next()

@dp.message_handler(content_types=types.ContentTypes.PHOTO, state=Form.photo)
async def edit_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    file_info = await bot.get_file(photo_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)
    
    if not os.path.exists('photos'):
        os.makedirs('photos')
    
    photo_path = f"photos/{message.from_user.id}.jpg"
    with open(photo_path, 'wb') as new_file:
        new_file.write(file.read())

    await state.update_data(photo_path=photo_path)
    await message.answer("Выберите ваш новый пол:", reply_markup=gender_menu)
    await Form.next()

@dp.message_handler(state=Form.gender)
async def edit_gender(message: types.Message, state: FSMContext):
    gender = message.text.strip()
    if gender not in ["Мужской", "Женский"]:
        await message.answer("Пожалуйста, выберите правильный пол.")
        return
    
    await state.update_data(gender=gender)
    await message.answer("Введите ваш новый Telegram ID (например, @username):")
    await Form.next()

@dp.message_handler(state=Form.telegram_id)
async def edit_telegram_id(message: types.Message, state: FSMContext):
    telegram_id = message.text.strip()
    if not telegram_id.startswith('@'):
        await message.answer("Telegram ID должен начинаться с символа '@'. Пожалуйста, введите снова:")
        return
    
    user_data = await state.get_data()

    try:
        add_or_update_user(
            message.from_user.id,
            user_data['name'],
            user_data['age'],
            user_data['student_group'],
            user_data['description'],
            user_data['photo_path'],
            telegram_id,
            user_data['gender']
        )
        await message.answer("Ваша анкета успешно обновлена!", reply_markup=main_menu)
    except Exception as e:
        logging.error(f"Ошибка обновления данных анкеты: {e}")
        await message.answer("Ошибка обновления данных анкеты. Пожалуйста, попробуйте снова.")

    await state.finish()

# Команда "Смотреть анкеты"
@dp.message_handler(text="Смотреть анкеты")
async def search_profiles(message: types.Message):
    await message.answer("Выберите пол для поиска анкет:", reply_markup=search_gender_menu)

# Обработка выбора пола для поиска
@dp.message_handler(lambda message: message.text in ["Мужской", "Женский", "Неважно"])
async def process_gender_search(message: types.Message):
    gender = message.text.strip()
    users = get_all_users()
    user_id = message.from_user.id
    last_viewed_time = datetime.now() - timedelta(days=1)

    # Исключаем собственную анкету и анкеты, которые были просмотрены за последние 24 часа
    filtered_users = [user for user in users
                      if user[0] != user_id and (user[0], last_viewed_time) not in get_viewed_profiles(user_id)]

    if gender != "Неважно":
        filtered_users = [user for user in filtered_users if user[7] == gender]

    if filtered_users:
        for user in filtered_users:
            user_id, name, age, student_group, description, photo_path, telegram_id, _ = user
            photo = open(photo_path, 'rb') if os.path.exists(photo_path) else None
            # Добавляем текущую анкету в список просмотренных
            add_viewed_profile(user_id, user_id)
            await bot.send_photo(
                message.chat.id,
                photo,
                caption=f"""
                Имя: {name}
                Возраст: {age}
                Группа: {student_group}
                Описание: {description}
                """,
                reply_markup=InlineKeyboardMarkup().add(
                    InlineKeyboardButton("👍 Лайк", callback_data=f"like_{user_id}"),
                    InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike_{user_id}")
                )
            )
    else:
        await message.answer("Анкеты не найдены.")

# Обработка нажатия кнопок лайка и дизлайка
@dp.callback_query_handler(lambda c: c.data.startswith('like_') or c.data.startswith('dislike_'))
async def process_like_dislike(callback_query: types.CallbackQuery):
    action, liked_user_id = callback_query.data.split('_')
    liked_user_id = int(liked_user_id)
    current_user_id = callback_query.from_user.id

    # Проверка, ставил ли пользователь уже лайк на эту анкету
    if get_user_likes(current_user_id, liked_user_id):
        await callback_query.answer("Вы уже поставили лайк этой анкете.")
        return

    if action == 'like':
        add_like(current_user_id, liked_user_id)

        # Уведомляем пользователя, что на его анкету поставили лайк
        user_profile = get_user_profile(current_user_id)
        user_photo_path = get_user_profile_photo(current_user_id)
        await bot.send_photo(
            liked_user_id,
            open(user_photo_path, 'rb'),
            caption=f"Вам поставили лайк! Вот анкета этого пользователя:\n\n{user_profile}",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("👍 Лайк", callback_data=f"like_{current_user_id}"),
                InlineKeyboardButton("👎 Дизлайк", callback_data=f"dislike_{current_user_id}")
            )
        )

        # Проверка взаимного лайка
        if check_match(current_user_id, liked_user_id):
            # Уведомляем первого пользователя о совпадении
            await bot.send_message(
                current_user_id,
                f"Поздравляю! У вас совпадение с пользователем {get_user_name(liked_user_id)}! Telegram ID: {get_user_telegram_id(liked_user_id)}"
            )
            # Уведомляем второго пользователя о совпадении
            await bot.send_message(
                liked_user_id,
                f"Поздравляю! У вас совпадение с пользователем {get_user_name(current_user_id)}! Telegram ID: {get_user_telegram_id(current_user_id)}"
            )
            
    elif action == 'dislike':
        # Запрещаем спам дизлайками
        await callback_query.answer("Дизлайк функционал в разработке.")
        
    # Удаляем кнопки лайка и дизлайка после нажатия
    await callback_query.message.edit_reply_markup()

    await callback_query.answer()

# Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
