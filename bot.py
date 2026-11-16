import os
import threading
import time
import random  # 📌 Rastgele seçimler için gerekli kütüphane
from datetime import datetime, timedelta
import telebot
from flask import Flask

# 1. TEMEL AYARLAR
TOKEN = os.environ.get("BOT_TOKEN", "9032286572:AAH4-z-92Dx-gr1LX0Ka5Q4HelpoQJsDMUU")
CHANNEL_ID = "@SINIRSIZPDF2"  # Hedef kanalınız

# Güvenlik ve Yetkilendirme Ayarları
BENIM_TELEGRAM_ID = 6787610448  
GIZLI_SIFRE = "SINIRSIZPDF2735"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# Durum Değişkenleri
is_running = False
current_message_text = """⚡️⚡️⚡️⚡️⚡️⚡️⚡️⚡️⚡️⚡️⚡️

<b><a href="https://t.me/SINIRSIZPDF">        TAŞINDIK

GÜNCEL KANALIMIZA

      KATILIN</a></b>

👇👇👇👇👇👇👇👇👇👇👇

https://t.me/SINIRSIZPDF"""

current_photo_id = None
thread_lock = threading.Lock()

# Render'ı uykudan (keep-alive) tutmak için web sunucusu endpoint'i
@app.route('/')
def home():
    return "Bot aktif ve çalışıyor!"

# 📌 Her gönderimde saatle birlikte tamamen rastgele karakter/emoji üreten fonksiyon
def get_final_message():
    with thread_lock:
        base_text = current_message_text
    
    # Türkiye saatine göre güncel saat (UTC+3)
    turkey_time = datetime.utcnow() + timedelta(hours=3)
    current_time_str = turkey_time.strftime("%H:%M")
    
    # Her seferinde spam filtresini kırmak için rastgele seçilecek gizli semboller/boşluk varyasyonları listesi
    # (Görünmez veya şık varyasyonlar Telegram'ın kopyalama algoritmalarını tamamen şaşırtır)
    random_decorations = [
        "🔹",
        "▪️",
        "▫️",
        "🔸",
        "✦",
        "✧",
        "◈",
        "◇",
        "•",
        "– ✦ –"
    ]
    chosen_dec = random.choice(random_decorations)
    
    # Mesajın en altına saat ve rastgele süsleme eklenir
    final_text = f"{base_text}\n\n<i>{chosen_dec} Güncelleme: {current_time_str} {chosen_dec}</i>"
    return final_text

# Botu arka planda kanala mesaj gönderme döngüsü
def background_loop():
    global is_running, current_photo_id
    while True:
        with thread_lock:
            running_status = is_running
            photo_id = current_photo_id

        if running_status:
            try:
                msg_to_send = get_final_message()
                if photo_id:
                    bot.send_photo(CHANNEL_ID, photo_id, caption=msg_to_send, parse_mode='HTML')
                else:
                    bot.send_message(CHANNEL_ID, msg_to_send, parse_mode='HTML', disable_web_page_preview=True)
                print("✅ Kanala periyodik benzersiz mesaj başarıyla gönderildi.")
            except Exception as e:
                print(f"❌ Kanala gönderim hatası: {e}")
        
        # Gönderim aralığı (300 saniye = 5 dakika)
        time.sleep(300)

# Güvenlik Kontrollü /dehh Komutu (Başlatma)
@bot.message_handler(
    content_types=['text', 'photo'],
    func=lambda m: (m.text and m.text.startswith('/dehh')) or (m.caption and m.caption.startswith('/dehh'))
)
def start_command(message):
    print(f">>> [DEBUG] Telegram'dan komut yakalandı! Gönderen ID: {message.from_user.id}")
    
    global is_running, current_message_text, current_photo_id
    
    user_id = message.from_user.id
    full_text = message.caption if message.caption else message.text
    
    # Yetki Kontrolü
    if user_id == BENIM_TELEGRAM_ID:
        yetki_onayli = True
    else:
        parts = full_text.split(maxsplit=1)
        if len(parts) > 1 and parts[1].startswith(GIZLI_SIFRE):
            yetki_onayli = True
        else:
            yetki_onayli = False

    if not yetki_onayli:
        if full_text.strip() == '/dehh':
            bot.send_message(message.chat.id, "🔒 Bu botu çalıştırmak için parola gerekiyor.\nKullanım: `/dehh parolaniz`")
        else:
            bot.send_message(message.chat.id, "❌ Hatalı parola! Yetkisiz kullanım.")
        return

    if message.photo:
        current_photo_id = message.photo[-1].file_id

    # Metin Güncelleme Kısmı
    parts = full_text.split(maxsplit=1)
    if len(parts) > 1:
        if user_id == BENIM_TELEGRAM_ID:
            potential_text = parts[1].strip()
            if potential_text:
                current_message_text = potential_text
        else:
            sub_parts = full_text.split(maxsplit=2)
            if len(sub_parts) > 2:
                current_message_text = sub_parts[2].strip()

    with thread_lock:
        is_running = True
    
    bot.send_message(message.chat.id, "✅ Yetki onaylandı! Bot başlatıldı ve kanala test mesajı gönderiliyor...")

    # ANINDA KANALA GÖNDERME TESTİ
    try:
        msg_to_send = get_final_message()
        if current_photo_id:
            bot.send_photo(CHANNEL_ID, current_photo_id, caption=msg_to_send, parse_mode='HTML')
        else:
            bot.send_message(CHANNEL_ID, msg_to_send, parse_mode='HTML', disable_web_page_preview=True)
        print("✅ Kanala ilk test mesajı başarıyla iletildi!")
    except Exception as e:
        print(f"❌ Kanala ilk test mesajı gönderilemedi! Hata: {e}")
        bot.send_message(message.chat.id, f"⚠️ Bot başlatıldı ancak kanala mesaj atılamadı!\nHata: {e}")

# Güvenlik Kontrollü /ooha Komutu (Durdurma)
@bot.message_handler(
    func=lambda m: m.text and m.text.startswith('/ooha')
)
def stop_command(message):
    global is_running
    user_id = message.from_user.id
    
    if user_id == BENIM_TELEGRAM_ID:
        with thread_lock:
            is_running = False
        bot.send_message(message.chat.id, "🛑 Bot durduruldu! Kanala otomatik gönderimler durduruldu.")
    else:
        bot.send_message(message.chat.id, "❌ Bu komutu kullanmaya yetkiniz yok.")

# Güvenli Polling Başlatıcı
def start_bot_polling():
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.infinity_polling(skip_pending=True)
    except Exception as e:
        print(f"Polling hatası: {e}")

if __name__ == '__main__':
    t = threading.Thread(target=background_loop, daemon=True)
    t.start()
    
    polling_thread = threading.Thread(target=start_bot_polling, daemon=True)
    polling_thread.start()
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
