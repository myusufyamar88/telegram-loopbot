import os
import threading
import time
import telebot
from flask import Flask

# 1. TEMEL AYARLAR
TOKEN = os.environ.get("BOT_TOKEN", "9032286572:AAEef58DDLIwDYDeHpHfFtdyQCsX2tpU6Jc")
CHANNEL_ID = -1891277095  # Kanalın sayısal ID'si

# Güvenlik ve Yetkilendirme Ayarları
BENIM_TELEGRAM_ID = 6787610448
GIZLI_SIFRE = "SINIRSIZPDF2735"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Durum Değişkenleri
is_running = False
current_message_text = "TAŞINDIK : @SINIRSIZPDF"
current_photo_id = None
thread_lock = threading.Lock()

# Render'ı uykudan (keep-alive) tutmak için web sunucusu endpoint'i
@app.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

# Botun arka planda kanala mesaj gönderme döngüsü
def background_loop():
    global is_running, current_message_text, current_photo_id
    while True:
        with thread_lock:
            running_status = is_running
            msg_text = current_message_text
            photo_id = current_photo_id

        if running_status:
            try:
                if photo_id:
                    bot.send_photo(CHANNEL_ID, photo_id, caption=msg_text, parse_mode='HTML')
                else:
                    bot.send_message(CHANNEL_ID, msg_text, parse_mode='HTML')
            except Exception as e:
                print(f"Gönderim hatası: {e}")
        
        time.sleep(300)

# Güvenlik Kontrollü /baslat Komutu
@bot.message_handler(
    content_types=['text', 'photo'],
    func=lambda m: (m.text and m.text.startswith('/baslat')) or (m.caption and m.caption.startswith('/baslat'))
)
def start_command(message):
    global is_running, current_message_text, current_photo_id
    
    user_id = message.from_user.id
    full_text = message.caption if message.caption else message.text
    
    if user_id == BENIM_TELEGRAM_ID:
        yetki_onayli = True
    else:
        parts = full_text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].startswith(GIZLI_SIFRE):
            yetki_onayli = True
        else:
            yetki_onayli = False

    if not yetki_onayli:
        if full_text.strip() == '/baslat':
            bot.reply_to(message, "🔒 Bu botu çalıştırmak için parola gerekiyor.\nKullanım: `/baslat parolaniz`")
        else:
            bot.reply_to(message, "❌ Hatalı parola! Yetkisiz kullanım.")
        return

    if message.photo:
        current_photo_id = message.photo[-1].file_id

    with thread_lock:
        is_running = True
    
    bot.reply_to(message, "✅ Yetki onaylandı! Bot başarıyla başlatıldı ve döngüye girdi.")

# Güvenli Polling Başlatıcı (409 çakışmalarını önlemek için webhook'u sıfırlar)
def start_bot_polling():
    try:
        bot.remove_webhook()  # Eski takılı kalan webhook/session bağlantılarını temizler
        time.sleep(1)
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Polling hatası: {e}")

# Flask uygulamasını, arka plan döngüsünü ve Telegram Dinleyicisini Başlatma
if __main__ == '__main__':
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    
    polling_thread = threading.Thread(target=start_bot_polling, daemon=True)
    polling_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
