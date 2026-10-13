import telebot
from telebot import types
import random
import json
import os
import time
from flask import Flask
from threading import Thread

# --- НАСТРОЙКИ ---
TOKEN = "8854430576:AAG5XqMZjIJtCG202WtUgU6PFbX-iy1gQU4"
DEV_ID = 8543358373  # Твой Telegram ID

bot = telebot.TeleBot(TOKEN)
DB_FILE = "database.json"

# --- 24/7 СЕРВЕР ДЛЯ RENDER ---
app = Flask('')

@app.route('/')
def home():
    return "<h1>Prince Russia Core Engine v7.0 Ultimate Buttons Edition is Online!</h1>"

def run_web():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# --- ДОСТУПНЫЕ РОЛИ ---
CAN_MANAGE_PREFIXES = ["💻 Разработчик", "👑 Владелец Проекта", "🔱 Зам. Владельца"]
AVAILABLE_ROLES = [
    "💻 Разработчик", 
    "👑 Владелец Проекта", 
    "🔱 Зам. Владельца", 
    "🛡 Главный Администратор", 
    "⭐ Старший Администратор", 
    "🛠 Администратор"
]

# --- БАЗА ДАННЫХ ---
def load_data():
    default_data = {
        "admins": [DEV_ID],
        "admin_prefixes": {str(DEV_ID): "💻 Разработчик"},
        "all_users": [DEV_ID],
        "banned_users": [],
        "user_names": {str(DEV_ID): "Evgenii (Dev)"},
        "user_scores": {},
        "user_exp": {},
        "test_server_open": False
    }
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                admins = list(set(data.get("admins", [DEV_ID])))
                if DEV_ID not in admins: admins.append(DEV_ID)
                all_users = list(set(data.get("all_users", [DEV_ID])))
                if DEV_ID not in all_users: all_users.append(DEV_ID)
                admin_prefixes = data.get("admin_prefixes", {})
                admin_prefixes[str(DEV_ID)] = "💻 Разработчик"
                return {
                    "admins": admins,
                    "admin_prefixes": admin_prefixes,
                    "all_users": all_users,
                    "banned_users": data.get("banned_users", []),
                    "user_names": data.get("user_names", {}),
                    "user_scores": data.get("user_scores", {}),
                    "user_exp": data.get("user_exp", {}),
                    "test_server_open": data.get("test_server_open", False)
                }
        except Exception:
            return default_data
    return default_data

def save_data():
    data_to_save = {
        "admins": list(set(db["admins"])),
        "admin_prefixes": db["admin_prefixes"],
        "all_users": list(set(db["all_users"])),
        "banned_users": list(set(db["banned_users"])),
        "user_names": db["user_names"],
        "user_scores": db["user_scores"],
        "user_exp": db["user_exp"],
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
    str_uid = str(user_id)
    if user_id not in db["all_users"]:
        db["all_users"].append(user_id)
    if str_uid not in db["user_scores"]:
        db["user_scores"][str_uid] = 100
    if str_uid not in db["user_exp"]:
        db["user_exp"][str_uid] = 0
    
    name_str = f"@{user.username}" if user.username else user.first_name
    db["user_names"][str_uid] = name_str
    save_data()

def add_exp(user_id, amount):
    str_uid = str(user_id)
    db["user_exp"][str_uid] = db["user_exp"].get(str_uid, 0) + amount
    save_data()

def get_user_lvl(user_id):
    return (db["user_exp"].get(str(user_id), 0) // 50) + 1

def get_main_inline_kb(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("👤 Профиль", callback_data="btn_profile"),
        types.InlineKeyboardButton("🎰 Казино", callback_data="btn_casino")
    )
    kb.add(
        types.InlineKeyboardButton("🛒 Донат", callback_data="btn_shop"),
        types.InlineKeyboardButton("🧪 Тест-Сервер", callback_data="btn_test_server")
    )
    kb.add(
        types.InlineKeyboardButton("💡 Идеи", callback_data="btn_idea"),
        types.InlineKeyboardButton("🛠 Поддержка", callback_data="btn_support")
    )
    kb.add(
        types.InlineKeyboardButton("📜 Правила", callback_data="btn_rules"),
        types.InlineKeyboardButton("🌐 Ресурсы", callback_data="btn_links")
    )
    if user_id in db["admins"]:
        kb.add(types.InlineKeyboardButton("⚡ АДМИН-ПАНЕЛЬ ⚡", callback_data="btn_admin_panel"))
    return kb

def get_links_inline_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🌐 Сайт", url="https://site-prince-russia.samp.date"),
        types.InlineKeyboardButton("💬 Форум", url="https://forum-prince-russia.samp.date")
    )
    kb.add(
        types.InlineKeyboardButton("📢 Telegram", url="https://t.me/prince_russiaa"),
        types.InlineKeyboardButton("🔹 VK", url="https://vk.ru/princerussiaa")
    )
    kb.add(types.InlineKeyboardButton("🔙 Главное меню", callback_data="btn_main_menu"))
    return kb

def get_cancel_inline_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("❌ Отмена", callback_data="btn_cancel"))
    return kb

def get_admin_inline_kb(user_id):
    kb = types.InlineKeyboardMarkup(row_width=2)
    status_icon = "🔓" if db["test_server_open"] else "🔒"
    kb.add(types.InlineKeyboardButton(f"{status_icon} Тест: {'ОТКРЫТ' if db['test_server_open'] else 'ЗАКРЫТ'}", callback_data="adm_toggle_test"))
    kb.add(
        types.InlineKeyboardButton("➕ Назначить админа", callback_data="adm_add_menu"),
        types.InlineKeyboardButton("➖ Снять админа", callback_data="adm_remove_menu")
    )
    kb.add(
        types.InlineKeyboardButton("🏷 Изменить префикс", callback_data="adm_prefix_menu"),
        types.InlineKeyboardButton("📋 Состав команды", callback_data="adm_list")
    )
    kb.add(
        types.InlineKeyboardButton("🔒 Забанить игрока", callback_data="adm_ban_menu"),
        types.InlineKeyboardButton("🔓 Разбанить", callback_data="adm_unban_menu")
    )
    kb.add(
        types.InlineKeyboardButton("✉️ Написать игроку", callback_data="adm_pm_menu"),
        types.InlineKeyboardButton("📊 Статистика", callback_data="adm_stats")
    )
    kb.add(types.InlineKeyboardButton("📢 Рассылка", callback_data="adm_broadcast"))
    kb.add(types.InlineKeyboardButton("🔙 Главное меню", callback_data="btn_main_menu"))
    return kb

def get_users_list_kb(action_prefix):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for uid in db["all_users"]:
        if uid == DEV_ID and action_prefix in ["exec_rem", "exec_ban"]: continue
        name = db["user_names"].get(str(uid), f"ID: {uid}")
        kb.add(types.InlineKeyboardButton(f"👤 {name} ({uid})", callback_data=f"{action_prefix}_{uid}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
    return kb

def get_bans_list_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    if not db["banned_users"]:
        kb.add(types.InlineKeyboardButton("⚠️ Бан-лист пуст", callback_data="btn_admin_panel"))
    else:
        for uid in db["banned_users"]:
            name = db["user_names"].get(str(uid), f"ID: {uid}")
            kb.add(types.InlineKeyboardButton(f"🔓 Разбанить: {name} ({uid})", callback_data=f"unban_exec_{uid}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
    return kb

def get_roles_inline_kb(target_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    for role in AVAILABLE_ROLES:
        kb.add(types.InlineKeyboardButton(role, callback_data=f"setrole_{target_id}_{role}"))
    kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
    return kb

def get_casino_inline_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🎰 Слот-Машина (50 Coins)", callback_data="game_slot"),
        types.InlineKeyboardButton("🎯 Числовая рулетка", callback_data="btn_game_numbers"),
        types.InlineKeyboardButton("🔙 Главное меню", callback_data="btn_main_menu")
    )
    return kb

def get_game_inline_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🟢 Легкий (1-10) | +20 Coins", callback_data="game_easy"),
        types.InlineKeyboardButton("🟡 Средний (1-50) | +75 Coins", callback_data="game_medium"),
        types.InlineKeyboardButton("🔴 Хардкор (1-100) | +200 Coins", callback_data="game_hard"),
        types.InlineKeyboardButton("🔙 В казино", callback_data="btn_casino")
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

@bot.message_handler(commands=['start', 'menu', 'admin', 'panel'])
def start_cmd(message):
    user_id = message.chat.id
    register_user(message.from_user)
    user_states[user_id] = None
    
    coins = db["user_scores"].get(str(user_id), 100)
    lvl = get_user_lvl(user_id)
    
    text = (
        f"👑 <b>ПРОЕКТ PRINCE RUSSIA RP</b>\n"
        f"───────────────────────────────\n"
        f"🏆 Уровень: {lvl} LVL | 💰 Баланс: <code>{coins} Coins</code>\n\n"
        f"Управляйте всеми функциями через кнопки ниже:"
    )
    bot.send_message(user_id, text, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
    @bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    register_user(call.from_user)

    if user_id in db["banned_users"]:
        bot.answer_callback_query(call.id, "⛔ Вы заблокированы!", show_alert=True)
        return

    if call.data == "btn_main_menu":
        user_states[user_id] = None
        coins = db["user_scores"].get(str(user_id), 100)
        lvl = get_user_lvl(user_id)
        text = f"👑 <b>ГЛАВНОЕ МЕНЮ</b>\nБаланс: {coins} Coins | Уровень: {lvl}"
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    elif call.data == "btn_profile":
        str_uid = str(user_id)
        coins = db["user_scores"].get(str_uid, 100)
        exp = db["user_exp"].get(str_uid, 0)
        lvl = get_user_lvl(user_id)
        status = "Игрок"
        if user_id == DEV_ID: status = "💻 Главный Разработчик"
        elif user_id in db["admins"]: status = f"🛡 {db['admin_prefixes'].get(str_uid, 'Администратор')}"

        text = (
            f"👤 <b>ЛИЧНЫЙ КАБИНЕТ</b>\n"
            f"───────────────────────────────\n"
            f"Имя: <b>{call.from_user.first_name}</b>\n"
            f"ID: <code>{user_id}</code>\n"
            f"Статус: <b>{status}</b>\n"
            f"LVL: <b>{lvl}</b> | EXP: <b>{exp}</b> | Баланс: <b>{coins} Coins</b>"
        )
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Главное меню", callback_data="btn_main_menu"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "btn_casino":
        coins = db["user_scores"].get(str(user_id), 100)
        bot.edit_message_text(f"🎰 <b>КАЗИНО</b>\nБаланс: {coins} Coins", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_casino_inline_kb())

    elif call.data == "game_slot":
        str_uid = str(user_id)
        coins = db["user_scores"].get(str_uid, 100)
        if coins < 50:
            bot.answer_callback_query(call.id, "❌ Нужно 50 Coins!", show_alert=True)
            return
        db["user_scores"][str_uid] = coins - 50
        
        symbols = ["🍓", "🍋", "7️⃣", "💎", "🔔"]
        s1, s2, s3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)
        win = 500 if s1 == s2 == s3 == "7️⃣" else (250 if s1 == s2 == s3 else (75 if s1 == s2 or s2 == s3 or s1 == s3 else 0))
        
        db["user_scores"][str_uid] += win
        add_exp(user_id, 10)
        save_data()
        
        res_text = f"🎉 Выиграно +{win} Coins!" if win > 0 else "💔 Не повезло."
        text = f"🎰 <b>СЛОТЫ</b>\n[ {s1} | {s2} | {s3} ]\n{res_text}\nБаланс: {db['user_scores'][str_uid]} Coins"
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_casino_inline_kb())

    elif call.data == "btn_test_server":
        if not db["test_server_open"]:
            bot.answer_callback_query(call.id, "⛔ Набор закрыт!", show_alert=True)
            return
        user_states[user_id] = 'test_step1'
        test_applications[user_id] = {}
        bot.edit_message_text("🧪 <b>Шаг 1 из 3:</b> Введите ваш игровой никнейм в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data.startswith("test_accept_") or call.data.startswith("test_decline_"):
        if user_id not in db["admins"]: return
        is_accept = call.data.startswith("test_accept_")
        target_id = int(call.data.replace("test_accept_", "").replace("test_decline_", ""))
        pending_test_actions[user_id] = {'target_id': target_id, 'action': 'accept' if is_accept else 'decline', 'msg_id': call.message.message_id, 'card_text': call.message.text}
        user_states[user_id] = 'awaiting_test_reason'
        bot.answer_callback_query(call.id)
        bot.send_message(user_id, "📝 Напишите причину вердикта в чат:", reply_markup=get_cancel_inline_kb())

    elif call.data == "btn_game_numbers":
        bot.edit_message_text("🎯 <b>Числовая рулетка</b>\nВыберите сложность:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_game_inline_kb())

    elif call.data in ["game_easy", "game_medium", "game_hard"]:
        max_val, reward = (10, 20) if call.data == "game_easy" else ((50, 75) if call.data == "game_medium" else (100, 200))
        games[user_id] = {'secret': random.randint(1, max_val), 'attempts': 0, 'reward': reward}
        user_states[user_id] = 'playing_game'
        bot.edit_message_text(f"🎯 Угадайте число от 1 до {max_val}.\nНапишите число в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "btn_shop":
        bot.edit_message_text("🛒 <b>Донат:</b> Пишите разработчику: @Evgenn010", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
    elif call.data == "btn_rules":
        bot.edit_message_text("📜 <b>Правила:</b> Не читерить, уважать админов.", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))
    elif call.data == "btn_links":
        bot.edit_message_text("🌐 <b>Ресурсы:</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_links_inline_kb())
    elif call.data == "btn_idea":
        user_states[user_id] = 'idea'
        bot.edit_message_text("💡 Напишите вашу идею в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())
    elif call.data == "btn_support":
        user_states[user_id] = 'support'
        bot.edit_message_text("🛠 Опишите проблему в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())
    elif call.data == "btn_cancel":
        user_states[user_id] = None
        pending_test_actions.pop(user_id, None)
        bot.answer_callback_query(call.id, "Отменено.")
        bot.edit_message_text("👑 <b>Главное меню</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_main_inline_kb(user_id))

    elif call.data == "btn_admin_panel":
        if user_id in db["admins"]:
            bot.edit_message_text("⚡ <b>АДМИН-ПАНЕЛЬ</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
    elif call.data == "adm_toggle_test":
        if user_id in db["admins"]:
            db["test_server_open"] = not db["test_server_open"]
            save_data()
            bot.edit_message_text("⚡ <b>АДМИН-ПАНЕЛЬ</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
    
    elif call.data == "adm_add_menu":
        bot.edit_message_text("➕ Выберите игрока для назначения админом:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_users_list_kb("exec_add"))
    elif call.data == "adm_remove_menu":
        bot.edit_message_text("➖ Выберите админа для снятия:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_users_list_kb("exec_rem"))
    elif call.data == "adm_prefix_menu":
        bot.edit_message_text("🏷 Выберите админа для смены префикса:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_users_list_kb("exec_pref"))
    elif call.data == "adm_ban_menu":
        bot.edit_message_text("🔒 Выберите игрока для блокировки:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_users_list_kb("exec_ban"))
    elif call.data == "adm_unban_menu":
        bot.edit_message_text("🔓 Выберите забаненного игрока:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_bans_list_kb())
    elif call.data == "adm_pm_menu":
        bot.edit_message_text("✉️ Выберите игрока для сообщения:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_users_list_kb("exec_pm"))
    
    elif call.data.startswith("exec_add_"):
        target_id = int(call.data.replace("exec_add_", ""))
        if target_id not in db["admins"]: db["admins"].append(target_id)
        db["admin_prefixes"][str(target_id)] = "🛡 Главный Администратор"
        save_data()
        bot.answer_callback_query(call.id, "✅ Назначен администратором!", show_alert=True)
        bot.edit_message_text("⚡ <b>АДМИН-ПАНЕЛЬ</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))
    
    elif call.data.startswith("exec_rem_"):
        target_id = int(call.data.replace("exec_rem_", ""))
        if target_id != DEV_ID:
            if target_id in db["admins"]: db["admins"].remove(target_id)
            db["admin_prefixes"].pop(str(target_id), None)
            save_data()
        bot.answer_callback_query(call.id, "✅ Права сняты!", show_alert=True)
        bot.edit_message_text("⚡ <b>АДМИН-ПАНЕЛЬ</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data.startswith("exec_pref_"):
        target_id = int(call.data.replace("exec_pref_", ""))
        bot.edit_message_text(f"🏷 Выберите роль для ID <code>{target_id}</code>:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_roles_inline_kb(target_id))

    elif call.data.startswith("setrole_"):
        _, target_str, role_name = call.data.split("_", 2)
        target_id = int(target_str)
        db["admin_prefixes"][str(target_id)] = role_name
        save_data()
        bot.answer_callback_query(call.id, "✅ Префикс успешно изменен!", show_alert=True)
        bot.edit_message_text("⚡ <b>АДМИН-ПАНЕЛЬ</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data.startswith("exec_ban_"):
        target_id = int(call.data.replace("exec_ban_", ""))
        if target_id != DEV_ID and target_id not in db["banned_users"]:
            db["banned_users"].append(target_id)
            save_data()
        bot.answer_callback_query(call.id, "⛔ Пользователь заблокирован!", show_alert=True)
        bot.edit_message_text("⚡ <b>АДМИН-ПАНЕЛЬ</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data.startswith("unban_exec_"):
        target_id = int(call.data.replace("unban_exec_", ""))
        if target_id in db["banned_users"]:
            db["banned_users"].remove(target_id)
            save_data()
        bot.answer_callback_query(call.id, "🔓 Пользователь разблокирован!", show_alert=True)
        bot.edit_message_text("⚡ <b>АДМИН-ПАНЕЛЬ</b>", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_admin_inline_kb(user_id))

    elif call.data.startswith("exec_pm_"):
        target_id = int(call.data.replace("exec_pm_", ""))
        admin_reply_targets[user_id] = target_id
        bot.send_message(user_id, f"📝 Напишите личное сообщение для игрока (ID: <code>{target_id}</code>) в чат:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data == "adm_stats":
        t_status = "ОТКРЫТ 🔓" if db["test_server_open"] else "ЗАКРЫТ 🔒"
        text = f"📊 <b>Статистика:</b>\nИгроков: {len(db['all_users'])}\nАдминов: {len(db['admins'])}\nБанов: {len(db['banned_users'])}\nТест: {t_status}"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_list":
        text = "📋 <b>Состав команды:</b>\n\n"
        for adm in db["admins"]:
            pref = db["admin_prefixes"].get(str(adm), "Админ")
            name = db["user_names"].get(str(adm), f"ID: {adm}")
            text += f"• {name} (`{adm}`) — <b>{pref}</b>\n"
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🔙 Назад", callback_data="btn_admin_panel"))
        bot.edit_message_text(text, chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=kb)

    elif call.data == "adm_broadcast":
        user_states[user_id] = 'awaiting_broadcast'
        bot.edit_message_text("📢 Отправьте пост для массовой рассылки в чат:", chat_id=user_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_cancel_inline_kb())

    elif call.data.startswith("reply_to_"):
        target_id = int(call.data.replace("reply_to_", ""))
        admin_reply_targets[user_id] = target_id
        bot.send_message(user_id, f"📝 Напишите ответ игроку (ID: <code>{target_id}</code>):", parse_mode="HTML", reply_markup=get_cancel_inline_kb())

@bot.message_handler(content_types=['text', 'photo', 'video', 'animation', 'voice', 'document', 'sticker'])
def handle_all_messages(message):
    user_id = message.chat.id
    register_user(message.from_user)

    if user_id in db["banned_users"]: return

    state = user_states.get(user_id)
    is_replying = user_id in db["admins"] and admin_reply_targets.get(user_id)

    if state == 'awaiting_broadcast':
        count = 0
        for uid in list(set(db["all_users"])):
            try:
                bot.copy_message(uid, message.chat.id, message.message_id)
                count += 1
            except Exception: pass
        bot.send_message(user_id, f"📢 Рассылка завершена! Доставлено: {count}", reply_markup=get_main_inline_kb(user_id))
        user_states[user_id] = None
        return

    elif state == 'awaiting_test_reason':
        act_info = pending_test_actions.get(user_id)
        if act_info:
            target_id = act_info['target_id']
            is_accept = (act_info['action'] == 'accept')
            reason = message.text.strip()
            
            user_msg = f"🎉 <b>Ваша заявка на тест одобрена!</b>\n💬 Причина: {reason}" if is_accept else f"❌ <b>Ваша заявка отклонена.</b>\n💬 Причина: {reason}"
            try: bot.send_message(target_id, user_msg, parse_mode="HTML")
            except Exception: pass
            
            bot.send_message(user_id, "✅ Вердикт отправлен игроку!", reply_markup=get_admin_inline_kb(user_id))
            user_states[user_id] = None
            pending_test_actions.pop(user_id, None)
        return

    elif state == 'test_step1':
        test_applications[user_id]['nick'] = message.text.strip()
        user_states[user_id] = 'test_step2'
        bot.send_message(user_id, "<b>Шаг 2 из 3:</b> Укажите ваш возраст:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step2':
        test_applications[user_id]['age'] = message.text.strip()
        user_states[user_id] = 'test_step3'
        bot.send_message(user_id, "<b>Шаг 3 из 3:</b> Опишите ваш опыт:", parse_mode="HTML", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'test_step3':
        app_data = test_applications[user_id]
        card = f"🧪 <b>[ЗАЯВКА НА ТЕСТ]</b>\nИгрок: {message.from_user.first_name} (ID: <code>{user_id}</code>)\nНик: {app_data.get('nick')}\nВозраст: {app_data.get('age')}\nОпыт: {message.text}"
        for admin_id in db["admins"]:
            try: bot.send_message(admin_id, card, parse_mode="HTML", reply_markup=get_test_app_keyboard(user_id))
            except Exception: pass
        bot.send_message(user_id, "🎉 Заявка отправлена!", reply_markup=get_main_inline_kb(user_id))
        user_states[user_id] = None
        return

    elif state == 'playing_game' and message.text.isdigit():
        val = int(message.text)
        gdata = games.get(user_id, {'secret': 5, 'attempts': 0, 'reward': 20})
        gdata['attempts'] += 1
        if val == gdata['secret']:
            reward = gdata['reward']
            db["user_scores"][str(user_id)] = db["user_scores"].get(str(user_id), 100) + reward
            add_exp(user_id, 15)
            save_data()
            bot.send_message(user_id, f"🎉 Победа! +{reward} Coins", reply_markup=get_main_inline_kb(user_id))
            user_states[user_id] = None
            games.pop(user_id, None)
        elif val < gdata['secret']:
            bot.send_message(user_id, "📈 Число больше!", reply_markup=get_cancel_inline_kb())
        else:
            bot.send_message(user_id, "📉 Число меньше!", reply_markup=get_cancel_inline_kb())
        return

    elif state == 'idea':
        for admin_id in db["admins"]:
            try: bot.send_message(admin_id, f"💡 <b>ИДЕЯ от {message.from_user.first_name}</b> (ID: <code>{user_id}</code>)")
            except Exception: pass
            try: bot.copy_message(admin_id, user_id, message.message_id, reply_markup=get_reply_keyboard(user_id))
            except Exception: pass
        bot.send_message(user_id, "✅ Идея отправлена!", reply_markup=get_main_inline_kb(user_id))
        user_states[user_id] = None
        return

    elif state == 'support':
        for admin_id in db["admins"]:
            try: bot.send_message(admin_id, f"🛠 <b>ТИКЕТ от {message.from_user.first_name}</b> (ID: <code>{user_id}</code>)")
            except Exception: pass
            try: bot.copy_message(admin_id, user_id, message.message_id, reply_markup=get_reply_keyboard(user_id))
            except Exception: pass
        bot.send_message(user_id, "✅ Тикет создан!", reply_markup=get_main_inline_kb(user_id))
        user_states[user_id] = None
        return

    elif is_replying:
        target_id = admin_reply_targets[user_id]
        try:
            bot.send_message(target_id, "💬 <b>Ответ администрации:</b>", parse_mode="HTML")
            bot.copy_message(target_id, user_id, message.message_id)
            bot.send_message(user_id, f"✅ Доставлено игроку <code>{target_id}</code>!", reply_markup=get_admin_inline_kb(user_id))
        except Exception as e:
            bot.send_message(user_id, f"❌ Ошибка: {e}")
        admin_reply_targets[user_id] = None
        return

if __name__ == '__main__':
    keep_alive()
    bot.remove_webhook()
    print("Prince Russia Ultra All-Buttons v7.0 Started!")
    bot.infinity_polling(skip_pending=True)
