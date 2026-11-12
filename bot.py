import time
import threading
import datetime
import os
import telebot
from flask import Flask

# --- AYARLAR ---
TOKEN = os.environ.get("BOT_TOKEN", "9257963202:AAF-yIjBWuHd_8-N0otm-XdYmySLwlLLM3A")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@SINIRSIZPDF2")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

is_running = False
last_message_id = None
current_photo_id = None
current_message_text = "⚠️ TAŞINDIK :\n👉https://t.me/SINIRSIZPDF"
thread_lock = threading.Lock()

@app.route('/')
def home():
    return "Telegram Bot Aktif ve Çalışıyor!"

def send_update_to_channel():
    global last_message_id, current_photo_id, current_message_text
    try:
        if last_message_id:
            try:
                bot.delete_message(CHANNEL_ID, last_message_id)
            except Exception as e:
                print(f"Eski mesaj silinemedi: {e}")

        current_time = datetime.datetime.now().strftime("%H:%M")
        dynamic_text = f"{current_message_text}\n\n⏱️ Güncelleme: {current_time}"
        
        if current_photo_id:
            sent_msg = bot.send_photo(CHANNEL_ID, current_photo_id, caption=dynamic_text, parse_mode='Markdown')
        else:
            sent_msg = bot.send_message(CHANNEL_ID, dynamic_text, parse_mode='Markdown')
            
        last_message_id = sent_msg.message_id
        print(f"[{current_time}] Kanalda mesaj güncellendi.")
    except Exception as e:
        print(f"❌ Gönderim hatası: {e}")

def background_loop():
    global is_running
    while True:
        time.sleep(300) # 5 dakika
        with thread_lock:
            active = is_running
        if active:
            send_update_to_channel()

# Arka plan döngüsünü başlat
t = threading.Thread(target=background_loop, daemon=True)
t.start()

@bot.message_handler(content_types=['text', 'photo'], commands=['baslat'])
def start_command(message):
    global is_running, current_message_text, current_photo_id
    if message.photo:
        current_photo_id = message.photo[-1].file_id
    full_text = message.caption if message.caption else message.text
    if full_text:
        parts = full_text.split(maxsplit=1)
        if len(parts) > 1:
            current_message_text = parts[1]
    with thread_lock:
        is_running = True
    bot.reply_to(message, "✅ Ayarlar kaydedildi ve döngü başlatıldı!")
    send_update_to_channel()

@bot.message_handler(commands=['durdur'])
def stop_command(message):
    global is_running
    with thread_lock:
        is_running = False
    bot.reply_to(message, "🛑 Otomatik döngü durduruldu.")

# Botu arka planda dinlemeye başla
def run_bot():
    bot.infinity_polling(skip_pending=True)

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)