""" Buttons and other settings """

from telebot import types

def markup():
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.add('Add new button ', 'Add second button  2')

    return markup