""" Handling major events and functions """

def bot_handlers(bot):
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        bot.send_message(message.chat.id, "Привіт! Я бот. Введи /help для отримання довідки.")


    @bot.message_handler(commands=['help'])
    def handle_help(message):
        bot.send_message(message.chat.id, "Це довідковий бот. Якщо у вас є питання, звертайтесь!")


    # Обробник всіх інших повідомлень
    @bot.message_handler(func=lambda message: True)
    def handle_echo(message):
        bot.send_message(message.chat.id, f"Ви сказали: {message.text}")