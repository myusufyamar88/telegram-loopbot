import time
import threading
import datetime
import os
import telebot
from flask import Flask

# --- AYARLAR ---
TOKEN = os.environ.get("BOT_TOKEN", "9032286572:AAEef58DDLIwDYDeHpHfFtdyQCsX2tpU6Jc")
CHANNEL_ID = os.environ.get("CHANNEL_ID", "@SINIRSIZPDF2")

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

is_running = False
last_message_id = None
current_photo_id = None
current_message_text = "⚠️⚠️⚠️TAŞINDIK⚠️⚠️⚠️ https://t.me/SINIRSIZPDF"
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

        current_time = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).strftime("%H:%M")
        dynamic_text = f"{current_message_text}\n\n⏱️ Güncelleme: {current_time}"
        
        if current_photo_id:
            sent_msg = bot.send_photo(CHANNEL_ID, current_photo_id, caption=dynamic_text, parse_mode='HTML')
        else:
            sent_msg = bot.send_message(CHANNEL_ID, dynamic_text, parse_mode='HTML')
            
        last_message_id = sent_msg.message_id
        print(f"[{current_time}] Kanalda mesaj güncellendi.")
    except Exception as e:
        print(f"❌ Gönderim hatası: {e}")

def background_loop():
    global is_running
    while True:
        time.sleep(300)  # 5 dakika
        with thread_lock:
            active = is_running
        if active:
            send_update_to_channel()

t = threading.Thread(target=background_loop, daemon=True)
t.start()

# Hem düz metin hem de fotoğraflı /baslat komutlarını yakalayan yeni filtre
@bot.message_handler(
    content_types=['text', 'photo'],
    func=lambda m: (m.text and m.text.startswith('/baslat')) or (m.caption and m.caption.startswith('/baslat'))
)
# Kendi Telegram ID'nizi buraya yazın (Örn: @userinfobot'tan öğrendiğiniz sayısal ID)
BENIM_TELEGRAM_ID = 6787610448  
GIZLI_SIFRE = "SINIRSIZPDF2735"  # İstediğiniz bir şifre belirleyin

@bot.message_handler(
    content_types=['text', 'photo'],
    func=lambda m: (m.text and m.text.startswith('/baslat')) or (m.caption and m.caption.startswith('/baslat'))
)
def start_command(message):
    global is_running, current_message_text, current_photo_id
    
    user_id = message.from_user.id
    full_text = message.caption if message.caption else message.text
    
    # 1. KONTROL: Gönderen kişi siz misiniz?
    if user_id == BENIM_TELEGRAM_ID:
        # Sizseniz şifre sormadan direkt çalıştır
        yetki_onayli = True
    else:
        # Başkasıysa şifre kontrolü yap (/baslat şifre_buraya formatında olmalı)
        parts = full_text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].startswith(GIZLI_SIFRE):
            yetki_onayli = True
        else:
            yetki_onayli = False

    # 2. YETKİ YOKSA UYAR
    if not yetki_onayli:
        # Eğer yabiri sadece "/baslat" yazdıysa parola iste
        if full_text.strip() == '/baslat':
            bot.reply_to(message, "🔒 Bu botu çalıştırmak için parolasını girmeniz gerekiyor.\nÖrnek kullanım: `/baslat parolaniz`")
        else:
            bot.reply_to(message, "❌ Hatalı parola! Yetkisiz kullanım.")
        return

    # 3. YETKİ ONAYLANDIYSA (Siz veya doğru şifreyi giren kişi)
    if message.photo:
        current_photo_id = message.photo[-1].file_id
    else:
        current_photo_id = None

    if full_text:
        # Şifre girildiyse mesaj metnini şifreden sonrasına göre ayarla (Siz düz yazdıysanız varsayılanı korur)
        parts = full_text.split(maxsplit=1)
        if len(parts) > 1 and user_id != BENIM_TELEGRAM_ID:
            # Başkası şifreden sonra ek metin yazdıysa ayıkla (isteğe bağlı)
            pass  # Standart mesaj metnini koruyoruz

    with thread_lock:
        is_running = True
    
    bot.reply_to(message, "✅ Yetki onaylandı! Ayarlar kaydedildi ve döngü başlatıldı.")
    send_update_to_channel()
@bot.message_handler(commands=['durdur'])
def stop_command(message):
    global is_running
    with thread_lock:
        is_running = False
    bot.reply_to(message, "🛑 Otomatik döngü durduruldu.")

# Botu arka planda dinlemeye başla
def run_bot():
    try:
        bot.remove_webhook()  # Takılı kalan eski bağlantıları temizler
    except Exception as e:
        print(f"Webhook temizleme hatası: {e}")
    
    bot.infinity_polling(skip_pending=True)

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
