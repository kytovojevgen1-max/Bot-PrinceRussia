import telebot
from telebot import types

TOKEN = "8854430576:AAGDUzRNstP58pQuGIOx8hX9iKBC6YKOvPI"
SUPER_ADMIN_ID = 8543358373  # Ваш ID (главный владелец)

bot = telebot.TeleBot(TOKEN)

# Список ID всех администраторов
admins = {SUPER_ADMIN_ID}
# Словарь для связи username -> user_id
username_to_id = {}
# Состояния пользователей (что они сейчас отправляют)
user_states = {}

# --- КЛАВИАТУРЫ ---
def get_main_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛒 Донат Магазин")
    kb.row("💡 Предложить идею", "🛠 Поддержка / Вопрос")
    if user_id in admins:
        kb.row("⚙️ Админ-панель")
    return kb

def get_admin_keyboard():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("➕ Добавить админа", callback_data="add_admin"))
    kb.add(types.InlineKeyboardButton("➖ Удалить админа", callback_data="remove_admin"))
    kb.add(types.InlineKeyboardButton("📋 Список админов", callback_data="list_admins"))
    return kb

# --- КОМАНДА /START ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    user_id = message.chat.id
    if message.from_user.username:
        username_to_id[message.from_user.username.lower()] = user_id

    user_states[user_id] = None

    welcome_text = (
        "<b>Приветствуем на проекте Prince Russia!</b>\n\n"
        "Воспользуйтесь меню ниже для связи с администрацией:\n\n"
        "🛒 <b>Донат Магазин</b> — покупка доната и валюты\n"
        "💡 <b>Предложить идею</b> — ваши предложения по улучшению проекта\n"
        "🛠 <b>Поддержка / Вопрос</b> — задать вопрос или сообщить о проблеме"
    )
    bot.send_message(user_id, welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard(user_id))

# --- ОБРАБОТКА КНОПОК МЕНЮ ---
@bot.message_handler(func=lambda msg: msg.text in ["🛒 Донат Магазин", "💡 Предложить идею", "🛠 Поддержка / Вопрос", "⚙️ Админ-панель"])
def menu_handler(message):
    user_id = message.chat.id
    
    if message.text == "🛒 Донат Магазин":
        shop_text = (
            "<b>🛒 Донат Магазин проекта Prince Russia</b>\n\n"
            "Для покупки доната, игровой валюты или привилегий обращайтесь к главному администратору:\n\n"
            "🔹 <b>Telegram:</b> @AsikWhiskey\n"
            "🔹 <b>ВКонтакте:</b> https://vk.com/asik_whiskey\n\n"
            "⚠️ <i>Покупки совершаются только через указанные контакты! Остерегайтесь фейков.</i>"
        )
        bot.send_message(user_id, shop_text, parse_mode="HTML", disable_web_page_preview=True)

    elif message.text == "💡 Предложить идею":
        user_states[user_id] = 'idea'
        bot.send_message(
            user_id, 
            "<b>💡 Раздел предложений и улучшений</b>\n\n"
            "Напишите вашу идею, предложение или добавление на проект (можно прикрепить скриншот, фото или видео):", 
            parse_mode="HTML"
        )

    elif message.text == "🛠 Поддержка / Вопрос":
        user_states[user_id] = 'support'
        bot.send_message(
            user_id, 
            "<b>🛠 Техническая поддержка</b>\n\n"
            "Опишите вашу проблему или задайте вопрос (вы можете отправить текст, фото, видео или голосовое сообщение):", 
            parse_mode="HTML"
        )

    elif message.text == "⚙️ Админ-панель":
        if user_id in admins:
            bot.send_message(user_id, "<b>⚙️ Панель управления администратора:</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(user_id, "У вас нет доступа к этой панели.")

# --- CALLBACK ОБРАБОТКА ДЛЯ АДМИН-ПАНЕЛИ ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if user_id not in admins:
        bot.answer_callback_query(call.id, "У вас нет прав!", show_alert=True)
        return

    if call.data == "add_admin":
        msg = bot.send_message(user_id, "Введите @username пользователя, которому хотите выдать админку:")
        bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "remove_admin":
        msg = bot.send_message(user_id, "Введите @username пользователя, у которого хотите снять админку:")
        bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data == "list_admins":
        text = f"<b>📋 Список администраторов ({len(admins)}):</b>\n\n"
        for adm in admins:
            role = "👑 Владелец" if adm == SUPER_ADMIN_ID else "🛠 Админ"
            text += f"• ID: <code>{adm}</code> ({role})\n"
        bot.send_message(user_id, text, parse_mode="HTML")

def process_add_admin(message):
    if message.chat.id not in admins:
        return
    username = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(username)
    
    if target_id:
        admins.add(target_id)
        bot.send_message(message.chat.id, f"✅ Пользователь @{username} успешно добавлен в список администраторов!")
        bot.send_message(target_id, "🎉 Вам выданы права администратора! Нажмите /start для обновления меню.")
    else:
        bot.send_message(message.chat.id, f"❌ Пользователь @{username} еще не запускал бота. Он должен написать боту /start хотя бы один раз.")

def process_remove_admin(message):
    if message.chat.id not in admins:
        return
    username = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(username)
    
    if target_id:
        if target_id == SUPER_ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Нельзя снять права у главного владельца!")
            return
        admins.discard(target_id)
        bot.send_message(message.chat.id, f"✅ Права администратора у @{username} успешно сняты.")
        bot.send_message(target_id, "ℹ️ Ваши права администратора были отозваны.")
    else:
        bot.send_message(message.chat.id, f"❌ Пользователь @{username} не найден.")

# --- ОБРАБОТКА ВСЕХ ВХОДЯЩИХ СООБЩЕНИЙ (Текст, Фото, Видео, Голосовые) ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'document'])
def handle_all_messages(message):
    user_id = message.chat.id
    if message.from_user.username:
        username_to_id[message.from_user.username.lower()] = user_id

    # 1. Если пишет АДМИНИСТРАТОР
    if user_id in admins:
        if message.reply_to_message and message.reply_to_message.forward_from:
            recipient_id = message.reply_to_message.forward_from.id
            try:
                if message.content_type == 'text':
                    bot.send_message(recipient_id, message.text)
                elif message.content_type == 'photo':
                    bot.send_photo(recipient_id, message.photo[-1].file_id, caption=message.caption)
                elif message.content_type == 'video':
                    bot.send_video(recipient_id, message.video.file_id, caption=message.caption)
                elif message.content_type == 'voice':
                    bot.send_voice(recipient_id, message.voice.file_id)
                elif message.content_type == 'document':
                    bot.send_document(recipient_id, message.document.file_id, caption=message.caption)
                
                bot.send_message(user_id, "✅ Ответ успешно доставлен пользователю!")
            except Exception as e:
                bot.send_message(user_id, f"❌ Не удалось отправить сообщение. Ошибка: {e}")
        else:
            bot.send_message(user_id, "⚠️ Чтобы ответить пользователю, зажмите его сообщение и выберите <b>'Ответить' (Reply)</b>.", parse_mode="HTML")

    # 2. Если пишет ОБЫЧНЫЙ ПОЛЬЗОВАТЕЛЬ
    else:
        state = user_states.get(user_id, 'support')
        tag = "💡 <b>[ПРЕДЛОЖЕНИЕ ПО УЛУЧШЕНИЮ]</b>" if state == 'idea' else "📩 <b>[ТЕХ. ПОДДЕРЖКА]</b>"
        
        for admin_id in admins:
            try:
                bot.send_message(admin_id, tag, parse_mode="HTML")
                bot.forward_message(admin_id, user_id, message.message_id)
            except Exception:
                pass
        
        if state == 'idea':
            bot.send_message(user_id, "💡 Ваше предложение отправлено разработчикам! Спасибо за вклад в проект.")
        else:
            bot.send_message(user_id, "📩 Ваше обращение доставлено технической поддержке! Ожидайте ответа.")
            
        user_states[user_id] = None

if __name__ == '__main__':
    bot.remove_webhook()
    print("Бот обновлен и запущен...")
    bot.infinity_polling()