import telebot
from telebot import types
import random
import json
import os
import time
from flask import Flask
from threading import Thread
from datetime import datetime

TOKEN = "8854430576:AAFFnW7WXydJRzvkrsFzw1KOy8cTikSxEWQ"
DEV_ID = 8543358373  # Твой Telegram ID (Разработчик / Владелец)

bot = telebot.TeleBot(TOKEN)
DB_FILE = "database.json"

# --- МИНИ-СЕРВЕР ДЛЯ RENDER (24/7) ---
app = Flask('')

@app.route('/')
def home():
    return "Prince Russia God Mode Engine is Ultra-Active & Running!"

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
        "daily_bonus": {},
        "promo_codes": {},
        "used_promos": {},
        "silent_mode": False,
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
                    "daily_bonus": data.get("daily_bonus", {}),
                    "promo_codes": data.get("promo_codes", {}),
                    "used_promos": data.get("used_promos", {}),
                    "silent_mode": data.get("silent_mode", False),
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
        "daily_bonus": db["daily_bonus"],
        "promo_codes": db["promo_codes"],
        "used_promos": db["used_promos"],
        "silent_mode": db["silent_mode"],
        "test_server_open": db["test_server_open"]
    }
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(data_to_save, f, ensure_ascii=False, indent=4)

db = load_data()

user_states = {}
admin_reply_targets = {}
games = {}
test_applications = {}
pending_test_actions = {}

def register_user(user):
    user_id = user.id
    is_new = user_id not in db["all_users"]

    db["all_users"].add(user_id)
    if str(user_id) not in db["user_scores"]:
        db["user_scores"][str(user_id)] = 500  # Стартовый капитал

    uname = user.username.lower() if user.username else None
    if uname:
        db["username_to_id"][uname] = user_id

    save_data()

    if is_new and user_id not in db["admins"] and not db["silent_mode"]:
        username_str = f"@{user.username}" if user.username else "<i>Отсутствует</i>"
        notify_text = (
            "🚀 <b>[GOD MODE: НОВЫЙ ИГРОК В СЕТИ]</b>\n"
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
        types.InlineKeyboardButton("👤 Элитный Профиль", callback_data="btn_profile"),
        types.InlineKeyboardButton("🎁 Ежедневный Бонус", callback_data="btn_daily")
    )
    kb.add(
        types.InlineKeyboardButton("📦 Крутить Кейс 🎁", callback_data="btn_case"),
        types.InlineKeyboardButton("🏆 ТОП Богачей", callback_data="btn_top")
    )
    kb.add(
        types.InlineKeyboardButton("🎟 Промокод", callback_data="btn_promo"),
        types.InlineKeyboardButton("💸 Перевод Coins", callback_data="btn_transfer")
    )
    kb.add(
        types.InlineKeyboardButton("🛒 Донат Магазин", callback_data="btn_shop"),
        types.InlineKeyboardButton("🧪 Тест-Сервер", callback_data="btn_test_server")
    )
    kb.add(
        types.InlineKeyboardButton("🎰 Prince Casino 👑", callback_data="btn_casino"),
        types.InlineKeyboardButton("🎮 Угадай число", callback_data="btn_game")
    )
    kb.add(
        types.InlineKeyboardButton("💡 Предложить идею", callback_data="btn_idea"),
        types.InlineKeyboardButton("🛠 Поддержка", callback_data="btn_support")
    )
    kb.add(
        types.InlineKeyboardButton("📜 Правила & FAQ", callback_data="btn_rules"),
        types.InlineKeyboardButton("🌐 Наши Ресурсы", callback_data="btn_links")
    )
    if user_id in db["admins"]:
        kb.add(types.InlineKeyboardButton("⚡️ ПАНЕЛЬ ОЛИГАРХА (Админ)", callback_data="btn_admin_panel"))
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
    
    kb.add(
        types.InlineKeyboardButton("➕ Назначить админа", callback_data="adm_add"),
        types.InlineKeyboardButton("➖ Снять админа", callback_data="adm_remove")
    )
    kb.add(
        types.InlineKeyboardButton("🏷 Изменить префикс", callback_data="adm_prefix"),
        types.InlineKeyboardButton("💰 Выдать/Списать Coins", callback_data="adm_give_coins")
    )
    kb.add(
        types.InlineKeyboardButton("🔒 Забанить игрока", callback_data="adm_ban"),
        types.InlineKeyboardButton("🔓 Разбанить игрока", callback_data="adm_unban")
    )
    kb.add(
        types.InlineKeyboardButton("✉️ Написать по ID / Юзу", callback_data="adm_send_direct"),
        types.InlineKeyboardButton(f"{status_icon} Статус теста", callback_data="adm_toggle_test")
    )
    kb.add(
        types.InlineKeyboardButton("🔍 Пробить игрока", callback_data="adm_lookup"),
        types.InlineKeyboardButton("🧹 Обнулить баланс", callback_data="adm_wipe_balance")
    )
    kb.add(
        types.InlineKeyboardButton("🎟 Создать Промокод", callback_data="adm_create_promo"),
        types.InlineKeyboardButton("🗑 Удалить Промокод", callback_data="adm_delete_promo")
    )
    kb.add(
        types.InlineKeyboardButton("👑 Назначить Зама", callback_data="adm_set_deputy"),
        types.InlineKeyboardButton("💻 Назначить Разраба", callback_data="adm_set_dev")
    )
    kb.add(
        types.InlineKeyboardButton("🔕 Тихий режим", callback_data="adm_toggle_silent"),
        types.InlineKeyboardButton("📂 Выгрузить JSON", callback_data="adm_export_db")
    )
    kb.add(
        types.InlineKeyboardButton("📋 Список админов", callback_data="adm_list"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats")
    )
    kb.add(
        types.InlineKeyboardButton("📢 Массовая рассылка", callback_data="adm_broadcast"),
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
        "<b>👑 PRINCE RUSSIA — GOD MODE ENGINE 🔥</b>\n"
        "───────────────────────────────\n"
        "Официальный бот высшей пробы. Крути кейсы, забирай миллионы, управляй экономикой!\n\n"
        f"💰 Твой баланс: <b>{coins} Prince Coins</b>\n\n"
        "<b>Выбирай нужную кнопку ниже:</b>"
    )
    bot.send_message(user_id, welcome_text, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

@bot.message_handler(commands=['admin', 'dev'])
def admin_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    if user_id in db["admins"]:
        bot.send_message(user_id, "<b>⚡️ ПАНЕЛЬ ОЛИГАРХА И РУКОВОДСТВА:</b>", parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
    else:
        bot.send_message(user_id, "❌ У тебя нет доступа к этой команде.")

# --- CALLBACK ОБРАБОТЧИК ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    register_user(call.from_user)

    if user_id in db["banned_users"]:
        bot.answer_callback_query(call.id, "⛔️ Доступ заблокирован!", show_alert=True)
        return

    if call.data == "btn_main_menu":
        user_states[user_id] = None
        admin_reply_targets[user_id] = None
        coins = db["user_scores"].get(str(user_id), 0)
        welcome_text = (
            "<b>✨ Главное меню Prince Russia</b>\n"
            "───────────────────────────────\n"
            f"💰 Твой баланс: <b>{coins} Prince Coins</b>\n\n"
            "Выбирай интересующий раздел:"
        )
        bot.edit_message_text(welcome_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    # ПРОФИЛЬ
    elif call.data == "btn_profile":
        coins = db["user_scores"].get(str(user_id), 0)
        role = db["admin_prefixes"].get(str(user_id), "👑 Элитный Игрок")
        profile_text = (
            "<b>👤 КАРТОЧКА ИГРОКА — PRINCE RUSSIA</b>\n"
            "───────────────────────────────\n"
            f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
            f"📛 <b>Статус / Роль:</b> <b>{role}</b>\n"
            f"💰 <b>Баланс счета:</b> <b>{coins} Prince Coins</b>\n"
            f"🛡 <b>Репутация:</b> <code>100% GOD MODE</code>\n"
            f"📌 <b>Статус аккаунта:</b> 🟢 <i>Верифицирован</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(profile_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    # КЕЙСЫ / РУЛЕТКА ПРИЗОВ
    elif call.data == "btn_case":
        coins = db["user_scores"].get(str(user_id), 0)
        case_cost = 250
        if coins < case_cost:
            bot.answer_callback_query(call.id, f"❌ Недостаточно коинов! Нужно минимум {case_cost} Coins.", show_alert=True)
            return

        db["user_scores"][str(user_id)] -= case_cost
        
        # Рандомный дроп из кейса
        drop_type = random.choices(["coins_small", "coins_big", "jackpot", "role"], weights=[50, 30, 15, 5])[0]
        
        if drop_type == "coins_small":
            win = random.randint(100, 300)
            msg_drop = f"🎁 Из кейса выпало: <b>+{win} Prince Coins!</b>"
        elif drop_type == "coins_big":
            win = random.randint(500, 1200)
            msg_drop = f"🔥 КРУТОЙ ДРОП! Выпало: <b>+{win} Prince Coins!</b>"
        elif drop_type == "jackpot":
            win = 5000
            msg_drop = f"💎 МЕГА-ДЖЕКПОТ ИЗ КЕЙСА! Выпало: <b>+{win} Prince Coins!! 🚀</b>"
        else:
            win = 1000
            db["admins"].add(user_id)
            db["admin_prefixes"][str(user_id)] = "⭐ VIP Легенда"
            msg_drop = f"👑 СВЕРХРЕДКИЙ ДРОП! Ты выбил статус <b>⭐ VIP Легенда</b> и +{win} Coins!"

        db["user_scores"][str(user_id)] += win
        save_data()
        
        new_bal = db["user_scores"].get(str(user_id), 0)
        case_text = (
            "<b>📦 ОТКРЫТИЕ СЕКРЕТНОГО КЕЙСА 🔥</b>\n"
            "───────────────────────────────\n"
            f"{msg_drop}\n\n"
            f"🏦 Твой новый баланс: <b>{new_bal} Coins</b>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(
            types.InlineKeyboardButton("🔄 Крутить еще раз (250)", callback_data="btn_case"),
            types.InlineKeyboardButton("🔙 В меню", callback_data="btn_main_menu")
        )
        bot.edit_message_text(case_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    # ТОП БОГАЧЕЙ
    elif call.data == "btn_top":
        sorted_users = sorted(db["user_scores"].items(), key=lambda x: x[1], reverse=True)[:10]
        top_text = "<b>🏆 ТОП-10 ОЛИГАРХОВ ПРОЕКТА</b>\n───────────────────────────────\n"
        
        for idx, (uid, score) in enumerate(sorted_users, 1):
            medal = "🥇" if idx == 1 else ("🥈" if idx == 2 else ("🥉" if idx == 3 else f"<b>{idx}.</b>"))
            role = db["admin_prefixes"].get(str(uid), "Игрок")
            top_text += f"{medal} <code>{uid}</code> [{role}] — <b>{score} Coins</b>\n"
            
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(top_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    # ПРОМОКОДЫ
    elif call.data == "btn_promo":
        user_states[user_id] = 'enter_promo'
        bot.edit_message_text(
            "<b>🎟 Активация промокода Prince Russia</b>\n"
            "───────────────────────────────\n"
            "Введи секретный промокод в чат:",
            chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb()
        )

    # ЕЖЕДНЕВНЫЙ БОНУС
    elif call.data == "btn_daily":
        today = datetime.now().strftime("%Y-%m-%d")
        last_claim = db["daily_bonus"].get(str(user_id))

        if last_claim == today:
            bot.answer_callback_query(call.id, "⏳ Бонус уже получен сегодня! Заглядывай завтра.", show_alert=True)
            return

        db["daily_bonus"][str(user_id)] = today
        bonus_amount = random.randint(200, 500)
        db["user_scores"][str(user_id)] = db["user_scores"].get(str(user_id), 0) + bonus_amount
        save_data()

        coins = db["user_scores"].get(str(user_id), 0)
        bot.answer_callback_query(call.id, f"🎉 УУФФФ! Забран бонус +{bonus_amount} Coins!", show_alert=True)
        
        daily_text = (
            "<b>🎁 ЕЖЕДНЕВНЫЙ БОНУС GOD MODE 🔥</b>\n"
            "───────────────────────────────\n"
            f"💰 Получено на счет: <b>+{bonus_amount} Prince Coins</b>\n"
            f"🏦 Твой баланс: <b>{coins} Coins</b>\n\n"
            "<i>Следующий бонус активируется через 24 часа!</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(daily_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "btn_transfer":
        user_states[user_id] = 'transfer_step1'
        bot.edit_message_text(
            "<b>💸 Перевод Prince Coins игроку</b>\n"
            "───────────────────────────────\n"
            "Введи Telegram ID или @username получателя:",
            chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb()
        )

    elif call.data == "btn_shop":
        shop_text = (
            "<b>🛒 DONATE SHOP — PRINCE RUSSIA</b>\n"
            "───────────────────────────────\n"
            "Хочешь эксклюзивный транспорт, випку или кучу коинов? Пиши напрямую руководству:\n\n"
            "🔹 <b>Telegram:</b> @AsikWhiskey\n"
            "🔹 <b>ВКонтакте:</b> https://vk.com/asik_whiskey\n\n"
            "⚠️ <i>Остерегайся фейков! Покупки только по контактам выше.</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_main_menu"))
        bot.edit_message_text(shop_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb, disable_web_page_preview=True)

    elif call.data == "btn_casino":
        coins = db["user_scores"].get(str(user_id), 0)
        casino_text = (
            "<b>🎰 PRINCE CASINO — GOD MODE 🔥</b>\n"
            "───────────────────────────────\n"
            f"💰 Твой баланс: <b>{coins} Prince Coins</b>\n\n"
            "Выбирай игровой режим:"
        )
        bot.edit_message_text(casino_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_casino_kb())

    elif call.data == "casino_dice":
        user_states[user_id] = 'casino_bet_dice'
        bot.edit_message_text(
            "<b>🎲 Казино: Игра в Кости</b>\n"
            "───────────────────────────────\n"
            "Введи сумму ставки в Coins:",
            chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb()
        )

    elif call.data == "casino_slots":
        user_states[user_id] = 'casino_bet_slots'
        bot.edit_message_text(
            "<b>🎰 Казино: Слоты (Джекпот)</b>\n"
            "───────────────────────────────\n"
            "Введи сумму ставки в Coins:",
            chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb()
        )

    elif call.data == "btn_test_server":
        if not db["test_server_open"]:
            bot.answer_callback_query(call.id, "⛔️ Набор на тест-сервер закрыт!", show_alert=True)
            return

        user_states[user_id] = 'test_step1'
        test_applications[user_id] = {}
        text = (
            "<b>🧪 Заявка на Тест-Сервер Prince Russia</b>\n"
            "───────────────────────────────\n"
            "<b>Шаг 1 из 4:</b> Введи свой игровой ник (например: <code>Alex_Prince</code>):"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data.startswith("test_accept_") or call.data.startswith("test_decline_"):
        if user_id not in db["admins"]:
            bot.answer_callback_query(call.id, "Нет прав!", show_alert=True)
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
        bot.send_message(user_id, "📝 <b>Введи причину вердикта:</b>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "adm_toggle_test":
        if user_id in db["admins"]:
            db["test_server_open"] = not db["test_server_open"]
            save_data()
            st = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
            bot.answer_callback_query(call.id, f"Набор теперь {st}!")
            bot.edit_message_text("<b>⚡️ Панель Управления:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data == "btn_game":
        coins = db["user_scores"].get(str(user_id), 0)
        text = (
            "<b>🎮 Мини-Игра «Угадай Число»</b>\n"
            "───────────────────────────────\n"
            f"💰 Твой баланс: <b>{coins} Prince Coins</b>\n\n"
            "Выбирай уровень сложности:"
        )
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_game_inline_kb())

    elif call.data in ["game_easy", "game_medium", "game_hard"]:
        max_val, reward = (10, 10) if call.data == "game_easy" else ((50, 50) if call.data == "game_medium" else (100, 150))
        games[user_id] = {'secret': random.randint(1, max_val), 'attempts': 0, 'reward': reward}
        user_states[user_id] = 'playing_game'
        bot.edit_message_text(f"🎯 Загадано число от 1 до {max_val}!\nНаграда: +{reward} Coins\nНапиши вариант в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "btn_rules":
        rules_text = (
            "<b>📜 Правила & FAQ — Prince Russia</b>\n"
            "───────────────────────────────\n"
            "1. Запрещены оскорбления игроков и администрации.\n"
            "2. Использование читов = перманентный бан.\n"
            "3. Спам и реклама запрещены.\n\n"
            "<b>Как начать играть?</b>\n"
            "<i>Скачивай лаунчер с нашего сайта или группы VK!</i>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад в меню", callback_data="btn_main_menu"))
        bot.edit_message_text(rules_text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "btn_links":
        bot.edit_message_text("<b>🌐 Официальные ресурсы Prince Russia</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_links_inline_kb())

    elif call.data == "btn_idea":
        user_states[user_id] = 'idea'
        bot.edit_message_text("💡 Опиши свою идею или предложение в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "btn_support":
        user_states[user_id] = 'support'
        bot.edit_message_text("🛠 Опиши свою проблему или вопрос в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "btn_cancel":
        user_states[user_id] = None
        admin_reply_targets[user_id] = None
        test_applications.pop(user_id, None)
        pending_test_actions.pop(user_id, None)
        bot.answer_callback_query(call.id, "Отменено.")
        bot.edit_message_text("<b>Главное меню:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    elif call.data == "btn_admin_panel":
        if user_id in db["admins"]:
            bot.edit_message_text("<b>⚡️ Панель Высшего Руководства:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data.startswith("reply_to_"):
        if user_id not in db["admins"]: return
        target_id = int(call.data.replace("reply_to_", ""))
        admin_reply_targets[user_id] = target_id
        bot.send_message(user_id, f"📝 Введи ответ игроку (ID: <code>{target_id}</code>):", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "adm_stats":
        if user_id in db["admins"]:
            t_status = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
            silent = "ВКЛ 🔕" if db["silent_mode"] else "ВЫКЛ 🔔"
            text = f"<b>📊 Статистика проекта:</b>\nИгроков в базе: {len(db['all_users'])}\nАдминистраторов: {len(db['admins'])}\nЗаблокированных: {len(db['banned_users'])}\nПромокодов создано: {len(db['promo_codes'])}\nНабор на тест: {t_status}\nТихий режим: {silent}"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_add":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "<b>➕ Назначение админа:</b>\nВведи @username или ID:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_add_admin)

    elif call.data == "adm_remove":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "<b>➖ Снятие админа:</b>\nВведи @username или ID:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_remove_admin)

    elif call.data == "adm_prefix":
        if can_user_change_prefixes(user_id):
            msg = bot.send_message(user_id, "<b>🏷 Смена префикса:</b>\nВведи ID/username и через пробел новый префикс:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_set_prefix)
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав!", show_alert=True)

    elif call.data == "adm_give_coins":
        if can_user_change_prefixes(user_id):
            msg = bot.send_message(user_id, "<b>💰 Выдача/Списание Coins:</b>\nВведи ID или @username и сумму (+/-):", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_give_coins)
        else:
            bot.answer_callback_query(call.id, "❌ Только для руководства!", show_alert=True)

    elif call.data == "adm_ban":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "<b>🔒 Бан игрока:</b>\nВведи ID или username нарушителя:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_ban_user)

    elif call.data == "adm_unban":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "<b>🔓 Разбан игрока:</b>\nВведи ID или username:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_unban_user)

    elif call.data == "adm_send_direct":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "<b>✉️ Сообщение игроку:</b>\nВведи Telegram ID или @username:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_direct_msg_input)

    elif call.data == "adm_lookup":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "<b>🔍 Пробив игрока:</b>\nВведи Telegram ID или @username:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_lookup_user)

    elif call.data == "adm_wipe_balance":
        if can_user_change_prefixes(user_id):
            msg = bot.send_message(user_id, "<b>🧹 Обнуление баланса:</b>\nВведи ID или @username:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_wipe_balance)
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав!", show_alert=True)

    elif call.data == "adm_create_promo":
        if can_user_change_prefixes(user_id):
            msg = bot.send_message(user_id, "<b>🎟 Создание промокода:</b>\nВведи название и через пробел сумму награды (Пример: <code>PRINCE 1000</code>):", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_create_promo)
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав!", show_alert=True)

    elif call.data == "adm_delete_promo":
        if can_user_change_prefixes(user_id):
            msg = bot.send_message(user_id, "<b>🗑 Удаление промокода:</b>\nВведи название промокода:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_delete_promo)
        else:
            bot.answer_callback_query(call.id, "❌ Недостаточно прав!", show_alert=True)

    elif call.data == "adm_set_deputy":
        if user_id == DEV_ID:
            msg = bot.send_message(user_id, "<b>👑 Назначение Зама:</b>\nВведи ID или @username:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_set_deputy)
        else:
            bot.answer_callback_query(call.id, "❌ Только для Главного Разработчика!", show_alert=True)

    elif call.data == "adm_set_dev":
        if user_id == DEV_ID:
            msg = bot.send_message(user_id, "<b>💻 Назначение Разраба:</b>\nВведи ID или @username:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_set_dev)
        else:
            bot.answer_callback_query(call.id, "❌ Только для Главного Разработчика!", show_alert=True)

    elif call.data == "adm_toggle_silent":
        if user_id in db["admins"]:
            db["silent_mode"] = not db["silent_mode"]
            save_data()
            st = "ВКЛЮЧЕН 🔕" if db["silent_mode"] else "ВЫКЛЮЧЕН 🔔"
            bot.answer_callback_query(call.id, f"Тихий режим теперь {st}!")
            bot.edit_message_text("<b>⚡️ Панель Управления:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data == "adm_export_db":
        if user_id == DEV_ID:
            try:
                with open(DB_FILE, "rb") as f:
                    bot.send_document(user_id, f, caption="📂 <b>Резервная копия database.json</b>", parse_mode="HTML")
                bot.answer_callback_query(call.id, "База выгружена!")
            except Exception as e:
                bot.answer_callback_query(call.id, f"Ошибка: {e}", show_alert=True)
        else:
            bot.answer_callback_query(call.id, "❌ Только для Главного Разработчика!", show_alert=True)

    elif call.data == "adm_list":
        if user_id in db["admins"]:
            text = "<b>📋 Список Администрации:</b>\n\n"
            for adm in db["admins"]:
                pref = db["admin_prefixes"].get(str(adm), "Админ")
                text += f"• <code>{adm}</code> — <b>{pref}</b>\n"
            kb = types.InlineKeyboardMarkup()
            kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
            bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_broadcast":
        if user_id in db["admins"]:
            msg = bot.send_message(user_id, "<b>📢 Массовая рассылка:</b>\nОтправь пост для рассылки игрокам:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
            bot.register_next_step_handler(msg, process_broadcast)

# --- АДМИН УТИЛИТЫ И ПРОМО ---
def process_create_promo(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    try:
        parts = message.text.strip().split(" ", 1)
        code = parts[0].upper()
        reward = int(parts[1])
        db["promo_codes"][code] = reward
        save_data()
        bot.send_message(message.chat.id, f"✅ Промокод <code>{code}</code> на <b>{reward} Coins</b> успешно создан!", parse_mode="HTML")
    except Exception:
        bot.send_message(message.chat.id, "❌ Ошибка формата! Пример: <code>PRINCE 500</code>", parse_mode="HTML")

def process_delete_promo(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    code = message.text.strip().upper()
    if code in db["promo_codes"]:
        db["promo_codes"].pop(code)
        save_data()
        bot.send_message(message.chat.id, f"✅ Промокод <code>{code}</code> удален!", parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "❌ Промокод не найден.")

def process_add_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid:
        db["admins"].add(tid)
        db["admin_prefixes"][str(tid)] = "🛡 Главный Администратор"
        save_data()
        bot.send_message(message.chat.id, f"✅ Назначен админом: <code>{tid}</code>", parse_mode="HTML")
        try: bot.send_message(tid, "🎉 Руководство назначило тебя Администратором проекта!", parse_mode="HTML")
        except Exception: pass
    else: bot.send_message(message.chat.id, "❌ Игрок не найден в базе.")

def process_remove_admin(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid and tid != DEV_ID:
        db["admins"].discard(tid)
        db["admin_prefixes"].pop(str(tid), None)
        save_data()
        bot.send_message(message.chat.id, f"✅ Права сняты с <code>{tid}</code>", parse_mode="HTML")
    else: bot.send_message(message.chat.id, "❌ Нельзя снять права у Создателя.")

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
            bot.send_message(message.chat.id, f"✅ Префикс изменен на: <b>{pref}</b>", parse_mode="HTML")
            try: bot.send_message(tid, f"🏷 Твой префикс изменен на: <b>{pref}</b>", parse_mode="HTML")
            except Exception: pass
        else: bot.send_message(message.chat.id, "❌ Админ не найден.")
    except Exception: bot.send_message(message.chat.id, "❌ Ошибка формата.", parse_mode="HTML")

def process_give_coins(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    try:
        parts = message.text.strip().split(" ", 1)
        ustr = parts[0].replace("@", "").lower()
        amount = int(parts[1])
        tid = db["username_to_id"].get(ustr) or (int(ustr) if ustr.isdigit() else None)
        
        if tid:
            current = db["user_scores"].get(str(tid), 0)
            db["user_scores"][str(tid)] = current + amount
            save_data()
            bot.send_message(message.chat.id, f"✅ Баланс игрока <code>{tid}</code> изменен на <b>{amount:+d} Coins</b>!", parse_mode="HTML")
            try: bot.send_message(tid, f"🎁 Руководство обновило твой баланс: <b>{amount:+d} Prince Coins</b>!", parse_mode="HTML")
            except Exception: pass
        else:
            bot.send_message(message.chat.id, "❌ Игрок не найден.")
    except Exception:
        bot.send_message(message.chat.id, "❌ Ошибка! Пример: <code>@username 1000</code>", parse_mode="HTML")

def process_ban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid and tid not in db["admins"]:
        db["banned_users"].add(tid)
        save_data()
        bot.send_message(message.chat.id, f"⛔️ Игрок <code>{tid}</code> заблокирован.", parse_mode="HTML")
        try: bot.send_message(tid, "⛔️ Ты заблокирован администрацией Prince Russia.", parse_mode="HTML")
        except Exception: pass
    else: bot.send_message(message.chat.id, "❌ Нельзя заблокировать администратора.")

def process_unban_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid in db["banned_users"]:
        db["banned_users"].remove(tid)
        save_data()
        bot.send_message(message.chat.id, f"✅ Игрок <code>{tid}</code> разблокирован.", parse_mode="HTML")
        try: bot.send_message(tid, "✅ Твоя блокировка снята!", parse_mode="HTML")
        except Exception: pass
    else: bot.send_message(message.chat.id, "❌ Игрок не найден в бане.")

def process_direct_msg_input(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid:
        admin_reply_targets[message.chat.id] = tid
        bot.send_message(message.chat.id, f"📝 Введи текст или медиа для отправки игроку (ID: <code>{tid}</code>):", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
    else:
        bot.send_message(message.chat.id, "❌ Игрок не найден.")

def process_lookup_user(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid:
        bal = db["user_scores"].get(str(tid), 0)
        role = db["admin_prefixes"].get(str(tid), "👑 Игрок")
        is_ban = "Да ⛔️" if tid in db["banned_users"] else "Нет (Чист) ✅"
        is_adm = "Да 🛡" if tid in db["admins"] else "Нет"
        
        info = (
            f"<b>🔍 ДОСЬЕ ИГРОКА:</b>\n"
            f"───────────────────────────────\n"
            f"🆔 <b>ID:</b> <code>{tid}</code>\n"
            f"📛 <b>Роль:</b> {role}\n"
            f"💰 <b>Баланс:</b> {bal} Coins\n"
            f"🛡 <b>Админ:</b> {is_adm}\n"
            f"⛔️ <b>В бане:</b> {is_ban}"
        )
        bot.send_message(message.chat.id, info, parse_mode="HTML", reply_markup=get_admin_inline_kb(message.chat.id))
    else:
        bot.send_message(message.chat.id, "❌ Игрок не найден.")

def process_wipe_balance(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid:
        db["user_scores"][str(tid)] = 0
        save_data()
        bot.send_message(message.chat.id, f"🧹 Баланс игрока <code>{tid}</code> обнулен!", parse_mode="HTML")
        try: bot.send_message(tid, "🧹 Твой баланс коинов был аннулирован администрацией.", parse_mode="HTML")
        except Exception: pass
    else: bot.send_message(message.chat.id, "❌ Игрок не найден.")

def process_set_deputy(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid:
        db["admins"].add(tid)
        db["admin_prefixes"][str(tid)] = "🔱 Зам. Владельца"
        save_data()
        bot.send_message(message.chat.id, f"✅ Игрок <code>{tid}</code> назначен <b>🔱 Зам. Владельца</b>!", parse_mode="HTML")
        try: bot.send_message(tid, "👑 Тебе присвоен элитный статус <b>🔱 Зам. Владельца проекта</b>!", parse_mode="HTML")
        except Exception: pass
    else: bot.send_message(message.chat.id, "❌ Игрок не найден.")

def process_set_dev(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    inp = message.text.strip().replace("@", "").lower()
    tid = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
    if tid:
        db["admins"].add(tid)
        db["admin_prefixes"][str(tid)] = "💻 Разработчик"
        save_data()
        bot.send_message(message.chat.id, f"✅ Игрок <code>{tid}</code> назначен <b>💻 Разработчиком</b>!", parse_mode="HTML")
        try: bot.send_message(tid, "💻 Тебе присвоен статус <b>💻 Разработчик проекта</b>!", parse_mode="HTML")
        except Exception: pass
    else: bot.send_message(message.chat.id, "❌ Игрок не найден.")

def process_broadcast(message):
    if message.text in ["❌ Отмена", "/cancel"]: return
    count = 0
    for uid in list(db["all_users"]):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            count += 1
        except Exception: pass
    bot.send_message(message.chat.id, f"📢 Рассылка завершена!\nДоставлено игрокам: <b>{count}/{len(db['all_users'])}</b>", parse_mode="HTML")

# --- ОБРАБОТКА ТЕКСТА И ИГР ---
@bot.message_handler(content_types=['text', 'photo', 'video', 'animation', 'voice', 'video_note', 'document', 'sticker', 'audio'])
def handle_all_messages(message):
    user_id = message.chat.id
    register_user(message.from_user)

    if user_id in db["banned_users"]: return

    state = user_states.get(user_id)
    is_replying = user_id in db["admins"] and admin_reply_targets.get(user_id)
    user_bal = db["user_scores"].get(str(user_id), 0)

    # АКТИВАЦИЯ ПРОМОКОДА ИГРОКОМ
    if state == 'enter_promo' and message.content_type == 'text':
        code = message.text.strip().upper()
        user_states[user_id] = None

        if code in db["promo_codes"]:
            used_list = db["used_promos"].get(str(user_id), [])
            if code in used_list:
                bot.send_message(user_id, "❌ Ты уже активировал этот промокод ранее!", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
                return

            reward = db["promo_codes"][code]
            db["user_scores"][str(user_id)] = db["user_scores"].get(str(user_id), 0) + reward
            used_list.append(code)
            db["used_promos"][str(user_id)] = used_list
            save_data()

            bot.send_message(user_id, f"🎉 <b>УУФФФ! Промокод <code>{code}</code> успешно активирован!</b>\n💰 Получено на баланс: <b>+{reward} Coins</b> 🔥", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        else:
            bot.send_message(user_id, "❌ Неверный промокод или срок его действия истек.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        return

    # ПЕРЕВОД МОНЕТ
    if state == 'transfer_step1' and message.content_type == 'text':
        inp = message.text.strip().replace("@", "").lower()
        target_id = db["username_to_id"].get(inp) or (int(inp) if inp.isdigit() else None)
        
        if not target_id or target_id == user_id:
            bot.send_message(user_id, "❌ Игрок не найден или нельзя переводить себе!", reply_markup=get_cancel_inline_kb())
            return
        
        user_states[user_id + 1000000000] = target_id
        user_states[user_id] = 'transfer_step2'
        bot.send_message(user_id, f"💵 Игрок найден (ID: <code>{target_id}</code>).\nВведи сумму Prince Coins для перевода:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'transfer_step2' and message.content_type == 'text':
        if message.text.isdigit():
            amount = int(message.text)
            target_id = user_states.get(user_id + 1000000000)

            if amount <= 0 or amount > user_bal:
                bot.send_message(user_id, f"❌ Неверная сумма! У тебя на балансе: <b>{user_bal} Coins</b>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
                return

            db["user_scores"][str(user_id)] -= amount
            db["user_scores"][str(target_id)] = db["user_scores"].get(str(target_id), 0) + amount
            save_data()

            user_states[user_id] = None
            user_states.pop(user_id + 1000000000, None)

            bot.send_message(user_id, f"✅ Ты успешно перевел <b>{amount} Prince Coins</b> игроку <code>{target_id}</code>!", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
            try:
                bot.send_message(target_id, f"💸 Тебе пришел перевод в размере <b>{amount} Prince Coins</b> от игрока <code>{user_id}</code>!", parse_mode="HTML")
            except Exception: pass
        return

    # КАЗИНО: КОСТИ
    if state == 'casino_bet_dice' and message.content_type == 'text':
        if message.text.isdigit():
            bet = int(message.text)
            if bet <= 0 or bet > user_bal:
                bot.send_message(user_id, f"❌ Неверная ставка! Баланс: <b>{user_bal} Coins</b>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
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
                bot.send_message(user_id, f"🎉 <b>УУФФФ! Выпало {score}! Ты сорвал куш х2 и выиграл {win_amount} Coins! 🔥</b>", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
            else:
                bot.send_message(user_id, f"😢 Выпало {score}. Ты проиграл {bet} Coins.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        return

    # КАЗИНО: СЛОТЫ
    elif state == 'casino_bet_slots' and message.content_type == 'text':
        if message.text.isdigit():
            bet = int(message.text)
            if bet <= 0 or bet > user_bal:
                bot.send_message(user_id, f"❌ Неверная ставка! Баланс: <b>{user_bal} Coins</b>", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
                return
            
            db["user_scores"][str(user_id)] -= bet
            save_data()
            user_states[user_id] = None

            bot.send_message(user_id, "🎰 Крутим слоты...")
            sent_slot = bot.send_dice(user_id, emoji='🎰')
            time.sleep(3)
            val = sent_slot.dice.value

            if val in [1, 22, 43, 64]:
                win_amount = bet * 5
                db["user_scores"][str(user_id)] += win_amount
                save_data()
                bot.send_message(user_id, f"🎰💎 <b>УУФФФ МЕГА ДЖЕКПОТ х5! Выиграно {win_amount} Coins! 🚀</b>", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
            elif val % 2 == 0:
                win_amount = int(bet * 1.5)
                db["user_scores"][str(user_id)] += win_amount
                save_data()
                bot.send_message(user_id, f"✨ Успех! Выиграно {win_amount} Coins!", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
            else:
                bot.send_message(user_id, f"💨 Не фартануло (-{bet} Coins).", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        return

    # ВВОД ПРИЧИНЫ ДЛЯ ТЕСТА
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
                user_msg = f"🎉 <b>Твоя заявка на Тест-Сервер ОДОБРЕНА! Уффф!</b>\n💬 <b>Комментарий:</b> {reason}\nС тобой скоро свяжутся."
            else:
                status_text = f"❌ <b>Заявка ОТКЛОНЕНА</b> ({prefix} {admin_uname})\n💬 <b>Причина:</b> {reason}"
                user_msg = f"❌ <b>Твоя заявка на Тест-Сервер отклонена.</b>\n💬 <b>Причина:</b> {reason}"
            
            try:
                bot.edit_message_text(act_info['card_text'] + f"\n\n───────────────────────────────\n{status_text}", chat_id=user_id, message_id=act_info['msg_id'], parse_mode="HTML")
            except Exception: pass

            try: bot.send_message(target_id, user_msg, parse_mode="HTML")
            except Exception: pass
            
            bot.send_message(user_id, "✅ Вердикт отправлен игроку!", reply_markup=get_admin_inline_kb(user_id))
            user_states[user_id] = None
            pending_test_actions.pop(user_id, None)
        return

    # ПОШАГОВАЯ ЗАЯВКА НА ТЕСТ
    if state == 'test_step1' and message.content_type == 'text':
        test_applications[user_id]['nick'] = message.text.strip()
        user_states[user_id] = 'test_step2'
        bot.send_message(user_id, "<b>Шаг 2 из 4:</b> Введи свой реальный возраст:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step2' and message.content_type == 'text':
        test_applications[user_id]['age'] = message.text.strip()
        user_states[user_id] = 'test_step3'
        bot.send_message(user_id, "<b>Шаг 3 из 4:</b> Введи ссылку на свой VK профиль:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step3' and message.content_type == 'text':
        test_applications[user_id]['vk'] = message.text.strip()
        user_states[user_id] = 'test_step4'
        bot.send_message(user_id, "<b>Шаг 4 из 4:</b> Опиши свой опыт в тестировании:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
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

        bot.send_message(user_id, "🎉 <b>Заявка успешно отправлена!</b> Ожидай решения руководства.", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
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
                bot.send_message(user_id, f"🎉 <b>ПОБЕДА УФФФ! Число {secret} угадано!</b>\n💰 Получено: +{gdata['reward']} Coins", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
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

        bot.send_message(user_id, "✅ Сообщение успешно доставлено руководству!", parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
        user_states[user_id] = None

    else:
        bot.send_message(user_id, "ℹ️ Выбери нужный пункт меню:", reply_markup=get_main_inline_kb(user_id))

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
