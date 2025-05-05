from flask import Flask
from threading import Thread
import telebot
from telebot import types
import datetime
import time
import threading
import openai
from PIL import Image
import io

# مفتاح OpenAI الخاص بك
OPENAI_API_KEY = "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"
openai.api_key = OPENAI_API_KEY

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

# ---------- إعداد البوت ----------
TOKEN = '7852504881:AAF5Ewj4PISL7Vzr0XQOZH10tSbEuhsX7Xk'
CHANNEL_USERNAME = '@elrefaiechannle'
bot = telebot.TeleBot(TOKEN)
tasks = {}
ai_users = set()

# ---------- القوائم ----------
def main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton('➕ إضافة', callback_data='add'),
        types.InlineKeyboardButton('🗑️ حذف', callback_data='delete'),
        types.InlineKeyboardButton('✏️ تعديل', callback_data='edit'),
        types.InlineKeyboardButton('✅ إنهاء', callback_data='done'),
        types.InlineKeyboardButton('📋 عرض المهام', callback_data='show'),
        types.InlineKeyboardButton('🤖 الذكاء الاصطناعي', callback_data='ai_mode')
    )
    markup.add(types.InlineKeyboardButton("👨‍💻 مطور البوت", url="https://t.me/v_9_z_2"))
    return markup

def back_button():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('↩️ رجوع', callback_data='back'))
    return markup

# ---------- التحقق من الاشتراك ----------
def check_subscription(user_id):
    try:
        res = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return res.status in ['member', 'administrator', 'creator']
    except:
        return False

# ---------- الأوامر ----------
@bot.message_handler(commands=['start'])
def start(msg):
    user_id = msg.from_user.id
    if check_subscription(user_id):
        ai_users.discard(user_id)
        bot.send_message(user_id, "أهلاً بك! اختر أحد الخيارات:", reply_markup=main_menu())
    else:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        bot.send_message(user_id, "⚠️ يجب الاشتراك في القناة أولاً، ثم العودة والضغط على /start", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.message.chat.id

    if call.data == 'back':
        ai_users.discard(user_id)
        send_main_menu(user_id)
    elif call.data == 'ai_mode':
        ai_users.add(user_id)
        bot.send_message(user_id, "أرسل سؤالك أو طلبك للذكاء الاصطناعي:", reply_markup=back_button())
    # باقي الأوامر كما هي مثل add/delete/edit وغيرها

# ---------- الذكاء الاصطناعي ----------
@bot.message_handler(func=lambda m: m.chat.id in ai_users, content_types=['text', 'photo'])
def ai_response(msg):
    user_id = msg.chat.id

    if msg.content_type == 'text':
        prompt = msg.text.strip()
        try:
            res = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            reply = res.choices[0].message.content
            bot.send_message(user_id, reply, reply_markup=back_button())
        except Exception as e:
            bot.send_message(user_id, "حدث خطأ أثناء الاتصال بالذكاء الاصطناعي.")
    
    elif msg.content_type == 'photo':
        # لتحويل الصورة إلى نص أو معلومات، سنحتاج لاستخدام API تحليل الصور
        file_info = bot.get_file(msg.photo[-1].file_id)
        file = bot.download_file(file_info.file_path)
        
        # هنا يمكن استخدام OpenAI أو أي خدمة لتحليل الصورة.
        # حالياً، نعرض الصورة فقط.
        bot.send_message(user_id, "تم استقبال الصورة، جاري تحليلها...")

        try:
            # تحويل الصورة إلى نص باستخدام OpenAI أو أي خدمة أخرى
            # مثال: إرسال الصورة إلى خدمة OpenAI إذا كانت تدعم ذلك
            image = Image.open(io.BytesIO(file))
            # افتراضًا نحتاج تحويل الصورة إلى نص بواسطة خدمة OpenAI أو خدمات أخرى
            # في حال دعم الخدمة لذلك (حاليًا OpenAI لا يدعم تحليل الصور بشكل مباشر)
            # البوت يمكنه فقط استلام الصورة في هذا النموذج.
            bot.send_message(user_id, "تحليل الصورة قيد الانتظار... (قد تحتاج إلى تكامل مع API خارجي لتحليل الصورة)")
        except Exception as e:
            bot.send_message(user_id, "حدث خطأ أثناء معالجة الصورة.")

# ---------- قائمة الرجوع ----------
def send_main_menu(user_id):
    ai_users.discard(user_id)
    bot.send_message(user_id, "تم الرجوع للقائمة الرئيسية:", reply_markup=main_menu())

# ---------- تشغيل البوت ----------
bot.polling(non_stop=True)
