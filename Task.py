from flask import Flask
from threading import Thread
import telebot
from telebot import types
import datetime
import time
import threading

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
        bot.register_next_step_handler(msg, lambda m: ask_time(m, user_id))
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
    elif call.data.startswith("remind_"):
        _, user_id, task_idx = call.data.split("_")
        user_id = int(user_id)
        task_idx = int(task_idx)
        task = tasks[user_id][task_idx]
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("✅ نعم", callback_data=f"done_{user_id}_{task_idx}"),
            types.InlineKeyboardButton("❌ لا", callback_data=f"redo_{user_id}_{task_idx}")
        )
        bot.send_message(user_id, f"هل أنهيت المهمة: {task['text']}؟", reply_markup=markup)
    elif call.data.startswith("done_"):
        _, user_id, task_idx = call.data.split("_")
        user_id = int(user_id)
        task_idx = int(task_idx)
        tasks[user_id][task_idx]['done'] = True
        bot.send_message(user_id, "✅ تم تعليم المهمة كمكتملة.")
    elif call.data.startswith("redo_"):
        _, user_id, task_idx = call.data.split("_")
        user_id = int(user_id)
        task_idx = int(task_idx)
        msg = bot.send_message(user_id, "أرسل الوقت الجديد (بصيغة 00:00 إلى 24:00):")
        bot.register_next_step_handler(msg, lambda m: update_time(m, user_id, task_idx))

# ---------- الوظائف ----------
def ask_time(msg, user_id):
    if is_back(msg):
        send_main_menu(user_id)
        return
    task_text = msg.text.strip()
    msg = bot.send_message(user_id, "أرسل الوقت بصيغة 00:00 إلى 24:00", reply_markup=back_button())
    bot.register_next_step_handler(msg, lambda m: add_task(m, user_id, task_text))

def add_task(msg, user_id, task_text):
    if is_back(msg):
        send_main_menu(user_id)
        return
    time_str = msg.text.strip()
    try:
        hour, minute = map(int, time_str.split(":"))
        now = datetime.datetime.now()
        task_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if task_time < now:
            task_time += datetime.timedelta(days=1)
        task = {'text': task_text, 'done': False, 'time': task_time.strftime("%H:%M")}
        tasks.setdefault(user_id, []).append(task)
        bot.send_message(user_id, "✅ تم إضافة المهمة!", reply_markup=back_button())
    except:
        bot.send_message(user_id, "صيغة الوقت غير صحيحة. أرسل مثل 13:30")

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
            bot.send_message(user_id, "رقم غير صحيح.", reply_markup=back_button())
    except:
        bot.send_message(user_id, "أدخل رقم صحيح.", reply_markup=back_button())

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
            bot.send_message(user_id, "رقم غير صحيح.", reply_markup=back_button())
    except:
        bot.send_message(user_id, "أدخل رقم صحيح.", reply_markup=back_button())

def edit_task_text(msg, user_id, idx):
    if is_back(msg):
        send_main_menu(user_id)
        return
    new_text = msg.text.strip()
    tasks[user_id][idx]['text'] = new_text
    bot.send_message(user_id, "✏️ تم تعديل المهمة.", reply_markup=back_button())

def update_time(msg, user_id, task_idx):
    try:
        hour, minute = map(int, msg.text.strip().split(":"))
        now = datetime.datetime.now()
        task_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if task_time < now:
            task_time += datetime.timedelta(days=1)
        tasks[user_id][task_idx]['time'] = task_time.strftime("%H:%M")
        bot.send_message(user_id, "⏰ تم تحديث وقت المهمة!")
    except:
        bot.send_message(user_id, "صيغة غير صحيحة. أرسل مثل 12:45")

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
            bot.send_message(user_id, "رقم غير صحيح.", reply_markup=back_button())
    except:
        bot.send_message(user_id, "أدخل رقم صحيح.", reply_markup=back_button())

def show_tasks(user_id, with_back=False):
    user_tasks = tasks.get(user_id, [])
    if not user_tasks:
        bot.send_message(user_id, "لا توجد مهام حالياً.", reply_markup=back_button() if with_back else None)
        return

    text = "قائمة المهام:\n\n"
    for i, t in enumerate(user_tasks, 1):
        status = "✅" if t['done'] else "⏳"
        text += f"{i}. {t['text']} {status} | ⏰ {t['time']}\n"

    bot.send_message(user_id, text, reply_markup=back_button() if with_back else None)

def is_back(msg):
    return msg.text.strip() == '↩️ رجوع' or msg.text.startswith('/')

def send_main_menu(user_id):
    bot.send_message(user_id, "تم الرجوع للقائمة الرئيسية:", reply_markup=main_menu())

# ---------- مؤقت التذكير (تم التعديل هنا) ----------
def reminder_loop():
    print("Reminder loop started...")
    while True:
        now = datetime.datetime.now().strftime("%H:%M")
        for user_id in list(tasks.keys()):
            for idx, task in enumerate(tasks[user_id]):
                task_time = task.get('time')
                if not task['done']:
                    print(f"الآن: {now} | مهمة: {task['text']} | وقت المهمة: {task_time}")
                if not task['done'] and task_time == now:
                    try:
                        bot.send_message(user_id, f"⏰ حان وقت المهمة: {task['text']}")
                        markup = types.InlineKeyboardMarkup()
                        markup.add(
                            types.InlineKeyboardButton("✅ نعم", callback_data=f"done_{user_id}_{idx}"),
                            types.InlineKeyboardButton("❌ لا", callback_data=f"redo_{user_id}_{idx}")
                        )
                        bot.send_message(user_id, "هل أنهيت المهمة؟", reply_markup=markup)
                    except Exception as e:
                        print(f"خطأ أثناء إرسال التذكير: {e}")
        time.sleep(60)

# تشغيل التذكير في خلفية
threading.Thread(target=reminder_loop, daemon=True).start()

bot.polling(non_stop=True)
