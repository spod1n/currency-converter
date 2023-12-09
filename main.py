"""
Point of entry.

Klymentii Spodin (2023)
Python 3.10.6
"""

import os
import json

import requests
import configparser
import telebot

from process import handlers, markup


# %%
# FUNCTIONS
def get_schema(path: str) -> dict:
    """ Функція для отримання схеми.

    :return: (dict) Схема у форматі JSON.
    """

    with open(path, 'r', encoding='utf-8') as js_file:
        parameters = json.load(js_file)

    return parameters


def get_config(section: str, key: str) -> str:
    """ Функція для отримання значення ключа файла конфігурації.

    :param section: (str) Ім'я секція
    :param key: (str) Ім'я ключа
    :return: (str) Значення ключа
    """

    if os.path.exists(schema['config_path']):
        config_obj = configparser.ConfigParser()
        config_obj.read(schema['config_path'])

        # Перевірка, чи існує вказана секція та ключ у конфігураційному файлі
        if config_obj.has_section(section) and config_obj.has_option(section, key):
            return config_obj[section][key]
        else:
            raise ValueError('Section or key not found in the configuration file..')
    else:
        raise ValueError('Configuration file not found..')


# %%
# VARIABLES & CONSTANTS
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_PATH)


# %%
# SCRIPT
schema = get_schema('schema.json')
bot = telebot.TeleBot(get_config('telegram', 'token'))

handlers.bot_handlers(bot)


if __name__ == '__main__':
    print('start polling..')
    bot.infinity_polling()
