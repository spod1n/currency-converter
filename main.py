"""
Point of entry.

Klymentii Spodin (2023)
Python 3.10.6
"""

import os
import json

import requests
import telebot

from process import handlers, markups


# %%
# FUNCTIONS
def get_schema(path) -> dict:
    """Функція для отримання схеми.

    :return: dict
    """

    with open(path, 'r', encoding='utf-8') as js_file:
        parameters = json.load(js_file)

    return parameters


# %%
# VARIABLES & CONSTANTS
PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))
os.chdir(PROJECT_PATH)

SCHEMA_FILE = 'schema.json'


if __name__ == '__main__':
    schema = get_schema(SCHEMA_FILE)
    bot = telebot.TeleBot(rule_config.read('telegram', 'token'))

    print(schema)

    bot.infinity_polling()