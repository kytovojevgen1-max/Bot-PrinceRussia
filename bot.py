import telebot
from telebot import types

TOKEN = "8854430576:AAGDUzRNstP58pQuGIOx8hX9iKBC6YKOvPI"
SUPER_ADMIN_ID = 8543358373  # Ваш Telegram ID (Главный Владелец)

bot = telebot.TeleBot(TOKEN)

# Базы данных в памяти
admins = {SUPER_ADMIN_ID}
all_users = set()
username_to_id = {}
user_states = {}
admin_reply_targets = {}  # admin_id -> target_user_id

# --- СЛУЖЕБНЫЕ ФУНКЦИИ ---
def register_user(user):
    all_users.add(user.id)
    if user.username:
        username_to_id[user.username.lower()] = user.id

# --- ИНЛАЙН КЛАВИАТУРЫ ---
def get_main_inline_kb(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🛒 Донат Магазин", callback_data="btn_shop"),
        types.InlineKeyboardButton("💡 Предложить идею", callback_data="btn_idea")
    )
    kb.add(
        types.InlineKeyboardButton("🛠 Тех. Поддержка", callback_data="btn_support"),
        types.InlineKeyboardButton("ℹ️ О проекте", callback_data="btn_info")
    )
    if user_id in admins:
        kb.add(types.InlineKeyboardButton("⚙️ Админ-Панель", callback_data="btn_admin_panel"))
    return kb

def get_cancel_inline_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Отмена", callback_data="btn_cancel"))
    return kb

def get_admin_inline_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Добавить админа", callback_data="adm_add"),
        types.InlineKeyboardButton("➖ Удалить админа", callback_data="adm_remove"),
        types.InlineKeyboardButton("📋 Список админов", callback_data="adm_list"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🔙 В главное меню", callback_data="btn_main_menu")
    )
    return kb

def get_reply_keyboard(target_user_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Ответить пользователю", callback_data=f"reply_to_{target_user_id}"))
    return kb

# --- КОМАНДЫ /START И /CANCEL ---
@bot.message_handler(commands=['start', 'cancel'])
def start_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    user_states[user_id] = None
    admin_reply_targets[user_id] = None

    welcome_text = (
        "<b>✨ Добро пожаловать на проект Prince Russia!</b>\n"
        "───────────────────────────────\n"
        "Вы находитесь в официальном боте поддержки и сервисов проекта.\n\n"
        "<b>Выберите нужный раздел ниже:</b>"
    )
    bot.send_message(user_id, welcome_text, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

# --- ОБРАБОТКА ВСЕХ INLINE-КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    register_user(call.from_user)

    # Главное меню
    if call.data == "btn_main_menu":
        user_states[user_id] = None
        welcome_text = (
            "<b>✨ Главное меню Prince Russia</b>\n"
            "───────────────────────────────\n"
            "Выберите интересующий вас раздел:"
        )
        bot.edit_message_text(welcome_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    # Донат магазин
    elif call.data == "btn_shop":
        shop_text = (
            "<b>🛒 Донат Магазин проекта Prince Russia</b>\n"
            "───────────────────────────────\n"
            "Для покупки игровой валюты, привилегий или донат-пакетов обращайтесь к ручной администрации:\n\n"
            "🔹 <b>Telegram:</b> @AsikWhiskey\n"
            "🔹 <b>ВКонтакте:</b> https://vk.com/asik_whiskey\n\n"
            "⚠️ <i>Покупки совершаются только через официальные контакты!</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_main_menu"))
        bot.edit_message_text(shop_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)

    # Идеи / Улучшения
    elif call.data == "btn_idea":
        user_states[user_id] = 'idea'
        text = (
            "<b>💡 Раздел предложений и улучшений</b>\n"
            "───────────────────────────────\n"
            "Напишите ваше предложение или идею для проекта. Вы можете прикрепить скриншоты или видео:"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Поддержка
    elif call.data == "btn_support":
        user_states[user_id] = 'support'
        text = (
            "<b>🛠 Техническая поддержка</b>\n"
            "───────────────────────────────\n"
            "Подробно опишите вашу проблему или задайте вопрос. Наша команда ответит вам в ближайшее время!"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Инфо
    elif call.data == "btn_info":
        text = (
            "<b>ℹ️ Информация о проекте</b>\n"
            "───────────────────────────────\n"
            "👑 <b>Проект:</b> Prince Russia\n"
            "🤖 <b>Версия бота:</b> 3.0 Ultra\n"
            "⚡️ <b>Режим работы:</b> 24/7 Онлайн"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_main_menu"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    # Отмена действия
    elif call.data == "btn_cancel":
        user_states[user_id] = None
        admin_reply_targets[user_id] = None
        bot.answer_callback_query(call.id, "Действие отменено.")
        bot.edit_message_text("<b>Действие отменено.</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    # Админ Панель
    elif call.data == "btn_admin_panel":
        if user_id in admins:
            bot.edit_message_text("<b>⚙️ Панель управления администратора:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb())
        else:
            bot.answer_callback_query(call.id, "Доступ запрещен!", show_alert=True)

    # Кнопка ответа для админов
    elif call.data.startswith("reply_to_"):
        if user_id not in admins:
            bot.answer_callback_query(call.id, "У вас нет прав админа!", show_alert=True)
            return
        target_id = int(call.data.replace("reply_to_", ""))
        admin_reply_targets[user_id] = target_id
        bot.send_message(user_id, f"📝 <b>Впишите ответ пользователю (ID: <code>{target_id}</code>):</b>\n<i>Ответ уйдет анонимно от имени бота.</i>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Админские функции
    elif call.data == "adm_stats":
        if user_id in admins:
            text = (
                "<b>📊 Статистика проекта Prince Russia:</b>\n"
                "───────────────────────────────\n"
                f"👤 Всего пользователей: <b>{len(all_users)}</b>\n"
                f"🛠 Администраторов: <b>{len(admins)}</b>"
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 В админ-панель", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_add":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите @username или Telegram ID нового админа:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "adm_remove":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите @username или Telegram ID для снятия админки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data == "adm_list":
        if user_id in admins:
            text = f"<b>📋 Список администраторов ({len(admins)}):</b>\n\n"
            for adm in admins:
                role = "👑 Владелец" if adm == SUPER_ADMIN_ID else "🛠 Админ"
                text += f"• ID: <code>{adm}</code> ({role})\n"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 В админ-панель", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_broadcast":
        if user_id in admins:
            msg = bot.send_message(user_id, "Отправьте сообщение/пост для массовой рассылки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_broadcast)

# --- ВПОМОГАТЕЛЬНЫЕ ФУНКЦИИ АДМИНКИ ---
def process_add_admin(message):
    if message.text == "❌ Отмена": return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        admins.add(target_id)
        bot.send_message(message.chat.id, f"✅ Пользователь <code>{target_id}</code> назначен администратором!", parse_mode="HTML")
        try:
            bot.send_message(target_id, "🎉 <b>Вам выданы права администратора Prince Russia!</b>\nНажмите /start для обновления доступа.", parse_mode="HTML")
        except Exception: pass
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден. Он должен запустить бота через /start.")

def process_remove_admin(message):
    if message.text == "❌ Отмена": return
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
    if message.text == "❌ Отмена": return
    count = 0
    for uid in list(all_users):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except Exception: pass
    bot.send_message(message.chat.id, f"📢 <b>Рассылка завершена!</b>\nУспешно доставлено: {count}/{len(all_users)} пользователей.", parse_mode="HTML")

# --- ОБРАБОТКА ВСЕХ СООБЩЕНИЙ ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'sticker'])
def handle_all_messages(message):
    user_id = message.chat.id
    register_user(message.from_user)

    # 1. Если АДМИН в режиме ответа
    if user_id in admins and admin_reply_targets.get(user_id):
        target_id = admin_reply_targets[user_id]
        try:
            bot.copy_message(target_id, message.chat.id, message.message_id)
            bot.send_message(user_id, "✅ <b>Ответ успешно отправлен пользователю от имени бота!</b>", parse_mode="HTML")
            admin_reply_targets[user_id] = None
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка отправки: {e}")
        return

    # 2. Если пишет ОБЫЧНЫЙ ПОЛЬЗОВАТЕЛЬ
    if user_id not in admins or (user_id in admins and not admin_reply_targets.get(user_id)):
        state = user_states.get(user_id, 'support')
        
        user_info = f"👤 <b>От:</b> {message.from_user.first_name}"
        if message.from_user.username:
            user_info += f" (@{message.from_user.username})\n"
        else:
            user_info += "\n"
        user_info += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"

        if state == 'idea':
            card_header = "💡 <b>[НОВОЕ ПРЕДЛОЖЕНИЕ ПО УЛУЧШЕНИЮ]</b>\n" + user_info
        else:
            card_header = "🛠 <b>[ОБРАЩЕНИЕ В ТЕХ. ПОДДЕРЖКУ]</b>\n" + user_info

        # Отправка админам
        for admin_id in admins:
            try:
                bot.send_message(admin_id, card_header, parse_mode="HTML")
                bot.copy_message(admin_id, user_id, message.message_id, reply_markup=get_reply_keyboard(user_id))
            except Exception: pass

        if state == 'idea':
            bot.send_message(user_id, "💡 <b>Спасибо!</b> Ваша идея отправлена разработчикам.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        else:
            bot.send_message(user_id, "📩 <b>Ваше сообщение доставлено!</b> Ожидайте ответа от администрации.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

        user_states[user_id] = None

if __name__ == '__main__':
    bot.remove_webhook()
    print("Бот Prince Russia 3.0 Ultra запущен...")
    bot.infinity_polling()