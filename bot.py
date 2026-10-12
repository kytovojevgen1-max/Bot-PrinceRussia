import telebot
from telebot import types

TOKEN = "8854430576:AAGDUzRNstP58pQuGIOx8hX9iKBC6YKOvPI"
SUPER_ADMIN_ID = 8543358373  # Ваш Telegram ID (Главный Владелец)

bot = telebot.TeleBot(TOKEN)

# База данных в памяти
admins = {SUPER_ADMIN_ID}
all_users = set()  # Все пользователи для рассылки
username_to_id = {}
user_states = {}
reply_mapping = {}  # Связка: ID сообщения админа -> ID пользователя

# --- КЛАВИАТУРЫ ---
def get_main_keyboard(user_id):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("🛒 Донат Магазин")
    kb.row("💡 Предложить идею", "🛠 Поддержка / Вопрос")
    if user_id in admins:
        kb.row("⚙️ Админ-панель")
    return kb

def get_cancel_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("❌ Отмена")
    return kb

def get_admin_keyboard():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Добавить админа", callback_data="add_admin"),
        types.InlineKeyboardButton("➖ Удалить админа", callback_data="remove_admin"),
        types.InlineKeyboardButton("📋 Список админов", callback_data="list_admins"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="stats"),
        types.InlineKeyboardButton("📢 Рассылка новостей", callback_data="broadcast")
    )
    return kb

# --- СЛУЖЕБНЫЕ ФУНКЦИИ ---
def register_user(user):
    all_users.add(user.id)
    if user.username:
        username_to_id[user.username.lower()] = user.id

# --- КОМАНДА /START И /CANCEL ---
@bot.message_handler(commands=['start', 'cancel'])
def start_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    user_states[user_id] = None

    welcome_text = (
        "<b>👑 Добро пожаловать на проект Prince Russia!</b>\n\n"
        "Воспользуйтесь меню ниже для работы с ботом:\n\n"
        "🛒 <b>Донат Магазин</b> — покупка привилегий и валюты\n"
        "💡 <b>Предложить идею</b> — ваши предложения по улучшению\n"
        "🛠 <b>Поддержка / Вопрос</b> — задать вопрос администрации"
    )
    bot.send_message(user_id, welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard(user_id))

# --- ОБРАБОТКА МЕНЮ ---
@bot.message_handler(func=lambda msg: msg.text in ["🛒 Донат Магазин", "💡 Предложить идею", "🛠 Поддержка / Вопрос", "⚙️ Админ-панель", "❌ Отмена"])
def menu_handler(message):
    user_id = message.chat.id
    register_user(message.from_user)

    if message.text == "❌ Отмена":
        user_states[user_id] = None
        bot.send_message(user_id, "Главное меню:", reply_markup=get_main_keyboard(user_id))
        return

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
            "Опишите вашу идею или добавление на проект (текст, фото, видео или документ):", 
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )

    elif message.text == "🛠 Поддержка / Вопрос":
        user_states[user_id] = 'support'
        bot.send_message(
            user_id, 
            "<b>🛠 Техническая поддержка</b>\n\n"
            "Опишите вашу проблему или задайте вопрос (принимаются сообщения, фото, видео и голосовые):", 
            parse_mode="HTML",
            reply_markup=get_cancel_keyboard()
        )

    elif message.text == "⚙️ Админ-панель":
        if user_id in admins:
            bot.send_message(user_id, "<b>⚙️ Панель управления администратора:</b>", parse_mode="HTML", reply_markup=get_admin_keyboard())
        else:
            bot.send_message(user_id, "У вас нет доступа к панели администратора.")

# --- CALLBACKS АДМИН-ПАНЕЛИ ---
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = call.message.chat.id
    if user_id not in admins:
        bot.answer_callback_query(call.id, "У вас нет доступа!", show_alert=True)
        return

    if call.data == "add_admin":
        msg = bot.send_message(user_id, "Введите @username или Telegram ID пользователя, которому хотите выдать админку:")
        bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "remove_admin":
        msg = bot.send_message(user_id, "Введите @username или Telegram ID пользователя для снятия админки:")
        bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data == "list_admins":
        text = f"<b>📋 Список администраторов ({len(admins)}):</b>\n\n"
        for adm in admins:
            role = "👑 Владелец" if adm == SUPER_ADMIN_ID else "🛠 Админ"
            text += f"• ID: <code>{adm}</code> ({role})\n"
        bot.send_message(user_id, text, parse_mode="HTML")

    elif call.data == "stats":
        text = (
            "<b>📊 Статистика бота:</b>\n\n"
            f"👤 всего пользователей: <b>{len(all_users)}</b>\n"
            f"🛠 Администраторов: <b>{len(admins)}</b>"
        )
        bot.send_message(user_id, text, parse_mode="HTML")

    elif call.data == "broadcast":
        msg = bot.send_message(user_id, "Введите текст/сообщение для рассылки ВСЕМ пользователям бота:")
        bot.register_next_step_handler(msg, process_broadcast)

def process_add_admin(message):
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        admins.add(target_id)
        bot.send_message(message.chat.id, f"✅ Пользователь <code>{target_id}</code> добавлен в админы!", parse_mode="HTML")
        try:
            bot.send_message(target_id, "🎉 Вам выданы права администратора! Нажмите /start для обновления меню.")
        except Exception:
            pass
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден. Он должен хотя бы один раз написать боту /start.")

def process_remove_admin(message):
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        if target_id == SUPER_ADMIN_ID:
            bot.send_message(message.chat.id, "❌ Нельзя снять права у Главного Владельца!")
            return
        admins.discard(target_id)
        bot.send_message(message.chat.id, f"✅ Права администратора у <code>{target_id}</code> успешно сняты.", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def process_broadcast(message):
    count = 0
    for uid in list(all_users):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"📢 Рассылка завершена! Доставлено пользователям: {count}/{len(all_users)}")

# --- ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'sticker'])
def handle_all_messages(message):
    user_id = message.chat.id
    register_user(message.from_user)

    # 1. ОБРАБОТКА ОТВЕТА АДМИНИСТРАТОРА (ОТ ИМЕНИ БОТА)
    if user_id in admins:
        if message.reply_to_message:
            reply_msg_id = message.reply_to_message.message_id
            target_user_id = reply_mapping.get(reply_msg_id) or (
                message.reply_to_message.forward_from.id if message.reply_to_message.forward_from else None
            )

            if target_user_id:
                try:
                    # Пересылаем точную копию от имени бота
                    bot.copy_message(target_user_id, message.chat.id, message.message_id)
                    bot.send_message(user_id, "✅ <b>Ответ успешно отправлен от имени бота!</b>", parse_mode="HTML")
                except Exception as e:
                    bot.send_message(user_id, f"❌ Ошибка отправки: {e}. Возможно, пользователь заблокировал бота.")
            else:
                bot.send_message(user_id, "⚠️ Не удалось определить получателя.")
        else:
            bot.send_message(user_id, "ℹ️ Используйте кнопку <b>'Ответить' (Reply)</b> на карточку сообщения, чтобы отправить ответ пользователю.", parse_mode="HTML")

    # 2. ОБРАБОТКА СООБЩЕНИЙ ОТ ОБЫЧНЫХ ПОЛЬЗОВАТЕЛЕЙ
    else:
        state = user_states.get(user_id, 'support')
        user_info = f"👤 <b>От:</b> {message.from_user.first_name} "
        if message.from_user.username:
            user_info += f"(@{message.from_user.username})\n"
        else:
            user_info += f"\n"
        user_info += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"

        if state == 'idea':
            card_header = "💡 <b>[НОВОЕ ПРЕДЛОЖЕНИЕ ПО УЛУЧШЕНИЮ]</b>\n" + user_info
        else:
            card_header = "🛠 <b>[ОБРАЩЕНИЕ В ТЕХ. ПОДДЕРЖКУ]</b>\n" + user_info

        for admin_id in admins:
            try:
                # Отправляем инфо-карточку
                card = bot.send_message(admin_id, card_header, parse_mode="HTML")
                # Копируем само сообщение пользователя
                fwd = bot.copy_message(admin_id, user_id, message.message_id)
                # Сохраняем связку для ответа
                reply_mapping[fwd.message_id] = user_id
                reply_mapping[card.message_id] = user_id
            except Exception:
                pass

        if state == 'idea':
            bot.send_message(user_id, "💡 Ваше предложение отправлено! Спасибо за вклад в проект Prince Russia.", reply_markup=get_main_keyboard(user_id))
        else:
            bot.send_message(user_id, "📩 Сообщение доставлено администрации! Ожидайте ответа в этом чате.", reply_markup=get_main_keyboard(user_id))

        user_states[user_id] = None

if __name__ == '__main__':
    bot.remove_webhook()
    print("Продвинутый бот Prince Russia запущен...")
    bot.infinity_polling()