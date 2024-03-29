from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from config import *
from database import *
from gpt import *
import logging

bot = TeleBot(TELEGRAM_TOKEN)
prepare_db()
logging.basicConfig(filename='logs.txt', level=logging.DEBUG)
create_new_token()

def log_message(message):
    with open('logs.txt', 'a') as file:
        log_entry = f"Time: {message.date}, User ID: {message.from_user.id}, Message: {message.text}\n"
        file.write(log_entry)
def create_genre_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    genres = ["Ужасы", "Фантастика", "Комедия"]
    for genre in genres:
        keyboard.add(KeyboardButton(genre))
    return keyboard

def create_character_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    characters = ["Бэтмэн", "Супермэн", "Спайдер-мен", "Терминатор"]
    for character in characters:
        keyboard.add(KeyboardButton(character))
    return keyboard

def create_setting_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    settings = ["Дремучий лес", "Замок", "Кибер город"]
    for setting in settings:
        keyboard.add(KeyboardButton(setting))
    return keyboard

def create_extra_buttons_markup():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("/whole_story"))
    keyboard.add(KeyboardButton("/new_story"))
    keyboard.add(KeyboardButton("/debug"))
    return keyboard

@bot.message_handler(commands=['start'])
def start(message):
    if is_users_limit():
        print("Достигнуто максимальное количество пользователей")
    else:
        bot.send_message(message.chat.id, "Привет! Я бот-сценарист. Нажми /new_story, чтобы начать создание новой истории.")

@bot.message_handler(commands=['new_story'])
def new_story(message):
    bot.send_message(message.chat.id, "Выбери жанр:", reply_markup=create_genre_keyboard())

@bot.message_handler(func=lambda message: message.text in ["Ужасы", "Фантастика", "Комедия"])
def handle_genre_choice(message):
    user_id = message.from_user.id
    genre = message.text
    save_user_data(user_id, genre, None, None)  # Сохраняем выбранный жанр
    bot.send_message(user_id, f"Ты выбрал жанр: {genre}. Теперь выбери главного героя:",
                     reply_markup=create_character_keyboard())

@bot.message_handler(func=lambda message: message.text in ["Бэтмэн", "Супермэн", "Спайдер-мен", "Терминатор"])
def handle_character_choice(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    character = message.text
    genre = None  # По умолчанию устанавливаем жанр None
    if user_data:
        genre = user_data[0][1]  # Получаем жанр только если данные пользователя существуют
    save_user_data(user_id, genre, character, None)  # Сохраняем выбранного героя
    bot.send_message(user_id, f"Ты выбрал героя: {character}. Теперь выбери сеттинг:",
                     reply_markup=create_setting_keyboard())

@bot.message_handler(func=lambda message: message.text in ["Дремучий лес", "Замок", "Кибер город"])
def handle_setting_choice(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    setting = message.text
    genre = None  # По умолчанию устанавливаем жанр None
    character = None  # По умолчанию устанавливаем героя None
    if user_data:
        genre = user_data[0][1]  # Получаем жанр
        character = user_data[0][2]  # Получаем героя
    save_user_data(user_id, genre, character, setting)  # Сохраняем выбранный сеттинг
    bot.send_message(user_id, f"Ты выбрал сеттинг: {setting}. Начнём! Если у тебя есть какая-то информация,"
                              f" которую мы должны учесть, напиши ее сейчас, если нет, нажми /begin для генерации истории.")

@bot.message_handler(commands=['begin'])
def begin_story(message):
    if is_users_limit():
        print("Достигнуто максимальное количество пользователей")
    else:
        log_message(message)
        user_id = message.from_user.id
        user_data = get_user_data(user_id)  # Получаем данные пользователя из базы данных
        if user_data:
            genre = user_data[0][1]  # Получаем жанр
            character = user_data[0][2]  # Получаем героя
            setting = user_data[0][3]  # Получаем сеттинг
            story = ask_gpt(genre, character, setting)  # Генерируем историю с помощью функции ask_gpt
            bot.send_message(message.chat.id, story, reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/end")))  # Отправляем сгенерированную историю
            save_user_data(user_id, genre, character, setting, story, 0)
        else:
            bot.send_message(message.chat.id, "Чтобы начать историю, выбери жанр, героя и сеттинг с помощью команд /new_story.")

@bot.message_handler(commands=['end'])
def end_story(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    log_message(message)
    if user_data:
        genre, character, setting = user_data[0][1:4]
        response = str(user_data[0][4])
        is_ended = user_data[0][5]  # Получаем значение флага is_ended
        if is_ended == 0:  # Проверяем, завершена ли уже история
            save_user_data(user_id, genre, character, setting, response, 1)  # Устанавливаем is_ended в 1
            end = ask_gpt(genre, character, setting, mode='continue', user_input=END_STORY)
            save_user_data(user_id, genre, character, setting, response + ". " + end, 1)
            bot.send_message(user_id, end)
            bot.send_message(user_id, "Спасибо, что писал со мной историю!", reply_markup=create_extra_buttons_markup())
    else:
        bot.send_message(user_id, "Для получения всей истории используйте команду /whole_story.")


@bot.message_handler(commands=['whole_story'])
def whole_story(message):
    user_id = message.from_user.id
    user_data = get_user_data(user_id)
    if user_data:
        response = user_data[0][4]  # Получаем всю историю из базы данных
        bot.send_message(user_id, response)
    else:
        bot.send_message(user_id, "История отсутствует.")

@bot.message_handler(commands=['debug'])
def handle_debug(message):
    log_file_path = 'logs.txt'
    if os.path.exists(log_file_path):
        with open(log_file_path, 'rb') as file:
            bot.send_document(message.chat.id, file)
    else:
        bot.send_message(message.chat.id, "Файл с логами не найден.")


@bot.message_handler(func=lambda message: True)
def handle_user_input(message):
    if is_users_limit():
        print("Достигнуто максимальное количество пользователей")
    else:
        log_message(message)
        user_id = message.from_user.id
        user_input = message.text
        user_data = get_user_data(user_id)
        if user_data:
            genre = user_data[0][1]
            character = user_data[0][2]
            setting = user_data[0][3]
            response = str(user_data[0][4])
            is_ended = user_data[0][5]  # Получаем значение флага is_ended
            if is_ended == 0:  # Проверяем, завершена ли уже история
                if genre and character and setting and response:
                    story = ask_gpt(genre, character, setting, user_input=f"{user_input}. {CONTINUE_STORY}")
                    save_user_data(user_id, genre, character, setting, response + ". " + story)
                    bot.send_message(user_id, story, reply_markup=ReplyKeyboardMarkup(resize_keyboard=True).add(KeyboardButton("/end")))
        else:
            bot.send_message(user_id, "Чтобы начать историю, выбери жанр, героя и сеттинг с помощью команд /new_story.")


bot.polling()