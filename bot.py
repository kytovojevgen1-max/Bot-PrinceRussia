import telebot
from telebot import types

TOKEN = "8854430576:AAGDUzRNstP58pQuGIOx8hX9iKBC6YKOvPI"
SUPER_ADMIN_ID = 8543358373  # Ваш Telegram ID (Главный Владелец)

bot = telebot.TeleBot(TOKEN)

# Базы данных в памяти
admins = {SUPER_ADMIN_ID}
all_users = set()
banned_users = set()
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
        types.InlineKeyboardButton("❓ Частые Вопросы (FAQ)", callback_data="btn_faq")
    )
    kb.add(
        types.InlineKeyboardButton("📜 Правила", callback_data="btn_rules"),
        types.InlineKeyboardButton("🌐 Наши Ресурсы", callback_data="btn_links")
    )
    if user_id in admins:
        kb.add(types.InlineKeyboardButton("⚙️ Админ-Панель", callback_data="btn_admin_panel"))
    return kb

def get_links_inline_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🌐 Наш Сайт", url="https://site-prince-russia.samp.date"),
        types.InlineKeyboardButton("💬 Наш Форум", url="https://forum-prince-russia.samp.date")
    )
    kb.add(
        types.InlineKeyboardButton("📢 Telegram Канал", url="https://t.me/prince_russiaa"),
        types.InlineKeyboardButton("🔹 Сообщество VK", url="https://vk.ru/princerussiaa")
    )
    kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
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
        types.InlineKeyboardButton("🔒 Забанить юзера", callback_data="adm_ban"),
        types.InlineKeyboardButton("🔓 Разбанить юзера", callback_data="adm_unban"),
        types.InlineKeyboardButton("✉️ Сообщение по ID", callback_data="adm_send_direct"),
        types.InlineKeyboardButton("📋 Список админов", callback_data="adm_list"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🔙 Главное меню", callback_data="btn_main_menu")
    )
    return kb

def get_reply_keyboard(target_user_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Ответить пользователю", callback_data=f"reply_to_{target_user_id}"))
    return kb

# --- КОМАНДЫ БОТА ---
@bot.message_handler(commands=['start', 'menu', 'cancel'])
def start_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    user_states[user_id] = None
    admin_reply_targets[user_id] = None

    welcome_text = (
        "<b>✨ Добро пожаловать на проект Prince Russia!</b>\n"
        "───────────────────────────────\n"
        "Вы находитесь в официальном многофункциональном боте проекта.\n\n"
        "<b>Выберите нужный раздел кнопкой ниже:</b>"
    )
    bot.send_message(user_id, welcome_text, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    if user_id in admins:
        bot.send_message(user_id, "<b>⚙️ Панель управления администратора:</b>", parse_mode="HTML", reply_markup=get_admin_inline_kb())
    else:
        bot.send_message(user_id, "❌ У вас нет доступа к этой команде.")

@bot.message_handler(commands=['faq'])
def faq_cmd(message):
    user_id = message.chat.id
    show_faq(user_id)

def show_faq(user_id, message_id=None):
    faq_text = (
        "<b>❓ Частые вопросы (FAQ) — Prince Russia</b>\n"
        "───────────────────────────────\n"
        "<b>1. Как начать играть?</b>\n"
        "<i>Скачайте наш лаунчер на официальном сайте или в VK и установите его на телефон.</i>\n\n"
        "<b>2. Как восстановить пароль от аккаунта?</b>\n"
        "<i>Обратитесь в тех. поддержку через этот бот или напишите на форум в специальный раздел.</i>\n\n"
        "<b>3. Где купить донат / валюту?</b>\n"
        "<i>Используйте раздел «🛒 Донат Магазин» в меню нашего бота.</i>"
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
    if message_id:
        bot.edit_message_text(faq_text, chat_id=user_id, message_id=message_id, parse_mode="HTML", reply_markup=kb)
    else:
        bot.send_message(user_id, faq_text, parse_mode="HTML", reply_markup=kb)

# --- ОБРАБОТКА ИНЛАЙН КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    register_user(call.from_user)

    if user_id in banned_users:
        bot.answer_callback_query(call.id, "⛔️ Вы заблокированы в боте!", show_alert=True)
        return

    # Главное меню
    if call.data == "btn_main_menu":
        user_states[user_id] = None
        admin_reply_targets[user_id] = None
        welcome_text = (
            "<b>✨ Главное меню Prince Russia</b>\n"
            "───────────────────────────────\n"
            "Выберите интересующий вас раздел:"
        )
        bot.edit_message_text(welcome_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    # Донат Магазин
    elif call.data == "btn_shop":
        shop_text = (
            "<b>🛒 Донат Магазин проекта Prince Russia</b>\n"
            "───────────────────────────────\n"
            "Для покупки игровой валюты, привилегий или донат-пакетов обращайтесь к администрации:\n\n"
            "🔹 <b>Telegram:</b> @AsikWhiskey\n"
            "🔹 <b>ВКонтакте:</b> https://vk.com/asik_whiskey\n\n"
            "⚠️ <i>Покупки совершаются только через официальные контакты!</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_main_menu"))
        bot.edit_message_text(shop_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)

    # Правила
    elif call.data == "btn_rules":
        rules_text = (
            "<b>📜 Правила проекта Prince Russia</b>\n"
            "───────────────────────────────\n"
            "1. Запрещено оскорбление игроков и администрации.\n"
            "2. Запрещено использование стороннего ПО (читов/скриптов).\n"
            "3. Запрещен спам и реклама сторонних ресурсов в боте.\n"
            "4. Совершая покупки, вы соглашаетесь с условиями проекта.\n\n"
            "Полный свод правил читайте на нашем форуме!"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Форум правил", url="https://forum-prince-russia.samp.date"))
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(rules_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    # FAQ
    elif call.data == "btn_faq":
        show_faq(user_id, call.message.message_id)

    # Ресурсы
    elif call.data == "btn_links":
        links_text = (
            "<b>🌐 Официальные ресурсы Prince Russia</b>\n"
            "───────────────────────────────\n"
            "Присоединяйтесь к нашим сообществам и будьте в курсе всех новостей проекта:"
        )
        bot.edit_message_text(links_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_links_inline_kb())

    # Предложения
    elif call.data == "btn_idea":
        user_states[user_id] = 'idea'
        text = (
            "<b>💡 Раздел предложений и улучшений</b>\n"
            "───────────────────────────────\n"
            "Напишите ваше предложение или идею прямо сейчас (можно прикрепить фото или видео):"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Поддержка
    elif call.data == "btn_support":
        user_states[user_id] = 'support'
        text = (
            "<b>🛠 Техническая поддержка</b>\n"
            "───────────────────────────────\n"
            "Опишите вашу проблему или задайте вопрос сообщением ниже. Наша команда ответит вам!"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Отмена
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

    # Ответ пользователю
    elif call.data.startswith("reply_to_"):
        if user_id not in admins:
            bot.answer_callback_query(call.id, "У вас нет прав!", show_alert=True)
            return
        target_id = int(call.data.replace("reply_to_", ""))
        admin_reply_targets[user_id] = target_id
        bot.send_message(user_id, f"📝 <b>Введите ответ для пользователя (ID: <code>{target_id}</code>):</b>\n<i>Пользователь увидит ваш юзернейм при ответе.</i>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Админские фичи
    elif call.data == "adm_stats":
        if user_id in admins:
            text = (
                "<b>📊 Статистика проекта Prince Russia:</b>\n"
                "───────────────────────────────\n"
                f"👤 Всего пользователей: <b>{len(all_users)}</b>\n"
                f"🛠 Администраторов: <b>{len(admins)}</b>\n"
                f"🚫 В бане: <b>{len(banned_users)}</b>"
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

    elif call.data == "adm_ban":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите @username или ID пользователя для блокировки в боте:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "adm_unban":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите @username или ID пользователя для разблокировки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "adm_send_direct":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите Telegram ID пользователя, которому хотите написать лично:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_direct_msg_id)

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
            msg = bot.send_message(user_id, "Отправьте пост/сообщение для массовой рассылки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_broadcast)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def process_add_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        admins.add(target_id)
        bot.send_message(message.chat.id, f"✅ Пользователь <code>{target_id}</code> назначен администратором!", parse_mode="HTML")
        try:
            bot.send_message(target_id, "🎉 <b>Вам выданы права администратора Prince Russia!</b>\nНажмите /menu для доступа.", parse_mode="HTML")
        except Exception: pass
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден. Он должен запустить бота через /start.")

def process_remove_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
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

def process_ban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        if target_id in admins:
            bot.send_message(message.chat.id, "❌ Нельзя заблокировать администратора!")
            return
        banned_users.add(target_id)
        bot.send_message(message.chat.id, f"⛔️ Пользователь <code>{target_id}</code> заблокирован в боте.", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def process_unban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id in banned_users:
        banned_users.remove(target_id)
        bot.send_message(message.chat.id, f"✅ Пользователь <code>{target_id}</code> разблокирован.", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден в списке забаненных.")

def process_direct_msg_id(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    if message.text.isdigit():
        target_id = int(message.text)
        admin_reply_targets[message.chat.id] = target_id
        msg = bot.send_message(message.chat.id, f"📝 Напишите сообщение, которое сразу уйдёт пользователю <code>{target_id}</code>:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
    else:
        bot.send_message(message.chat.id, "❌ Введите корректный числовой Telegram ID.")

def process_broadcast(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    count = 0
    for uid in list(all_users):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except Exception: pass
    bot.send_message(message.chat.id, f"📢 <b>Рассылка завершена!</b>\nУспешно доставлено: {count}/{len(all_users)} пользователей.", parse_mode="HTML")

# --- ОБРАБОТКА ВХОДЯЩИХ СООБЩЕНИЙ ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'sticker'])
def handle_all_messages(message):
    user_id = message.chat.id
    register_user(message.from_user)

    if user_id in banned_users:
        bot.send_message(user_id, "⛔️ Вы заблокированы в боте и не можете отправлять сообщения.")
        return

    state = user_states.get(user_id)
    is_replying = user_id in admins and admin_reply_targets.get(user_id)

    # 1. Если АДМИН отвечает пользователю
    if is_replying:
        target_id = admin_reply_targets[user_id]
        
        # Формируем подпись с указанием юзернейма админа
        admin_username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        role_label = "👑 Владелец проекта" if user_id == SUPER_ADMIN_ID else "🛡 Администратор"
        
        header_text = f"<b>{role_label} ({admin_username}) ответил на ваше обращение:</b>\n"
        
        try:
            bot.send_message(target_id, header_text, parse_mode="HTML")
            bot.copy_message(target_id, message.chat.id, message.message_id)
            bot.send_message(user_id, f"✅ <b>Ответ успешно отправлен пользователю <code>{target_id}</code>!</b>", parse_mode="HTML")
            admin_reply_targets[user_id] = None
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка отправки: {e}")
        return

    # 2. Если ПОЛЬЗОВАТЕЛЬ в режиме ввода обращения/идеи
    elif state in ['idea', 'support']:
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

        # Отправляем карточку админам
        for admin_id in admins:
            try:
                bot.send_message(admin_id, card_header, parse_mode="HTML")
                bot.copy_message(admin_id, user_id, message.message_id, reply_markup=get_reply_keyboard(user_id))
            except Exception: pass

        if state == 'idea':
            bot.send_message(user_id, "💡 <b>Спасибо!</b> Ваша идея принята и передана разработчикам.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        else:
            bot.send_message(user_id, "📩 <b>Ваше обращение доставлено!</b> Ожидайте ответа от администрации.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

        user_states[user_id] = None

    # 3. Обычное сообщение вне режима ввода
    else:
        bot.send_message(
            user_id, 
            "ℹ️ Воспользуйтесь меню ниже для взаимодействия с ботом:", 
            reply_markup=get_main_inline_kb(user_id)
        )

if __name__ == '__main__':
    bot.remove_webhook()
    print("Бот Prince Russia с функцией юзернеймов запущен...")
    bot.infinity_polling()