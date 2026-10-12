import telebot
from telebot import types
import random

TOKEN = "8854430576:AAGDUzRNstP58pQuGIOx8hX9iKBC6YKOvPI"
DEV_ID = 8543358373  # Ваш Telegram ID (Разработчик)

bot = telebot.TeleBot(TOKEN)

# --- БАЗЫ ДАННЫХ В ПАМЯТИ ---
admins = {DEV_ID}
admin_prefixes = {DEV_ID: "👑 Разработчик"}
all_users = set()
banned_users = set()
username_to_id = {}
user_states = {}
admin_reply_targets = {}  # admin_id -> target_user_id
user_last_messages = {}   # user_id -> dict with 'type', 'text'
games = {}                # user_id -> secret_number

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
        types.InlineKeyboardButton("🎮 Мини-Игра", callback_data="btn_game")
    )
    kb.add(
        types.InlineKeyboardButton("❓ FAQ / Вопросы", callback_data="btn_faq"),
        types.InlineKeyboardButton("📜 Правила", callback_data="btn_rules")
    )
    kb.add(
        types.InlineKeyboardButton("🌐 Наши Ресурсы", callback_data="btn_links")
    )
    if user_id in admins:
        kb.add(types.InlineKeyboardButton("⚙️ Панель Разработчика / Админа", callback_data="btn_admin_panel"))
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

def get_admin_inline_kb(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("➕ Добавить админа", callback_data="adm_add"),
        types.InlineKeyboardButton("➖ Удалить админа", callback_data="adm_remove"),
        types.InlineKeyboardButton("🏷 Выдать префикс", callback_data="adm_prefix"),
        types.InlineKeyboardButton("🔒 Забанить", callback_data="adm_ban"),
        types.InlineKeyboardButton("🔓 Разбанить", callback_data="adm_unban"),
        types.InlineKeyboardButton("✉️ Написать по ID", callback_data="adm_send_direct"),
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
        "Официальный многофункциональный бот поддержки и сервисов проекта.\n\n"
        "<b>Выберите нужный раздел кнопкой ниже:</b>"
    )
    bot.send_message(user_id, welcome_text, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

@bot.message_handler(commands=['admin', 'dev'])
def admin_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    if user_id in admins:
        bot.send_message(user_id, "<b>⚙️ Панель Управления:</b>", parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
    else:
        bot.send_message(user_id, "❌ У вас нет доступа к этой команде.")

@bot.message_handler(commands=['game'])
def game_cmd(message):
    user_id = message.chat.id
    start_game(user_id)

def start_game(user_id, message_id=None):
    secret = random.randint(1, 10)
    games[user_id] = secret
    user_states[user_id] = 'playing_game'

    text = (
        "<b>🎮 Мини-Игра «Угадай число»!</b>\n"
        "───────────────────────────────\n"
        "Я загадал число от <b>1 до 10</b>.\n"
        "Попробуй угадать его! Напиши число прямо в чат:"
    )
    kb = get_cancel_inline_kb()
    if message_id:
        bot.edit_message_text(text, chat_id=user_id, message_id=message_id, parse_mode="HTML", reply_markup=kb)
    else:
        bot.send_message(user_id, text, parse_mode="HTML", reply_markup=kb)

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
            "Для покупки игровой валюты, привилегий или донат-пакетов обращайтесь к руководству:\n\n"
            "🔹 <b>Telegram:</b> @AsikWhiskey\n"
            "🔹 <b>ВКонтакте:</b> https://vk.com/asik_whiskey\n\n"
            "⚠️ <i>Покупки совершаются только через официальные контакты!</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_main_menu"))
        bot.edit_message_text(shop_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)

    # Игра
    elif call.data == "btn_game":
        start_game(user_id, call.message.message_id)

    # Правила
    elif call.data == "btn_rules":
        rules_text = (
            "<b>📜 Правила проекта Prince Russia</b>\n"
            "───────────────────────────────\n"
            "1. Запрещено оскорбление игроков и администрации.\n"
            "2. Запрещено использование читов и сторонних скриптов.\n"
            "3. Запрещен спам и реклама в боте.\n"
            "4. Совершая покупки, вы соглашаетесь с правилами сервера."
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Форум Правил", url="https://forum-prince-russia.samp.date"))
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(rules_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    # FAQ
    elif call.data == "btn_faq":
        faq_text = (
            "<b>❓ Частые вопросы (FAQ) — Prince Russia</b>\n"
            "───────────────────────────────\n"
            "<b>1. Как начать играть?</b>\n"
            "<i>Скачайте лаунчер на сайте или в VK и установите его.</i>\n\n"
            "<b>2. Как восстановить аккаунт?</b>\n"
            "<i>Обратитесь в тех. поддержку через этого бота.</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(faq_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    # Ресурсы
    elif call.data == "btn_links":
        links_text = (
            "<b>🌐 Официальные ресурсы Prince Russia</b>\n"
            "───────────────────────────────\n"
            "Присоединяйтесь к нашим сообществам:"
        )
        bot.edit_message_text(links_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_links_inline_kb())

    # Предложения
    elif call.data == "btn_idea":
        user_states[user_id] = 'idea'
        text = (
            "<b>💡 Раздел предложений и улучшений</b>\n"
            "───────────────────────────────\n"
            "Напишите вашу идею прямо сейчас (можно прикрепить фото или видео):"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Поддержка
    elif call.data == "btn_support":
        user_states[user_id] = 'support'
        text = (
            "<b>🛠 Техническая поддержка</b>\n"
            "───────────────────────────────\n"
            "Опишите вашу проблему или вопрос. Вы можете отправить текст, фото или видео!"
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
            bot.edit_message_text("<b>⚙️ Панель Управления:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
        else:
            bot.answer_callback_query(call.id, "Доступ запрещен!", show_alert=True)

    # Ответ пользователю
    elif call.data.startswith("reply_to_"):
        if user_id not in admins:
            bot.answer_callback_query(call.id, "У вас нет прав!", show_alert=True)
            return
        target_id = int(call.data.replace("reply_to_", ""))
        admin_reply_targets[user_id] = target_id
        bot.send_message(user_id, f"📝 <b>Введите ответ пользователю (ID: <code>{target_id}</code>):</b>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Админские функции
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
            kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_add":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите @username или Telegram ID нового админа:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "adm_remove":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите @username или ID для снятия админки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data == "adm_prefix":
        if user_id == DEV_ID:
            msg = bot.send_message(user_id, "Введите ID или @username админа и через пробел префикс.\nПример: <code>@username [Гл. Администратор]</code>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_set_prefix)
        else:
            bot.answer_callback_query(call.id, "Только Разработчик может изменять префиксы!", show_alert=True)

    elif call.data == "adm_ban":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите @username или ID для блокировки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "adm_unban":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите @username или ID для разблокировки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "adm_send_direct":
        if user_id in admins:
            msg = bot.send_message(user_id, "Введите Telegram ID пользователя для прямого сообщения:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_direct_msg_id)

    elif call.data == "adm_list":
        if user_id in admins:
            text = f"<b>📋 Список администраторов ({len(admins)}):</b>\n\n"
            for adm in admins:
                prefix = admin_prefixes.get(adm, "🛠 Администратор")
                text += f"• ID: <code>{adm}</code> — <b>{prefix}</b>\n"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_broadcast":
        if user_id in admins:
            msg = bot.send_message(user_id, "Отправьте пост для массовой рассылки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_broadcast)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ АДМИНКИ ---
def process_add_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        admins.add(target_id)
        admin_prefixes[target_id] = "🛠 Администратор"
        bot.send_message(message.chat.id, f"✅ Пользователь <code>{target_id}</code> назначен администратором!", parse_mode="HTML")
        try:
            bot.send_message(target_id, "🎉 <b>Вам выданы права администратора Prince Russia!</b>\nНажмите /menu для работы.", parse_mode="HTML")
        except Exception: pass
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def process_remove_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        if target_id == DEV_ID:
            bot.send_message(message.chat.id, "❌ Нельзя снять права у Разработчика!")
            return
        admins.discard(target_id)
        admin_prefixes.pop(target_id, None)
        bot.send_message(message.chat.id, f"✅ Права у <code>{target_id}</code> сняты.", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def process_set_prefix(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    try:
        parts = message.text.strip().split(" ", 1)
        user_str = parts[0].replace("@", "").lower()
        new_prefix = parts[1]
        target_id = username_to_id.get(user_str) or (int(user_str) if user_str.isdigit() else None)

        if target_id and target_id in admins:
            admin_prefixes[target_id] = new_prefix
            bot.send_message(message.chat.id, f"✅ Для админа <code>{target_id}</code> установлен префикс: <b>{new_prefix}</b>", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден среди администраторов.")
    except Exception:
        bot.send_message(message.chat.id, "❌ Неверный формат! Вводите так: <code>@username [Префикс]</code>", parse_mode="HTML")

def process_ban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = username_to_id.get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        if target_id in admins:
            bot.send_message(message.chat.id, "❌ Нельзя заблокировать администратора!")
            return
        banned_users.add(target_id)
        bot.send_message(message.chat.id, f"⛔️ Пользователь <code>{target_id}</code> заблокирован.", parse_mode="HTML")
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
        bot.send_message(message.chat.id, "❌ Пользователь не найден в забаненных.")

def process_direct_msg_id(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    if message.text.isdigit():
        target_id = int(message.text)
        admin_reply_targets[message.chat.id] = target_id
        bot.send_message(message.chat.id, f"📝 Напишите сообщение для пользователя <code>{target_id}</code>:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
    else:
        bot.send_message(message.chat.id, "❌ Введите числовой Telegram ID.")

def process_broadcast(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    count = 0
    for uid in list(all_users):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except Exception: pass
    bot.send_message(message.chat.id, f"📢 <b>Рассылка завершена!</b>\nДоставлено: {count}/{len(all_users)}", parse_mode="HTML")

# --- ОБРАБОТКА ВХОДЯЩИХ СООБЩЕНИЙ ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'voice', 'video_note', 'document', 'sticker'])
def handle_all_messages(message):
    user_id = message.chat.id
    register_user(message.from_user)

    if user_id in banned_users:
        bot.send_message(user_id, "⛔️ Вы заблокированы в боте.")
        return

    state = user_states.get(user_id)
    is_replying = user_id in admins and admin_reply_targets.get(user_id)

    # 🎮 Мини-игра «Угадай число»
    if state == 'playing_game' and message.content_type == 'text':
        if message.text.isdigit():
            val = int(message.text)
            secret = games.get(user_id, 5)
            if val == secret:
                bot.send_message(user_id, f"🎉 <b>ПОЗДРАВЛЯЕМ!</b> Вы угадали число {secret}!", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
                user_states[user_id] = None
            elif val < secret:
                bot.send_message(user_id, "📉 Мое число <b>БОЛЬШЕ</b>! Попробуй еще раз:", parse_mode="HTML")
            else:
                bot.send_message(user_id, "📈 Мое число <b>МЕНЬШЕ</b>! Попробуй еще раз:", parse_mode="HTML")
        return

    # 1. Если АДМИН отвечает пользователю (с красочным цитированием!)
    if is_replying:
        target_id = admin_reply_targets[user_id]
        
        prefix = admin_prefixes.get(user_id, "🛡 Администратор")
        admin_uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

        # Формируем цитирование предыдущего обращения
        last_info = user_last_messages.get(target_id, {})
        m_type = last_info.get('type', 'сообщение')
        m_text = last_info.get('text', 'Прикрепленный медиафайл')

        quote_box = (
            f"<b>{prefix} ({admin_uname}) ответил на ваше {m_type}:</b>\n"
            f"───────────────────────────────\n"
            f"💬 <i>Ваше {m_type}:</i> «{m_text}»\n"
            f"───────────────────────────────\n"
            f"✍️ <b>Ответ:</b>\n"
        )
        
        try:
            bot.send_message(target_id, quote_box, parse_mode="HTML")
            bot.copy_message(target_id, message.chat.id, message.message_id)
            bot.send_message(user_id, f"✅ <b>Ответ успешно доставлен пользователю <code>{target_id}</code>!</b>", parse_mode="HTML")
            admin_reply_targets[user_id] = None
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка отправки: {e}")
        return

    # 2. Если ПОЛЬЗОВАТЕЛЬ отправляет идею или обращение
    elif state in ['idea', 'support']:
        msg_type_str = "предложение" if state == 'idea' else "обращение"
        msg_text_str = message.text or message.caption or f"[{message.content_type.upper()}]"

        # Сохраняем в память для цитирования
        user_last_messages[user_id] = {
            'type': msg_type_str,
            'text': msg_text_str
        }

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

        # Рассылка карточки админам
        for admin_id in admins:
            try:
                bot.send_message(admin_id, card_header, parse_mode="HTML")
                bot.copy_message(admin_id, user_id, message.message_id, reply_markup=get_reply_keyboard(user_id))
            except Exception: pass

        if state == 'idea':
            bot.send_message(user_id, "💡 <b>Спасибо!</b> Ваша идея передана разработчикам.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        else:
            bot.send_message(user_id, "📩 <b>Ваше обращение доставлено!</b> Ожидайте ответа от администрации.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

        user_states[user_id] = None

    # 3. Обычное сообщение
    else:
        bot.send_message(
            user_id, 
            "ℹ️ Воспользуйтесь меню ниже для взаимодействия с ботом:", 
            reply_markup=get_main_inline_kb(user_id)
        )

if __name__ == '__main__':
    bot.remove_webhook()
    print("Бот Prince Russia 4.0 Ultra (Разработчик) запущен...")
    bot.infinity_polling()