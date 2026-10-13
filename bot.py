import telebot
from telebot import types
import random
import json
import os
import time
from flask import Flask
from threading import Thread

TOKEN = "8854430576:AAFmXNrlGrJSfbxMSINFC8tQkX-NVbSjM2w"
DEV_ID = 8543358373  # Твой Telegram ID (Разработчик)

bot = telebot.TeleBot(TOKEN)
DB_FILE = "database.json"

# --- МИНИ-СЕРВЕР ДЛЯ RENDER (ЧТОБЫ БОТ РАБОТАЛ 24/7 БЕЗ ВЫЛЕТОВ) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
# ------------------------------------------------------------------

# Роли, которые имеют право выдавать и менять префиксы
CAN_MANAGE_PREFIXES = ["💻 Разработчик", "👑 Владелец Проекта", "🔱 Зам. Владельца"]

# --- ИНИЦИАЛИЗАЦИЯ И СОХРАНЕНИЕ БАЗЫ ДАННЫХ ---
def load_data():
    default_data = {
        "admins": {DEV_ID},
        "admin_prefixes": {str(DEV_ID): "💻 Разработчик"},
        "all_users": {DEV_ID},
        "banned_users": set(),
        "username_to_id": {},
        "allowed_usernames": [],  
        "user_scores": {},
        "test_server_open": False  # ПО УМОЛЧАНИЮ ВСЕГДА ЗАКРЫТО!
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                
                admins = set(data.get("admins", [DEV_ID]))
                admins.add(DEV_ID)
                
                all_users = set(data.get("all_users", [DEV_ID]))
                all_users.add(DEV_ID)
                
                banned_users = set(data.get("banned_users", []))
                
                admin_prefixes = data.get("admin_prefixes", {})
                admin_prefixes[str(DEV_ID)] = "💻 Разработчик"

                return {
                    "admins": admins,
                    "admin_prefixes": admin_prefixes,
                    "all_users": all_users,
                    "banned_users": banned_users,
                    "username_to_id": data.get("username_to_id", {}),
                    "allowed_usernames": data.get("allowed_usernames", []),
                    "user_scores": data.get("user_scores", {}),
                    "test_server_open": data.get("test_server_open", False)
                }
        except Exception:
            return default_data
    return default_data

def save_data():
    data_to_save = {
        "admins": list(db["admins"]),
        "admin_prefixes": db["admin_prefixes"],
        "all_users": list(db["all_users"]),
        "banned_users": list(db["banned_users"]),
        "username_to_id": db["username_to_id"],
        "allowed_usernames": db["allowed_usernames"],
        "user_scores": db["user_scores"],
        "test_server_open": db["test_server_open"]
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

db = load_data()

# Временные состояния в оперативной памяти
user_states = {}
admin_reply_targets = {}
user_last_messages = {}
games = {}
test_applications = {}

# --- СЛУЖЕБНЫЕ ФУНКЦИИ ---
def register_user(user):
    user_id = user.id
    is_new = user_id not in db["all_users"]

    db["all_users"].add(user_id)
    if str(user_id) not in db["user_scores"]:
        db["user_scores"][str(user_id)] = 0

    uname = user.username.lower() if user.username else None
    if uname:
        db["username_to_id"][uname] = user_id
        if uname in db["allowed_usernames"]:
            db["admins"].add(user_id)
            if str(user_id) not in db["admin_prefixes"]:
                db["admin_prefixes"][str(user_id)] = "🛡 Главный Администратор"
            db["allowed_usernames"].remove(uname)

    save_data()

    if is_new and user_id not in db["admins"]:
        username_str = f"@{user.username}" if user.username else "<i>Отсутствует</i>"
        notify_text = (
            "🎉 <b>[НОВЫЙ ПОЛЬЗОВАТЕЛЬ В БОТЕ]</b>\n"
            "───────────────────────────────\n"
            f"👤 <b>Имя:</b> {user.first_name}\n"
            f"🔗 <b>Юзернейм:</b> {username_str}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            "───────────────────────────────\n"
            f"📊 Всего пользователей: <b>{len(db['all_users'])}</b>"
        )
        for admin_id in db["admins"]:
            try:
                bot.send_message(admin_id, notify_text, parse_mode="HTML")
            except Exception:
                pass

def can_user_change_prefixes(user_id):
    if user_id == DEV_ID:
        return True
    user_prefix = db["admin_prefixes"].get(str(user_id), "")
    return any(role in user_prefix for role in CAN_MANAGE_PREFIXES)

# --- ИНЛАЙН КЛАВИАТУРЫ ---
def get_main_inline_kb(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🛒 Донат Магазин", callback_data="btn_shop"),
        types.InlineKeyboardButton("💡 Предложить идею", callback_data="btn_idea")
    )
    kb.add(
        types.InlineKeyboardButton("🛠 Тех. Поддержка", callback_data="btn_support"),
        types.InlineKeyboardButton("🧪 Заявка на Тест-Сервер", callback_data="btn_test_server")
    )
    kb.add(
        types.InlineKeyboardButton("🎮 Игра (Prince Coins)", callback_data="btn_game"),
        types.InlineKeyboardButton("❓ FAQ / Вопросы", callback_data="btn_faq")
    )
    kb.add(
        types.InlineKeyboardButton("📜 Правила", callback_data="btn_rules"),
        types.InlineKeyboardButton("🌐 Наши Ресурсы", callback_data="btn_links")
    )
    if user_id in db["admins"]:
        kb.add(types.InlineKeyboardButton("⚙️ Панель Управления", callback_data="btn_admin_panel"))
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
    status_icon = "🔓" if db["test_server_open"] else "🔒"
    kb.add(types.InlineKeyboardButton(f"{status_icon} Открыть/Закрыть Тест", callback_data="adm_toggle_test"))

    kb.add(
        types.InlineKeyboardButton("➕ Добавить админа", callback_data="adm_add"),
        types.InlineKeyboardButton("➖ Удалить админа", callback_data="adm_remove"),
        types.InlineKeyboardButton("🏷 Изменить префикс", callback_data="adm_prefix"),
        types.InlineKeyboardButton("🔒 Забанить", callback_data="adm_ban"),
        types.InlineKeyboardButton("🔓 Разбанить", callback_data="adm_unban"),
        types.InlineKeyboardButton("✉️ Написать по ID", callback_data="adm_send_direct"),
        types.InlineKeyboardButton("📋 Список админов", callback_data="adm_list"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats"),
        types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"),
        types.InlineKeyboardButton("🔙 Главное меню", callback_data="btn_main_menu")
    )
    return kb

def get_game_inline_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🟢 Легкий (1-10) | +10 Coins", callback_data="game_easy"),
        types.InlineKeyboardButton("🟡 Средний (1-50) | +50 Coins", callback_data="game_medium"),
        types.InlineKeyboardButton("🔴 Хардкор (1-100) | +150 Coins", callback_data="game_hard"),
        types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu")
    )
    return kb

def get_reply_keyboard(target_user_id):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("💬 Ответить пользователю", callback_data=f"reply_to_{target_user_id}"))
    return kb

def get_test_app_keyboard(target_user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"test_accept_{target_user_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"test_decline_{target_user_id}")
    )
    return kb

# --- КОМАНДЫ БОТА ---
@bot.message_handler(commands=['start', 'menu', 'cancel'])
def start_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    user_states[user_id] = None
    admin_reply_targets[user_id] = None

    coins = db["user_scores"].get(str(user_id), 0)
    welcome_text = (
        "<b>✨ Добро пожаловать на проект Prince Russia!</b>\n"
        "───────────────────────────────\n"
        "Официальный многофункциональный бот поддержки и сервисов проекта.\n\n"
        f"💰 Ваш баланс: <b>{coins} Prince Coins</b>\n\n"
        "<b>Выберите нужный раздел кнопкой ниже:</b>"
    )
    bot.send_message(user_id, welcome_text, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

@bot.message_handler(commands=['admin', 'dev'])
def admin_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    if user_id in db["admins"]:
        bot.send_message(user_id, "<b>⚙️ Панель Управления Команды Проекта:</b>", parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
    else:
        bot.send_message(user_id, "❌ У вас нет доступа к этой команде.")

# --- ОБРАБОТКА ИНЛАЙН КНОПОК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    register_user(call.from_user)

    if user_id in db["banned_users"]:
        bot.answer_callback_query(call.id, "⛔️ Вы заблокированы в боте!", show_alert=True)
        return

    # Главное меню
    if call.data == "btn_main_menu":
        user_states[user_id] = None
        admin_reply_targets[user_id] = None
        coins = db["user_scores"].get(str(user_id), 0)
        welcome_text = (
            "<b>✨ Главное меню Prince Russia</b>\n"
            "───────────────────────────────\n"
            f"💰 Ваш баланс: <b>{coins} Prince Coins</b>\n\n"
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

    # 🧪 Заявка на тест-сервер
    elif call.data == "btn_test_server":
        if not db["test_server_open"]:
            bot.answer_callback_query(call.id, "⛔️ Набор на тест-сервер сейчас ЗАКРЫТ!", show_alert=True)
            return

        user_states[user_id] = 'test_step1'
        test_applications[user_id] = {}
        text = (
            "<b>🧪 Заявка на Тест-Сервер Prince Russia</b>\n"
            "───────────────────────────────\n"
            "<b>Шаг 1 из 3:</b> Введите ваш Игровой Никнейм (например: <code>Alex_Prince</code>):"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Принять/Отклонить заявку на тест
    elif call.data.startswith("test_accept_") or call.data.startswith("test_decline_"):
        if user_id not in db["admins"]:
            bot.answer_callback_query(call.id, "У вас нет прав!", show_alert=True)
            return

        is_accept = call.data.startswith("test_accept_")
        target_id = int(call.data.replace("test_accept_", "").replace("test_decline_", ""))

        prefix = db["admin_prefixes"].get(str(user_id), "🛡 Главный Администратор")
        admin_uname = f"@{call.from_user.username}" if call.from_user.username else call.from_user.first_name

        if is_accept:
            status_text = f"✅ <b>Заявка ОДОБРЕНА</b> ({prefix} {admin_uname})"
            user_msg = "🎉 <b>Ваша заявка на Тест-Сервер Prince Russia ОДОБРЕНА!</b>\nС вами свяжется администрация для выдачи доступа."
        else:
            status_text = f"❌ <b>Заявка ОТКЛОНЕНА</b> ({prefix} {admin_uname})"
            user_msg = "❌ <b>К сожалению, ваша заявка на Тест-Сервер отклонена.</b>"

        bot.edit_message_text(call.message.text + f"\n\n───────────────────────────────\n{status_text}", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML")
        try:
            bot.send_message(target_id, user_msg, parse_mode="HTML")
        except Exception: pass

    # Управление включением/выключением набора на тест
    elif call.data == "adm_toggle_test":
        if user_id in db["admins"]:
            db["test_server_open"] = not db["test_server_open"]
            save_data()
            st = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
            bot.answer_callback_query(call.id, f"Набор на тест-сервер теперь {st}!")
            bot.edit_message_text("<b>⚙️ Панель Управления:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
        else:
            bot.answer_callback_query(call.id, "Доступ запрещен!", show_alert=True)

    # Игра Выбор Сложности
    elif call.data == "btn_game":
        coins = db["user_scores"].get(str(user_id), 0)
        text = (
            "<b>🎮 Мини-Игра «Числовая Рулетка»</b>\n"
            "───────────────────────────────\n"
            f"💰 Ваш баланс: <b>{coins} Prince Coins</b>\n\n"
            "Угадайте загаданное число и получайте монеты!\n"
            "Выберите уровень сложности:"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_game_inline_kb())

    # Старт уровней игры
    elif call.data in ["game_easy", "game_medium", "game_hard"]:
        if call.data == "game_easy":
            max_val, reward = 10, 10
        elif call.data == "game_medium":
            max_val, reward = 50, 50
        else:
            max_val, reward = 100, 150

        games[user_id] = {
            'secret': random.randint(1, max_val),
            'attempts': 0,
            'max_val': max_val,
            'reward': reward
        }
        user_states[user_id] = 'playing_game'

        text = (
            f"🎯 <b>Загадано число от 1 до {max_val}!</b>\n"
            "───────────────────────────────\n"
            f"🏆 Награда за победу: <b>+{reward} Coins</b>\n"
            "Напишите ваш вариант числа прямо в чат:"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

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
            "Напишите вашу идею прямо сейчас!\n"
            "<i>Принимаются: текст, фото, видео, GIF, голосовые и файлы.</i>"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Поддержка
    elif call.data == "btn_support":
        user_states[user_id] = 'support'
        text = (
            "<b>🛠 Техническая поддержка</b>\n"
            "───────────────────────────────\n"
            "Опишите вашу проблему или вопрос ниже.\n"
            "<i>Вы можете отправить: текст, фото, видео, GIF, голосовое, кружочек или документ.</i>"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Отмена
    elif call.data == "btn_cancel":
        user_states[user_id] = None
        admin_reply_targets[user_id] = None
        test_applications.pop(user_id, None)
        bot.answer_callback_query(call.id, "Действие отменено.")
        bot.edit_message_text("<b>Действие отменено.</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    # Админ Панель
    elif call.data == "btn_admin_panel":
        if user_id in db["admins"]:
            bot.edit_message_text("<b>⚙️ Панель Управления:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
        else:
            bot.answer_callback_query(call.id, "Доступ запрещен!", show_alert=True)

    # Ответ пользователю
    elif call.data.startswith("reply_to_"):
        if user_id not in db["admins"]:
            bot.answer_callback_query(call.id, "У вас нет прав!", show_alert=True)
            return
        target_id = int(call.data.replace("reply_to_", ""))
        admin_reply_targets[user_id] = target_id
        bot.send_message(user_id, f"📝 <b>Введите ответ пользователю (ID: <code>{target_id}</code>):</b>\n<i>Можно отправлять текст, фото, видео, GIF и любые медиа!</i>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    # Функции админов
    elif call.data == "adm_stats":
        if user_id in db["admins"]:
            t_status = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
            text = (
                "<b>📊 Статистика проекта Prince Russia:</b>\n"
                "───────────────────────────────\n"
                f"👤 Всего пользователей: <b>{len(db['all_users'])}</b>\n"
                f"🛠 Администраторов: <b>{len(db['admins'])}</b>\n"
                f"⏳ В ожидании авто-выдачи: <b>{len(db['allowed_usernames'])}</b>\n"
                f"🚫 В бане: <b>{len(db['banned_users'])}</b>\n"
                f"🧪 Набор на Тест: <b>{t_status}</b>"
            )
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_add":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите @username или Telegram ID нового админа (Ему будет выдана роль Гл. Администратор):", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "adm_remove":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите @username или ID для снятия прав:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data == "adm_prefix":
        if can_user_change_prefixes(user_id):
            msg = bot.send_message(
                user_id, 
                "<b>🏷 Смена префикса / должности:</b>\n\n"
                "Введите ID или @username и через пробел новую должность.\n\n"
                "<b>Доступные роли:</b>\n"
                "• 💻 Разработчик\n"
                "• 👑 Владелец Проекта\n"
                "• 🔱 Зам. Владельца\n"
                "• 🛡 Главный Администратор\n\n"
                "<i>Пример:</i> <code>@username 🛡 Главный Администратор</code>", 
                parse_mode="HTML", 
                reply_markup=get_cancel_inline_kb()
            )
            bot.register_next_step_handler(msg, process_set_prefix)
        else:
            bot.answer_callback_query(call.id, "❌ Выдавать префиксы могут только Зам. Владельца и выше!", show_alert=True)

    elif call.data == "adm_ban":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите @username или ID для блокировки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "adm_unban":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите @username или ID для разблокировки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "adm_send_direct":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите Telegram ID пользователя для прямого сообщения:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_direct_msg_id)

    elif call.data == "adm_list":
        if user_id in db["admins"]:
            text = f"<b>📋 Команда Проекта Prince Russia ({len(db['admins'])}):</b>\n\n"
            for adm in db["admins"]:
                prefix = db["admin_prefixes"].get(str(adm), "🛡 Главный Администратор")
                text += f"• ID: <code>{adm}</code> — <b>{prefix}</b>\n"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_broadcast":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Отправьте пост для массовой рассылки:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_broadcast)

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ АДМИНКИ ---
def process_add_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = db["username_to_id"].get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        db["admins"].add(target_id)
        db["admin_prefixes"][str(target_id)] = "🛡 Главный Администратор"
        save_data()
        bot.send_message(message.chat.id, f"✅ Пользователь <code>{target_id}</code> назначен <b>🛡 Главным Администратором</b>!", parse_mode="HTML")
        try:
            bot.send_message(target_id, "🎉 <b>Вам выданы права Главного Администратора Prince Russia!</b>\nНажмите /menu для работы.", parse_mode="HTML")
        except Exception: pass
    else:
        if not input_data.isdigit():
            db["allowed_usernames"].append(input_data)
            save_data()
            bot.send_message(message.chat.id, f"⏳ Пользователь <code>@{input_data}</code> еще не запускал бота. Права зарезервированы!", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь с таким ID не найден.")

def process_remove_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = db["username_to_id"].get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        if target_id == DEV_ID:
            bot.send_message(message.chat.id, "❌ Нельзя снять права у Разработчика!")
            return
        db["admins"].discard(target_id)
        db["admin_prefixes"].pop(str(target_id), None)
        save_data()
        bot.send_message(message.chat.id, f"✅ Права у <code>{target_id}</code> успешно сняты.", parse_mode="HTML")
    else:
        if input_data in db["allowed_usernames"]:
            db["allowed_usernames"].remove(input_data)
            save_data()
            bot.send_message(message.chat.id, f"✅ Пользователь <code>@{input_data}</code> удален из списка ожидающих.", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def process_set_prefix(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    try:
        parts = message.text.strip().split(" ", 1)
        user_str = parts[0].replace("@", "").lower()
        new_prefix = parts[1]
        target_id = db["username_to_id"].get(user_str) or (int(user_str) if user_str.isdigit() else None)

        if target_id and target_id in db["admins"]:
            db["admin_prefixes"][str(target_id)] = new_prefix
            save_data()
            bot.send_message(message.chat.id, f"✅ Для пользователя <code>{target_id}</code> установлен префикс: <b>{new_prefix}</b>", parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден среди администраторов.")
    except Exception:
        bot.send_message(message.chat.id, "❌ Неверный формат! Вводите так: <code>ID_или_username [Префикс]</code>", parse_mode="HTML")

def process_ban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = db["username_to_id"].get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id:
        if target_id in db["admins"]:
            bot.send_message(message.chat.id, "❌ Нельзя заблокировать члена Команды Проекта!")
            return
        db["banned_users"].add(target_id)
        save_data()
        bot.send_message(message.chat.id, f"⛔️ Пользователь <code>{target_id}</code> заблокирован.", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Пользователь не найден.")

def process_unban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    input_data = message.text.strip().replace("@", "").lower()
    target_id = db["username_to_id"].get(input_data) or (int(input_data) if input_data.isdigit() else None)

    if target_id in db["banned_users"]:
        db["banned_users"].remove(target_id)
        save_data()
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
    for uid in list(db["all_users"]):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except Exception: pass
    bot.send_message(message.chat.id, f"📢 <b>Рассылка завершена!</b>\nДоставлено: {count}/{len(db['all_users'])}", parse_mode="HTML")

# --- ОБРАБОТКА ВХОДЯЩИХ СООБЩЕНИЙ ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'animation', 'voice', 'video_note', 'document', 'sticker', 'audio'])
def handle_all_messages(message):
    user_id = message.chat.id
    register_user(message.from_user)

    if user_id in db["banned_users"]:
        bot.send_message(user_id, "⛔️ Вы заблокированы в боте.")
        return

    state = user_states.get(user_id)
    is_replying = user_id in db["admins"] and admin_reply_targets.get(user_id)

    # 🧪 ПОШАГОВАЯ ЗАЯВКА НА ТЕСТ-СЕРВЕР
    if state == 'test_step1' and message.content_type == 'text':
        test_applications[user_id]['nick'] = message.text.strip()
        user_states[user_id] = 'test_step2'
        bot.send_message(user_id, "<b>Шаг 2 из 3:</b> Укажите ваш реальный возраст:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step2' and message.content_type == 'text':
        test_applications[user_id]['age'] = message.text.strip()
        user_states[user_id] = 'test_step3'
        bot.send_message(user_id, "<b>Шаг 3 из 3:</b> Опишите ваш опыт в тестировании CRMP/SAMP проектов и сколько времени готовы уделять:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step3':
        test_applications[user_id]['exp'] = message.text or message.caption or "Не указано"
        
        app_data = test_applications[user_id]
        uname = f"@{message.from_user.username}" if message.from_user.username else "Нет юзернейма"

        card_text = (
            "🧪 <b>[НОВАЯ ЗАЯВКА НА ТЕСТ-СЕРВЕР]</b>\n"
            "───────────────────────────────\n"
            f"👤 <b>Игрок:</b> {message.from_user.first_name} ({uname})\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"🎮 <b>Никнейм:</b> <code>{app_data.get('nick')}</code>\n"
            f"🎂 <b>Возраст:</b> {app_data.get('age')}\n"
            f"📝 <b>Опыт и готовность:</b> {app_data.get('exp')}"
        )

        for admin_id in db["admins"]:
            try:
                bot.send_message(admin_id, card_text, parse_mode="HTML", reply_markup=get_test_app_keyboard(user_id))
            except Exception: pass

        bot.send_message(user_id, "🎉 <b>Ваша заявка на Тест-Сервер успешно отправлена!</b>\nОжидайте ответа Команды Проекта.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        user_states[user_id] = None
        test_applications.pop(user_id, None)
        return

    # 🎮 ИГРА «УГАДАЙ ЧИСЛО»
    elif state == 'playing_game' and message.content_type == 'text':
        if message.text.isdigit():
            val = int(message.text)
            gdata = games.get(user_id, {'secret': 5, 'attempts': 0, 'reward': 10})
            gdata['attempts'] += 1
            secret = gdata['secret']

            if val == secret:
                db["user_scores"][str(user_id)] = db["user_scores"].get(str(user_id), 0) + gdata['reward']
                save_data()
                tot_coins = db["user_scores"][str(user_id)]
                bot.send_message(
                    user_id, 
                    f"🎉 <b>ПОЗДРАВЛЯЕМ! Вы угадали число {secret}!</b>\n"
                    f"⏱ Попыток использовано: <b>{gdata['attempts']}</b>\n"
                    f"💰 Получено: <b>+{gdata['reward']} Prince Coins</b>\n"
                    f"🏦 Ваш итоговый баланс: <b>{tot_coins} Coins</b>", 
                    parse_mode="HTML", 
                    reply_markup=get_main_inline_kb(user_id)
                )
                user_states[user_id] = None
            elif val < secret:
                bot.send_message(user_id, f"📉 Загаданное число <b>БОЛЬШЕ</b> чем {val}! Попробуй еще раз (Попытка {gdata['attempts']}):", parse_mode="HTML")
            else:
                bot.send_message(user_id, f"📈 Загаданное число <b>МЕНЬШЕ</b> чем {val}! Попробуй еще раз (Попытка {gdata['attempts']}):", parse_mode="HTML")
        return

    # 1. Если АДМИН отвечает пользователю
    if is_replying:
        target_id = admin_reply_targets[user_id]
        
        prefix = db["admin_prefixes"].get(str(user_id), "🛡 Главный Администратор")
        admin_uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

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

    # 2. Если ПОЛЬЗОВАТЕЛЬ отправляет обращение/идею
    elif state in ['idea', 'support']:
        msg_type_str = "предложение" if state == 'idea' else "обращение"
        msg_text_str = message.text or message.caption or f"[{message.content_type.upper()}]"

        user_last_messages[user_id] = {
            'type': msg_type_str,
            'text': msg_text_str
        }

        user_info = f"👤 <b>От:</b> {message.from_user.first_name}"
        if message.from_username:
            user_info += f" (@{message.from_user.username})\n"
        else:
            user_info += "\n"
        user_info += f"🆔 <b>ID:</b> <code>{user_id}</code>\n"

        if state == 'idea':
            card_header = "💡 <b>[НОВОЕ ПРЕДЛОЖЕНИЕ ПО УЛУЧШЕНИЮ]</b>\n" + user_info
        else:
            card_header = "🛠 <b>[ОБРАЩЕНИЕ В ТЕХ. ПОДДЕРЖКУ]</b>\n" + user_info

        for admin_id in db["admins"]:
            try:
                bot.send_message(admin_id, card_header, parse_mode="HTML")
                bot.copy_message(admin_id, user_id, message.message_id, reply_markup=get_reply_keyboard(user_id))
            except Exception: pass

        if state == 'idea':
            bot.send_message(user_id, "💡 <b>Спасибо!</b> Ваша идея передана Команде Проекта.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        else:
            bot.send_message(user_id, "📩 <b>Ваше обращение доставлено!</b> Ожидайте ответа.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

        user_states[user_id] = None

    # 3. Обычное сообщение
    else:
        bot.send_message(
            user_id, 
            "ℹ️ Воспользуйтесь меню ниже для взаимодействия с ботом:", 
            reply_markup=get_main_inline_kb(user_id)
        )

# --- ЗАПУСК БОТА + ВЕБ-СЕРВЕР ДЛЯ 24/7 РАБОТЫ ---
if __name__ == '__main__':
    keep_alive()  # Запуск веб-сервера на порту 8080 для Render
    while True:
        try:
            bot.remove_webhook()
            print("🚀 Бот Prince Russia успешно запущен и работает 24/7!")
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"⚠️ Ошибка сети или Telegram API: {e}. Перезапуск через 5 секунд...")
            time.sleep(5)
