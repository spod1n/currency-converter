""" Buttons and other settings """

import pandas as pd
from telebot import types


def get_text_buttons(rate_data: pd.DataFrame, param_name: str, filter_value=None):
    keyboard = types.InlineKeyboardMarkup(row_width=2)

    if param_name == 'CodeNameA':
        options = rate_data['CodeNameA'].unique().tolist()
    elif param_name == 'CodeNameB':
        filter_rate_data = rate_data[rate_data['CodeNameA'] == filter_value]
        options = filter_rate_data['CodeNameB'].unique().tolist()
    else:
        options = []

    for option in options:
        button = types.InlineKeyboardButton(text=option, callback_data=option)
        keyboard.add(button)
    return keyboard
