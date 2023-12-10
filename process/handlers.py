""" Handling major events and functions """

import json
import datetime as dt
import pandas as pd
import sqlite3

from time import sleep
from requests import HTTPError, get

from process import markup


def bot_handlers(bot):
    user_params = {}
    rate_data = get_rate()

    @bot.message_handler(commands=['start'])
    def handle_start(message):
        chat_id = message.chat.id

        bot.reply_to(message, f'Вітаю, {message.from_user.username}! Я бот з конвертації валюти.')
        bot.send_message(chat_id, 'Виберіть початкову валюту:',
                         reply_markup=markup.get_text_buttons(rate_data, 'CodeNameA'))

    def save_history(chat_id, user_id, selected_a, selected_b, value_sum, result):
        history_file_path = 'history.json'

        try:
            with open(history_file_path, 'r') as history_file:
                history_log = json.load(history_file)
        except FileNotFoundError:
            history_log = []

        history_entry = {
            'chat_id': chat_id,
            'user_id': user_id,
            'selected_start_currency': selected_a,
            'selected_end_currency': selected_b,
            'value_sum': value_sum,
            'result': result
        }

        history_log.append(history_entry)

        history_log = history_log[-10:]

        with open(history_file_path, 'w') as history_file:
            json.dump(history_log, history_file, indent=4)

    @bot.callback_query_handler(
        func=lambda call: call.data in rate_data['CodeNameA'].unique().tolist() or
                          call.data in rate_data['CodeNameB'].unique().tolist())
    def handle_text_selection(call):
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        selected_text = call.data

        user_params[user_id]['username'] = call.message.from_user.username

        # Збереження текстового параметра
        if user_id not in user_params:
            user_params[user_id] = {}

        if 'CodeNameA' not in user_params[user_id]:
            user_params[user_id]['CodeNameA'] = selected_text
            bot.send_message(chat_id, f'Валютою конвертації вибрано: {selected_text}.\n'
                                      'Тепер виберіть валюту, в яку будемо конвертувати:',
                             reply_markup=markup.get_text_buttons(rate_data, 'CodeNameB',
                                                                  filter_value=selected_text))
        elif 'CodeNameB' not in user_params[user_id]:
            user_params[user_id]['CodeNameB'] = selected_text

            # Вибір наступного параметра або виведення результату
            if 'value_sum' not in user_params[user_id]:
                bot.send_message(chat_id, 'Введіть суму конвертації:')
            else:
                handle_number_input(bot.message.Message(message_json={'chat': {'id': chat_id}}))

    @bot.message_handler(func=lambda message: message.text.isdigit(), content_types=['text'])
    def handle_number_input(message):
        """ Обробник введення числового параметра.

        :param message:
        :return:
        """
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Перевірка, що введено число
        try:
            value_sum = float(message.text)
        except ValueError:
            bot.send_message(chat_id, 'Будь ласка, введіть коректне число.')
            return

        # Перевірка, чи користувач вже вибрав перші два параметри
        if user_id not in user_params or 'CodeNameA' not in user_params[user_id]:
            bot.send_message(chat_id, 'Будь ласка, виберіть початкову валюту.')
            return

        if 'CodeNameB' not in user_params[user_id]:
            bot.send_message(chat_id, 'Будь ласка, виберіть кінцеву валюту.')
            return

        rate_result = rate_data[(rate_data['CodeNameA'] == user_params[user_id]['CodeNameA']) &
                                (rate_data['CodeNameB'] == user_params[user_id]['CodeNameB'])]
        if rate_result.shape[0] != 1:
            bot.send_message(chat_id, 'Щось пішло не так.. За вибраними параметрами не можна однозначно відвісти.')
            return

        final_result = rate_result['value'].iloc[0] * value_sum

        # Збереження числового параметра
        user_params[user_id]['value_sum'] = value_sum

        # Збереження історії запитів
        save_history(chat_id,
                     user_id,
                     user_params[user_id]['CodeNameA'],
                     user_params[user_id]['CodeNameB'],
                     value_sum,
                     final_result)

        # Виведення результату
        result = f"Фінальний результат: {user_params[user_id]['CodeNameA']} * {user_params[user_id]['CodeNameB']} * {value_sum} = {final_result}"
        bot.send_message(chat_id, result)


def get_rate():
    schema = get_schema('schema.json')
    checking_for_update(schema)

    with sqlite3.connect(schema['database']['name']) as conn:
        df_rate = pd.read_sql(f"SELECT * FROM {schema['database']['tables']['rate']}", conn)
        df_current = pd.read_sql(f"SELECT * FROM {schema['database']['tables']['currency']}", conn)

    for i in ['A', 'B']:
        df_rate = pd.merge(df_rate, df_current, left_on=f'code{i}', right_on='CodeId', how='inner')
        df_rate.rename(columns={'CodeName': f'CodeName{i}', 'CurrencyName': f'CurrencyName{i}', 'Symbol': f'Symbol{i}'},
                       inplace=True)

    return df_rate[schema['database']['fields_rate_join']]


def checking_for_update(schema: dict) -> bool:
    """ Функція перевіряє дату та час останнього оновлення таблиці.
    Якщо останнє оновлення було понад 30 хвилин назад - оновлюю таблицю бази даних новими даними API.

    :return: (bool)
    """

    with sqlite3.connect(schema['database']['name']) as conn:
        cur = conn.cursor()
        cur.execute(f"SELECT MAX([datetime_insert]) FROM {schema['database']['tables']['rate']}")
        last_date_insert = dt.datetime.strptime(cur.fetchall()[0][0], '%Y-%m-%d %H:%M:%S.%f')

        if (dt.datetime.now() - last_date_insert) >= dt.timedelta(minutes=10):
            df_rate = pd.DataFrame(get_response(schema['monobank_api']))

            if not df_rate.empty:
                df_rate['datetime_update'] = df_rate['date'].apply(lambda x: dt.datetime.utcfromtimestamp(x))
                df_rate['datetime_insert'] = dt.datetime.today()

                df_rate.loc[df_rate['rateCross'].notna(), ['rateBuy', 'rateSell']] = df_rate['rateCross']
                df_rate.fillna(value=0, inplace=True)
                df_rate['rateCross'] = df_rate['rateCross'].astype(bool).astype(int)

                tmp_df = df_rate.copy()
                df_rate.rename(columns={'currencyCodeA': 'codeA', 'currencyCodeB': 'codeB',
                                        'rateCross': 'is_cross', 'rateBuy': 'value'},
                               inplace=True)
                tmp_df.rename(columns={'currencyCodeB': 'codeA', 'currencyCodeA': 'codeB',
                                       'rateCross': 'is_cross', 'rateSell': 'value'},
                              inplace=True)

                df_rate = pd.concat([df_rate[schema['database']['fields_rate']],
                                     tmp_df[schema['database']['fields_rate']]],
                                    ignore_index=True)

                df_rate.to_sql(schema['database']['tables']['rate'],
                               conn,
                               if_exists='replace',
                               index=False)

                conn.commit()
                print('add new rate')
                return True

        else:
            return False


def get_response(url: str) -> dict:
    """ Виклик URL та перевірка коду відповіді API.
    Якщо код відповіді знаходиться не в діапазоні 200 - 299: викликаємо URL повторно.
    Кількість спроб виклику - 5.

    :param url: (str) адреса
    :return: (dict) відповідь API
    """
    for attempt in range(1, 6):
        try:
            response = get(url)
            code = response.status_code

            if 200 <= code < 300:
                return response.json()
            else:
                print(f'API status code: {code}.. Retrying... Attempt {attempt} of 5...')
                sleep(attempt * 10)

        except HTTPError as http_err:
            print(f'Http response error: {http_err}.. Retrying... Attempt {attempt} of 5...')
            sleep(attempt * 10)

        except Exception as exc_str:
            print(f'Global error: {exc_str}.. Retrying... Attempt {attempt} of 5...')
            sleep(attempt * 10)
    else:
        return dict()


def get_schema(path: str) -> dict:
    """ Функція для отримання схеми проєкту.

    :return: (dict) Схема у форматі JSON.
    """

    with open(path, 'r', encoding='utf-8') as js_file:
        parameters = json.load(js_file)

    return parameters
