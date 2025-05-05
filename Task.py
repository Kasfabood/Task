from flask import Flask
from threading import Thread
import telebot
from telebot import types
import requests

# ---------- إعداد Flask لتشغيل keep_alive ----------
app = Flask('')

@app.route('/')
def home():
    return "I'm alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ---------- كود البوت ----------
TOKEN = '7852504881:AAF5Ewj4PISL7Vzr0XQOZH10tSbEuhsX7Xk'
CHANNEL_USERNAME = '@elrefaiechannle'

bot = telebot.TeleBot(TOKEN)
tasks = {}

# ---------- القوائم ----------
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('➕ إضافة', callback_data='add'),
        types.InlineKeyboardButton('🗑️ حذف', callback_data='delete'),
        types.InlineKeyboardButton('✏️ تعديل', callback_data='edit'),
        types.InlineKeyboardButton('✅ إنهاء', callback_data='done'),
        types.InlineKeyboardButton('📋 عرض المهام', callback_data='show')
    )
    markup.add(types.InlineKeyboardButton("👨‍💻 مطور البوت", url="https://t.me/v_9_z_2"))
    return markup

def back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('↩️ رجوع', callback_data='back'))
    return markup

def check_subscription(user_id):
    try:
        res = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return res.status in ['member', 'administrator', 'creator']
    except:
        return False

# ---------- أوامر ----------
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id
    if check_subscription(user_id):
        bot.send_message(user_id, "أهلاً بك! اختر أحد الخيارات:", reply_markup=main_menu())
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        bot.send_message(user_id, "⚠️ يجب الاشتراك في القناة أولاً، ثم العودة والضغط على /start", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.message.chat.id

    if call.data == 'back':
        send_main_menu(user_id)
    elif call.data == 'add':
        msg = bot.send_message(user_id, "أرسل اسم المهمة:", reply_markup=back_button())
        bot.register_next_step_handler(msg, lambda m: add_task(m, user_id))
    elif call.data == 'delete':
        show_tasks(user_id, with_back=True)
        msg = bot.send_message(user_id, "أرسل رقم المهمة التي تريد حذفها:", reply_markup=back_button())
        bot.register_next_step_handler(msg, lambda m: delete_task(m, user_id))
    elif call.data == 'edit':
        show_tasks(user_id, with_back=True)
        msg = bot.send_message(user_id, "أرسل رقم المهمة لتعديلها:", reply_markup=back_button())
        bot.register_next_step_handler(msg, lambda m: ask_edit_text(m, user_id))
    elif call.data == 'done':
        show_tasks(user_id, with_back=True)
        msg = bot.send_message(user_id, "أرسل رقم المهمة لتعليمها كمكتملة:", reply_markup=back_button())
        bot.register_next_step_handler(msg, lambda m: mark_done(m, user_id))
    elif call.data == 'show':
        show_tasks(user_id, with_back=True)

# ---------- الوظائف ----------
def add_task(msg, user_id):
    if is_back(msg):
        send_main_menu(user_id)
        return
    task = msg.text.strip()
    tasks.setdefault(user_id, []).append({'text': task, 'done': False})
    bot.send_message(user_id, "✅ تم إضافة المهمة!", reply_markup=back_button())

def delete_task(msg, user_id):
    if is_back(msg):
        send_main_menu(user_id)
        return
    try:
        idx = int(msg.text) - 1
        if 0 <= idx < len(tasks.get(user_id, [])):
            removed = tasks[user_id].pop(idx)
            bot.send_message(user_id, f"🗑️ تم حذف المهمة: {removed['text']}", reply_markup=back_button())
        else:
            back_or_tasks_list(user_id, "رقم غير صحيح.")
    except:
        back_or_tasks_list(user_id, "أدخل رقم صحيح.")

def ask_edit_text(msg, user_id):
    if is_back(msg):
        send_main_menu(user_id)
        return
    try:
        idx = int(msg.text) - 1
        if 0 <= idx < len(tasks.get(user_id, [])):
            m = bot.send_message(user_id, "أرسل النص الجديد:", reply_markup=back_button())
            bot.register_next_step_handler(m, lambda m: edit_task_text(m, user_id, idx))
        else:
            back_or_tasks_list(user_id, "رقم غير صحيح.")
    except:
        back_or_tasks_list(user_id, "أدخل رقم صحيح.")

def edit_task_text(msg, user_id, idx):
    if is_back(msg):
        send_main_menu(user_id)
        return
    new_text = msg.text.strip()
    tasks[user_id][idx]['text'] = new_text
    bot.send_message(user_id, "✏️ تم تعديل المهمة.", reply_markup=back_button())

def mark_done(msg, user_id):
    if is_back(msg):
        send_main_menu(user_id)
        return
    try:
        idx = int(msg.text) - 1
        if 0 <= idx < len(tasks.get(user_id, [])):
            tasks[user_id][idx]['done'] = True
            bot.send_message(user_id, "✅ تم تحديد المهمة كمكتملة.", reply_markup=back_button())
        else:
            back_or_tasks_list(user_id, "رقم غير صحيح.")
    except:
        back_or_tasks_list(user_id, "أدخل رقم صحيح.")

def show_tasks(user_id, with_back=False):
    user_tasks = tasks.get(user_id, [])
    if not user_tasks:
        bot.send_message(user_id, "لا توجد مهام حالياً.", reply_markup=back_button() if with_back else None)
        return

    text = "قائمة المهام:\n\n"
    for i, t in enumerate(user_tasks, 1):
        status = "✅" if t['done'] else "⏳"
        text += f"{i}. {t['text']} {status}\n"

    bot.send_message(user_id, text, reply_markup=back_button() if with_back else None)

def is_back(msg):
    return msg.text.strip() == '↩️ رجوع' or msg.text.startswith('/')

def send_main_menu(user_id):
    bot.send_message(user_id, "تم الرجوع للقائمة الرئيسية:", reply_markup=main_menu())

bot.polling()