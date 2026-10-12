import telebot

TOKEN = "8854430576:AAGDUzRNstP58pQuGIOx8hX9iKBC6YKOvPI"
ADMIN_ID = 8543358373

bot = telebot.TeleBot(TOKEN)

@bot.message_handler(commands=['start'])
def start_cmd(message):
    chat_id = message.chat.id
    if chat_id == ADMIN_ID:
        bot.send_message(chat_id, "<b>Привет, владелец!</b>\nБот успешно запущен и готов к работе 24/7.", parse_mode="HTML")
    else:
        bot.send_message(chat_id, "Привет! Напишите ваш вопрос или сообщение, и администратор ответит вам в ближайшее время.")

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'document'])
def handle_messages(message):
    chat_id = message.chat.id
    
    # Если пишет администратор (вы)
    if chat_id == ADMIN_ID:
        if message.reply_to_message and message.reply_to_message.forward_from:
            user_id = message.reply_to_message.forward_from.id
            if message.content_type == 'text':
                bot.send_message(user_id, message.text)
            elif message.content_type == 'photo':
                bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption)
            bot.send_message(ADMIN_ID, "✅ Ответ отправлен пользователю!")
        else:
            bot.send_message(ADMIN_ID, "⚠️ Чтобы ответить пользователю, зажмите его пересланное сообщение и выберите <b>'Ответить' (Reply)</b>.", parse_mode="HTML")
    
    # Если пишет обычный пользователь
    else:
        bot.forward_message(ADMIN_ID, chat_id, message.message_id)
        bot.send_message(chat_id, "Ваше сообщение доставлено администратору. Ожидайте ответа!")

if __name__ == '__main__':
    # Снимаем старый Webhook на случай, если он остался от веб-хостинга
    bot.remove_webhook()
    print("Бот запущен...")
    bot.infinity_polling()