import os
import json
import time
import requests
import logging
import sqlite3
import time
from config import *
from database import *

user_data = {}
user_collection = {}

def ask_gpt(genre, character, setting, mode='continue', user_input=None):
    url = f"https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        'Authorization': f'Bearer {IAM_TOKEN}',
        'Content-Type': 'application/json'
    }
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/{GPT_MODEL}/latest",
        "completionOptions": {
            "stream": False,
            "temperature": 0.6,
            "maxTokens": 100
        },
        "messages": [
            {
                "role": "user",
                "text": f"Ты сценарист истории, жанр которой: {genre}, главный герой: {character}, сеттинг которой: {setting}"
            }
        ]
    }

    if get_all_tokens() >= MAX_TOKENS:
        return "Количество доступных токенов исчерпано."
    else:
        if user_input:
            data["messages"].append({"role": "user", "text": user_input})

        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code != 200:
                result = f"Status code {response.status_code}"
                return result
            result = response.json()['result']['alternatives'][0]['message']['text']
        except Exception as e:
            result = "Произошла непредвиденная ошибка. Подробности см. в журнале."
        return result


def create_system_prompt(user_id):
    # Получаем данные пользователя из базы данных
    user_info = get_user_data(user_id)

    # Проверяем, есть ли информация о пользователе в базе данных
    if user_info:
        genre = user_info['genre']
        character = user_info['character']
        setting = user_info['setting']

        # Формируем system_prompt на основе полученных данных
        system_prompt = f"Ты - сценарист историй по жанру: {genre}, главный герой истории: {character}, сеттинг: {setting}. Начнём писать истории!"

        return system_prompt
    else:
        return "Данные пользователя не найдены. Начните новую историю, выбрав жанр, героя и сеттинг."


def create_new_token():
    """Создание нового токена"""
    metadata_url = "http://169.254.169.254/computeMetadata/v1/instance/service-accounts/default/token"
    headers = {"Metadata-Flavor": "Google"}

    token_dir = os.path.dirname(TOKEN_PATH)
    if not os.path.exists(token_dir):
        os.makedirs(token_dir)

    try:
        response = requests.get(metadata_url, headers=headers)
        if response.status_code == 200:
            token_data = response.json()
            # Добавляем время истечения токена к текущему времени
            token_data['expires_at'] = time.time() + token_data['expires_in']
            with open(TOKEN_PATH, "w") as token_file:
                json.dump(token_data, token_file)
            logging.info("Token created")
            return True
        else:
            logging.error(f"Failed to retrieve token. Status code: {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"An error occurred while retrieving token: {e}")
        return False


if __name__ == '__main__':
    prepare_db()