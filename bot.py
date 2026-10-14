import telebot
from telebot import types
import random
import json
import os
import time
from flask import Flask
from threading import Thread

TOKEN = "8854430576:AAFFnW7WXydJRzvkrsFzw1KOy8cTikSxEWQ"
DEV_ID = 8543358373  # Твой Telegram ID (Разработчик)

bot = telebot.TeleBot(TOKEN)
DB_FILE = "database.json"

# --- МИНИ-СЕРВЕР ДЛЯ RENDER (24/7) ---
app = Flask('')

@app.route('/')
def home():
    return "Prince Russia бот работает 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
# -------------------------------------

CAN_MANAGE_PREFIXES = ["💻 Разработчик", "👑 Владелец Проекта", "🔱 Зам. Владельца"]

# --- БАЗА ДАННЫХ ---
def load_data():
    default_data = {
        "admins": {DEV_ID},
        "admin_prefixes": {str(DEV_ID): "💻 Разработчик"},
        "all_users": {DEV_ID},
        "banned_users": set(),
        "username_to_id": {},
        "allowed_usernames": [],  
        "user_scores": {},
        "test_server_open": False
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

user_states = {}
admin_reply_targets = {}
user_last_messages = {}
games = {}
test_applications = {}
pending_test_actions = {}

def register_user(user):
    user_id = user.id
    is_new = user_id not in db["all_users"]

    db["all_users"].add(user_id)
    if str(user_id) not in db["user_scores"]:
        db["user_scores"][str(user_id)] = 500  # Стартовый бонус

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
            "🎉 <b>[НОВЫЙ ИГРОК В БОТЕ]</b>\n"
            "───────────────────────────────\n"
            f"👤 <b>Имя:</b> {user.first_name}\n"
            f"🔗 <b>Юзернейм:</b> {username_str}\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            "───────────────────────────────\n"
            f"📊 Всего игроков: <b>{len(db['all_users'])}</b>"
        )
        for admin_id in db["admins"]:
            try: bot.send_message(admin_id, notify_text, parse_mode="HTML")
            except Exception: pass

def can_user_change_prefixes(user_id):
    if user_id == DEV_ID: return True
    user_prefix = db["admin_prefixes"].get(str(user_id), "")
    return any(role in user_prefix for role in CAN_MANAGE_PREFIXES)

# --- КЛАВИАТУРЫ ---
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
        types.InlineKeyboardButton("🎰 Казино Prince Casino", callback_data="btn_casino"),
        types.InlineKeyboardButton("🎮 Угадай число", callback_data="btn_game")
    )
    kb.add(
        types.InlineKeyboardButton("❓ FAQ / Вопросы", callback_data="btn_faq"),
        types.InlineKeyboardButton("📜 Правила", callback_data="btn_rules")
    )
    kb.add(types.InlineKeyboardButton("🌐 Наши Ресурсы", callback_data="btn_links"))
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

def get_casino_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🎲 Сыграть в Кости (Dice)", callback_data="casino_dice"),
        types.InlineKeyboardButton("🎰 Крутить Слоты (Slots)", callback_data="casino_slots"),
        types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu")
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
    kb.add(types.InlineKeyboardButton("💬 Ответить игроку", callback_data=f"reply_to_{target_user_id}"))
    return kb

def get_test_app_keyboard(target_user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Принять", callback_data=f"test_accept_{target_user_id}"),
        types.InlineKeyboardButton("❌ Отклонить", callback_data=f"test_decline_{target_user_id}")
    )
    return kb

# --- КОМАНДЫ ---
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
        "Официальный игровой бот проекта. Участвуй в жизни сервера, играй в казино и подавай заявки!\n\n"
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

# --- CALLBACK ОБРАБОТЧИК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    register_user(call.from_user)

    if user_id in db["banned_users"]:
        bot.answer_callback_query(call.id, "⛔️ Вы заблокированы!", show_alert=True)
        return

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

    # --- КАЗИНО ---
    elif call.data == "btn_casino":
        coins = db["user_scores"].get(str(user_id), 0)
        casino_text = (
            "<b>🎰 Prince Casino — Испытай удачу!</b>\n"
            "───────────────────────────────\n"
            f"💰 Ваш баланс: <b>{coins} Prince Coins</b>\n\n"
            "Выбирайте режим игры ниже:"
        )
        bot.edit_message_text(casino_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_casino_kb())

    elif call.data == "casino_dice":
        user_states[user_id] = 'casino_bet_dice'
        bot.edit_message_text(
            "<b>🎲 Казино: Игра в Кости</b>\n"
            "───────────────────────────────\n"
            "Введите ставку в Prince Coins (числом), которую хотите поставить:",
            chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb()
        )

    elif call.data == "casino_slots":
        user_states[user_id] = 'casino_bet_slots'
        bot.edit_message_text(
            "<b>🎰 Казино: Слоты (Однорукий бандит)</b>\n"
            "───────────────────────────────\n"
            "Введите ставку в Prince Coins (числом):",
            chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb()
        )

    # --- ТЕСТ СЕРВЕР ---
    elif call.data == "btn_test_server":
        if not db["test_server_open"]:
            bot.answer_callback_query(call.id, "⛔️ Набор на тест-сервер сейчас ЗАКРЫТ!", show_alert=True)
            return

        user_states[user_id] = 'test_step1'
        test_applications[user_id] = {}
        text = (
            "<b>🧪 Заявка на Тест-Сервер Prince Russia</b>\n"
            "───────────────────────────────\n"
            "<b>Шаг 1 из 4:</b> Введите ваш Игровой Никнейм (например: <code>Alex_Prince</code>):"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data.startswith("test_accept_") or call.data.startswith("test_decline_"):
        if user_id not in db["admins"]:
            bot.answer_callback_query(call.id, "У вас нет прав!", show_alert=True)
            return

        is_accept = call.data.startswith("test_accept_")
        target_id = int(call.data.replace("test_accept_", "").replace("test_decline_", ""))
        
        pending_test_actions[user_id] = {
            'target_id': target_id,
            'action': 'accept' if is_accept else 'decline',
            'msg_id': call.message.message_id,
            'card_text': call.message.text
        }
        user_states[user_id] = 'awaiting_test_reason'
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "📝 <b>Введите причину вердикта по заявке:</b>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "adm_toggle_test":
        if user_id in db["admins"]:
            db["test_server_open"] = not db["test_server_open"]
            save_data()
            st = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
            bot.answer_callback_query(call.id, f"Набор теперь {st}!")
            bot.edit_message_text("<b>⚙️ Панель Управления:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data == "btn_game":
        coins = db["user_scores"].get(str(user_id), 0)
        text = (
            "<b>🎮 Мини-Игра «Числовая Рулетка»</b>\n"
            "───────────────────────────────\n"
            f"💰 Ваш баланс: <b>{coins} Prince Coins</b>\n\n"
            "Угадайте число и забирайте куш! Выберите сложность:"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_game_inline_kb())

    elif call.data in ["game_easy", "game_medium", "game_hard"]:
        max_val, reward = (10, 10) if call.data == "game_easy" else ((50, 50) if call.data == "game_medium" else (100, 150))
        games[user_id] = {'secret': random.randint(1, max_val), 'attempts': 0, 'reward': reward}
        user_states[user_id] = 'playing_game'
        bot.edit_message_text(f"🎯 Загадано число от 1 до {max_val}!\nНаграда: +{reward} Coins\nНапишите ваш вариант в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "btn_rules":
        rules_text = (
            "<b>📜 Правила проекта Prince Russia</b>\n"
            "───────────────────────────────\n"
            "1. Оскорбления игроков и администрации запрещены.\n"
            "2. Использование читов и сторонних скриптов карается баном.\n"
            "3. Спам и реклама в боте запрещены."
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Форум Правил", url="https://forum-prince-russia.samp.date"))
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(rules_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "btn_faq":
        faq_text = (
            "<b>❓ Частые вопросы (FAQ) — Prince Russia</b>\n"
            "───────────────────────────────\n"
            "<b>Как начать играть?</b>\n"
            "<i>Скачайте лаунчер на нашем сайте или в сообществе VK.</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(faq_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "btn_links":
        bot.edit_message_text("<b>🌐 Официальные ресурсы Prince Russia</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_links_inline_kb())

    elif call.data == "btn_idea":
        user_states[user_id] = 'idea'
        bot.edit_message_text("💡 Напишите вашу идею или предложение в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "btn_support":
        user_states[user_id] = 'support'
        bot.edit_message_text("🛠 Опишите вашу проблему или вопрос в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "btn_cancel":
        user_states[user_id] = None
        admin_reply_targets[user_id] = None
        test_applications.pop(user_id, None)
        pending_test_actions.pop(user_id, None)
        bot.answer_callback_query(call.id, "Отменено.")
        bot.edit_message_text("<b>Главное меню:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    elif call.data == "btn_admin_panel":
        if user_id in db["admins"]:
            bot.edit_message_text("<b>⚙️ Панель Управления:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data.startswith("reply_to_"):
        if user_id not in db["admins"]: return
        target_id = int(call.data.replace("reply_to_", ""))
        admin_reply_targets[user_id] = target_id
        bot.send_message(user_id, f"📝 Введите ответ игроку (ID: <code>{target_id}</code>):", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "adm_stats":
        if user_id in db["admins"]:
            t_status = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
            text = f"<b>📊 Статистика:</b>\nИгроков: {len(db['all_users'])}\nАдминов: {len(db['admins'])}\nБанов: {len(db['banned_users'])}\nТест: {t_status}"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_add":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите @username или ID нового админа:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "adm_remove":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите @username или ID для снятия прав:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data == "adm_prefix":
        if can_user_change_prefixes(user_id):
            msg = bot.send_message(user_id, "Введите ID/username и через пробел новый префикс:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_set_prefix)

    elif call.data == "adm_ban":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите ID или username для бана:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "adm_unban":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите ID или username для разбана:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "adm_send_direct":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Введите Telegram ID игрока:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_direct_msg_id)

    elif call.data == "adm_list":
        if user_id in db["admins"]:
            text = "<b>📋 Администрация проекта:</b>\n\n"
            for adm in db["admins"]:
                pref = db["admin_prefixes"].get(str(adm), "Админ")
                text += f"• <code>{adm}</code> — <b>{pref}</b>\n"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_broadcast":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "Отправьте пост для рассылки всем игрокам:", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_broadcast)

# --- АДМИН УТИЛИТЫ ---
def process_add_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid:
        db["admins"].add(tid)
        db["admin_prefixes"][str(tid)] = "🛡 Главный Администратор"
        save_data()
        bot.send_message(message.chat.id, f"✅ Назначен админом: <code>{tid}</code>", parse_mode="HTML")
        try: bot.send_message(tid, "🎉 Вам выданы права администратора!", parse_mode="HTML")
        except Exception: pass
    else: bot.send_message(message.chat.id, "❌ Игрок не найден.")

def process_remove_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid and tid != DEV_ID:
        db["admins"].discard(tid)
        db["admin_prefixes"].pop(str(tid), None)
        save_data()
        bot.send_message(message.chat.id, f"✅ Права сняты с <code>{tid}</code>", parse_mode="HTML")

def process_set_prefix(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    try:
        parts = message.text.strip().split(" ", 1)
        ustr = parts[0].replace("@", "").lower()
        pref = parts[1]
        tid = db["username_to_id"].get(ustr) or (int(ustr) if ustr.isdigit() else None)
        if tid and tid in db["admins"]:
            db["admin_prefixes"][str(tid)] = pref
            save_data()
            bot.send_message(message.chat.id, f"✅ Префикс успешно изменен!", parse_mode="HTML")
    except Exception: bot.send_message(message.chat.id, "❌ Ошибка формата.")

def process_ban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid and tid not in db["admins"]:
        db["banned_users"].add(tid)
        save_data()
        bot.send_message(message.chat.id, f"⛔️ Забанен ID: <code>{tid}</code>", parse_mode="HTML")

def process_unban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid in db["banned_users"]:
        db["banned_users"].remove(tid)
        save_data()
        bot.send_message(message.chat.id, f"✅ Разбанен ID: <code>{tid}</code>", parse_mode="HTML")

def process_direct_msg_id(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    if message.text.isdigit():
        tid = int(message.text)
        admin_reply_targets[message.chat.id] = tid
        bot.send_message(message.chat.id, f"📝 Напишите сообщение для ID <code>{tid}</code>:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

def process_broadcast(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    count = 0
    for uid in list(db["all_users"]):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except Exception: pass
    bot.send_message(message.chat.id, f"📢 Рассылка завершена! Доставлено: {count}", parse_mode="HTML")

# --- ОБРАБОТКА ТЕКСТА И ИГР ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'animation', 'voice', 'video_note', 'document', 'sticker', 'audio'])
def handle_all_messages(message):
    user_id = message.chat.id
    register_user(message.from_user)

    if user_id in db["banned_users"]: return

    state = user_states.get(user_id)
    is_replying = user_id in db["admins"] and admin_reply_targets.get(user_id)
    user_bal = db["user_scores"].get(str(user_id), 0)

    # ЛОГИКА КАЗИНО: СТАВКА НА КОСТИ
    if state == 'casino_bet_dice' and message.content_type == 'text':
        if message.text.isdigit():
            bet = int(message.text)
            if bet <= 0 or bet > user_bal:
                bot.send_message(user_id, f"❌ Неверная ставка! У вас на балансе: <b>{user_bal} Coins</b>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
                return
            
            db["user_scores"][str(user_id)] -= bet
            save_data()
            user_states[user_id] = None

            bot.send_message(user_id, "🎲 Бросаем кости...")
            sent_dice = bot.send_dice(user_id, emoji='🎲')
            time.sleep(3)
            score = sent_dice.dice.value

            if score >= 4:
                win_amount = bet * 2
                db["user_scores"][str(user_id)] += win_amount
                save_data()
                bot.send_message(user_id, f"🎉 <b>Выпало {score}! Вы выиграли {win_amount} Coins!</b> 🔥", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
            else:
                bot.send_message(user_id, f"😢 Выпало {score}. Вы проиграли ставку в {bet} Coins.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        return

    # ЛОГИКА КАЗИНО: СЛОТЫ
    elif state == 'casino_bet_slots' and message.content_type == 'text':
        if message.text.isdigit():
            bet = int(message.text)
            if bet <= 0 or bet > user_bal:
                bot.send_message(user_id, f"❌ Неверная ставка! У вас на балансе: <b>{user_bal} Coins</b>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
                return
            
            db["user_scores"][str(user_id)] -= bet
            save_data()
            user_states[user_id] = None

            bot.send_message(user_id, "🎰 Крутим барабан слотов...")
            sent_slot = bot.send_dice(user_id, emoji='🎰')
            time.sleep(3)
            val = sent_slot.dice.value

            if val in [1, 22, 43, 64]:
                win_amount = bet * 5
                db["user_scores"][str(user_id)] += win_amount
                save_data()
                bot.send_message(user_id, f"🎰💎 <b>ДЖЕКПОТ! Вы сорвали куш х5 и получили {win_amount} Coins!</b> 🚀", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
            elif val % 2 == 0:
                win_amount = int(bet * 1.5)
                db["user_scores"][str(user_id)] += win_amount
                save_data()
                bot.send_message(user_id, f"✨ Вы выиграли {win_amount} Coins!", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
            else:
                bot.send_message(user_id, f"💨 В этот раз не повезло (-{bet} Coins).", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        return

    # ВВОД ПРИЧИНЫ ДЛЯ ВЕРДИКТА ПО ТЕСТУ
    if state == 'awaiting_test_reason':
        act_info = pending_test_actions.get(user_id)
        if act_info:
            target_id = act_info['target_id']
            is_accept = (act_info['action'] == 'accept')
            reason = message.text.strip()
            
            prefix = db["admin_prefixes"].get(str(user_id), "🛡 Администратор")
            admin_uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            
            if is_accept:
                status_text = f"✅ <b>Заявка ОДОБРЕНА</b> ({prefix} {admin_uname})\n💬 <b>Причина:</b> {reason}"
                user_msg = f"🎉 <b>Ваша заявка на Тест-Сервер ОДОБРЕНА!</b>\n💬 <b>Комментарий:</b> {reason}\nС вами свяжется руководство."
            else:
                status_text = f"❌ <b>Заявка ОТКЛОНЕНА</b> ({prefix} {admin_uname})\n💬 <b>Причина:</b> {reason}"
                user_msg = f"❌ <b>Ваша заявка на Тест-Сервер отклонена.</b>\n💬 <b>Причина:</b> {reason}"
            
            try:
                bot.edit_message_text(act_info['card_text'] + f"\n\n───────────────────────────────\n{status_text}", chat_id=user_id, message_id=act_info['msg_id'], parse_mode="HTML")
            except Exception: pass

            try: bot.send_message(target_id, user_msg, parse_mode="HTML")
            except Exception: pass
            
            bot.send_message(user_id, "✅ Вердикт успешно отправлен игроку!", reply_markup=get_admin_inline_kb(user_id))
            user_states[user_id] = None
            pending_test_actions.pop(user_id, None)
        return

    # ПОШАГОВАЯ ЗАЯВКА НА ТЕСТ
    if state == 'test_step1' and message.content_type == 'text':
        test_applications[user_id]['nick'] = message.text.strip()
        user_states[user_id] = 'test_step2'
        bot.send_message(user_id, "<b>Шаг 2 из 4:</b> Укажите ваш реальный возраст:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step2' and message.content_type == 'text':
        test_applications[user_id]['age'] = message.text.strip()
        user_states[user_id] = 'test_step3'
        bot.send_message(user_id, "<b>Шаг 3 из 4:</b> Укажите ссылку на ваш VK (профиль или группу):", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step3' and message.content_type == 'text':
        test_applications[user_id]['vk'] = message.text.strip()
        user_states[user_id] = 'test_step4'
        bot.send_message(user_id, "<b>Шаг 4 из 4:</b> Опишите ваш опыт в тестировании и сколько времени готовы уделять:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step4':
        test_applications[user_id]['exp'] = message.text or message.caption or "Не указано"
        app_data = test_applications[user_id]
        uname = f"@{message.from_user.username}" if message.from_user.username else "Нет"

        card_text = (
            "🧪 <b>[НОВАЯ ЗАЯВКА НА ТЕСТ-СЕРВЕР]</b>\n"
            "───────────────────────────────\n"
            f"👤 <b>Игрок:</b> {message.from_user.first_name} ({uname})\n"
            f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
            f"🎮 <b>Никнейм:</b> <code>{app_data.get('nick')}</code>\n"
            f"🎂 <b>Возраст:</b> {app_data.get('age')}\n"
            f"🔗 <b>VK:</b> {app_data.get('vk')}\n"
            f"📝 <b>Опыт:</b> {app_data.get('exp')}"
        )

        for admin_id in db["admins"]:
            try: bot.send_message(admin_id, card_text, parse_mode="HTML", reply_markup=get_test_app_keyboard(user_id))
            except Exception: pass

        bot.send_message(user_id, "🎉 <b>Заявка успешно отправлена!</b> Ожидайте ответа руководства.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        user_states[user_id] = None
        test_applications.pop(user_id, None)
        return

    # ИГРА УГАДАЙ ЧИСЛО
    elif state == 'playing_game' and message.content_type == 'text':
        if message.text.isdigit():
            val = int(message.text)
            gdata = games.get(user_id, {'secret': 5, 'attempts': 0, 'reward': 10})
            secret = gdata['secret']

            if val == secret:
                db["user_scores"][str(user_id)] = db["user_scores"].get(str(user_id), 0) + gdata['reward']
                save_data()
                bot.send_message(user_id, f"🎉 <b>ПОБЕДА! Число {secret} угадано!</b>\n💰 Получено: +{gdata['reward']} Coins", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
                user_states[user_id] = None
            elif val < secret:
                bot.send_message(user_id, "📉 Загаданное число <b>БОЛЬШЕ</b>!", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            else:
                bot.send_message(user_id, "📈 Загаданное число <b>МЕНЬШЕ</b>!", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    # ОТВЕТ АДМИНА
    if is_replying:
        target_id = admin_reply_targets[user_id]
        prefix = db["admin_prefixes"].get(str(user_id), "🛡 Администратор")
        admin_uname = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name

        try:
            bot.send_message(target_id, f"<b>💬 Ответ от {prefix} ({admin_uname}):</b>", parse_mode="HTML")
            bot.copy_message(target_id, message.chat.id, message.message_id)
            bot.send_message(user_id, f"✅ Ответ доставлен игроку <code>{target_id}</code>!", parse_mode="HTML")
            admin_reply_targets[user_id] = None
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка: {e}")
        return

    elif state in ['idea', 'support']:
        card_header = "💡 <b>[НОВОЕ ПРЕДЛОЖЕНИЕ]</b>" if state == 'idea' else "🛠 <b>[ОБРАЩЕНИЕ В ПОДДЕРЖКУ]</b>"
        user_info = f"👤 От: {message.from_user.first_name} (ID: <code>{user_id}</code>)\n"

        for admin_id in db["admins"]:
            try:
                bot.send_message(admin_id, card_header + "\n" + user_info, parse_mode="HTML")
                bot.copy_message(admin_id, user_id, message.message_id, reply_markup=get_reply_keyboard(user_id))
            except Exception: pass

        bot.send_message(user_id, "✅ Сообщение успешно отправлено руководству!", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        user_states[user_id] = None

    else:
        bot.send_message(user_id, "ℹ️ Воспользуйтесь меню:", reply_markup=get_main_inline_kb(user_id))

# --- ЗАПУСК ПОТОКОВ ---
def start_bot():
    while True:
        try:
            bot.remove_webhook()
            print("✅ Бот успешно запущен и работает в штатном режиме!")
            bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"⚠️ Ошибка polling: {e}. Перезапуск...")
            time.sleep(3)

if __name__ == '__main__':
    print("🚀 Запуск бота в фоновом потоке...")
    bot_thread = Thread(target=start_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    print("🚀 Запуск веб-сервера Flask...")
    keep_alive()
    app.run(host='0.0.0.0', port=8080)
