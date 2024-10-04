from __future__ import annotations
import json
import logging
import os
import random

import requests
from dotenv import load_dotenv
from telegram import Message, MessageEntity, Update
from telegram.ext import ContextTypes

from colors import *
load_dotenv()


data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot', 'data')


def localized_text(key, *args, **kwargs):
    """
    Return translated text for a key in specified bot_language.
    Keys and translations can be found in the translations.json.
    """
    bot_language = os.getenv('BOT_LANGUAGE')

    try:
        with open('data/translations.json', 'r', encoding='utf-8') as f:
            translations = json.load(f)
    except json.JSONDecodeError:
        logging.error(f"Failed to decode file `translations.json`")
        exit(1)

    message = translations.get(bot_language, {}).get(key)

    if message is None:
        logging.warning(f"No translation for language code {LIGHT_CYAN}`{bot_language}`{WHITE} and key {LIGHT_MAGENTA}`{key}`{WHITE}")

        message = translations.get('en', {}).get(key)
        if message is None:
            logging.warning(f"No English for key {LIGHT_MAGENTA}`{key}`{WHITE} in translations.json")
            return key

    try:
        return message.format(**kwargs)
    except:
        return message.format(*args)


def get_games_data():
    response = requests.get('https://raw.githubusercontent.com/OxFF00FF/Hamster_Mayhem/refs/heads/master/data/playground_games_data.json')
    response.raise_for_status()
    return response.json()


def _loading_gif():
    loading_dir = f'{data_path}/loading_indicators/Loading'
    n = len(os.listdir(loading_dir))
    return open(f'{loading_dir}/Loading_{random.randint(1, n)}.gif', 'rb')


def _error_gif():
    error_dir = f'{data_path}/loading_indicators/Error'
    n = len(os.listdir(error_dir))
    return open(f'{error_dir}/Error_{random.randint(1, n)}.gif', 'rb')


def _downloading_gif():
    downloading_dir = f'{data_path}/loading_indicators/Downloading'
    n = len(os.listdir(downloading_dir))
    return open(f'{downloading_dir}/Downloading_{random.randint(1, n)}.gif', 'rb')


def _not_available():
    access_dir = f'{data_path}/loading_indicators/Access'
    n = len(os.listdir(access_dir))
    return open(f'{access_dir}/Access_{random.randint(1, n)}.gif', 'rb')


def _hamster_key():
    return open(f'{data_path}/loading_indicators/Hamster/hamster_key.jpg', 'rb')


def _combo_image():
    return open(f'{data_path}/loading_indicators/Hamster/combo.webp', 'rb')


def _game_image(prefix):
    games_data = [app for app in get_games_data()['apps'] if app.get('available')]
    for promo in games_data:
        if promo['prefix'] == prefix:
            try:
                return open(f'{data_path}/loading_indicators/Hamster/{prefix.strip()}.jpg', 'rb')
            except Exception as e:
                logging.error(e)
                return open(f'{data_path}/loading_indicators/Hamster/default_game.webp', 'rb')


def message_text(message: Message) -> str:
    message_txt = message.text
    if message_txt is None:
        return ''

    for _, text in sorted(message.parse_entities([MessageEntity.BOT_COMMAND]).items(),
                          key=(lambda item: item[0].offset)):
        message_txt = message_txt.replace(text, '').strip()
    return message_txt if len(message_txt) > 0 else ''


def get_thread_id(update: Update) -> int | None:
    if update.effective_message and update.effective_message.is_topic_message:
        return update.effective_message.message_thread_id
    return None


async def error_handler(_: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f'Exception while handling an update: {context.error}')


def load_settings():
    """Load settings from the JSON file."""
    try:
        with open('settings.json', 'r') as file:
            settings = json.load(file)
            return settings
    except (FileNotFoundError, json.JSONDecodeError):
        print("Настройки не найдены. Создан файл с настройками по умолчанию")
        settings = {'send_to_group': False, 'save_to_file': False, 'apply_promo': False}
        save_settings(settings)
        return settings


def save_settings(settings):
    """Save settings to the JSON file."""
    with open('settings.json', 'w') as file:
        json.dump(settings, file, indent=4)


def remain_time(seconds):
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    h = str(h).zfill(2)
    m = str(m).zfill(2)
    s = str(s).zfill(2)
    return f"{h}:{m}:{s}"


def text_to_morse(text: str) -> str:
    MORSE_CODE_DICT = {
        'A': '• —', 'B': '— • • •', 'C': '— • — •', 'D': '— • •', 'E': '•', 'F': '• • — •',
        'G': '— — •', 'H': '• • • •', 'I': '• •', 'J': '• — — —', 'K': '— • —', 'L': '• — • •',
        'M': '— —', 'N': '— •', 'O': '— — —', 'P': '• — — •', 'Q': '— — • —', 'R': '• — •',
        'S': '• • •', 'T': '—', 'U': '• • —', 'V': '• • • —', 'W': '• — —', 'X': '— • • —',
        'Y': '— • — —', 'Z': '— — • •', '1': '• — — — —', '2': '• • — — —', '3': '• • • — —',
        '4': '• • • • —', '5': '• • • • •', '6': '— • • • •', '7': '— — • • •', '8': '— — — • •',
        '9': '— — — — •', '0': '— — — — —', ', ': '— — • • — —', '.': '• — • — • —', '?': '• • — — • •',
        "'": '• — — — — •', '!': '— • — • — —', '/': '— • • — •', '(': '— • — — •', ')': '— • — — • —',
        '&': '• — • • •', ':': '— — — • • •', ';': '— • — • — •', '=': '— • • • —', '+': '• — • — •',
        '-': '— • • • • —', '_': '• • — — • —', '"': '• — • • — •', '$': '• • • — • • —', '@': '• — — • — •'}

    text = text.upper()
    morse_text = '\n'.join(f'{char}:  {MORSE_CODE_DICT.get(char, "")}' for char in text)
    return morse_text
