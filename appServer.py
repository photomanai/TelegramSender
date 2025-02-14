from flask import Flask, jsonify
from telethon import TelegramClient
from dotenv import load_dotenv
import os
import asyncio
from flask_cors import CORS  # CORS başlıklarını eklemek için

# .env dosyasını yükle
load_dotenv()

# API ID ve API Hash'i .env dosyasından al
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

# Telethon ile Telegram client'ını başlat
client = TelegramClient("invite_app_session", api_id, api_hash)

# Flask uygulamasını başlat
app = Flask(__name__)
CORS(app)  # CORS başlıklarını etkinleştir


# Telegram mesajlarını gönderecek asenkron fonksiyon
async def send_invites():
    await client.start()  # Client'ı başlat
    print("Client giriş yaptı!")

    selected_names = ["Fulii", "10c¹ Zahid", "Roofmom/2"]  # Gönderilecek adlar
    dialogs = await client.get_dialogs()  # Dialogları al
    for dialog in dialogs:
        for name in selected_names:
            if name.lower() in dialog.name.lower():  # İsim eşleşmesi
                try:
                    message = f"Salam {dialog.name}! Yeni dəvət tətbiqimə baxmağı tövsiyə edirəm."
                    await client.send_message(dialog.id, message)  # Mesaj gönder
                    print(f"{dialog.name} adlı kullanıcıya mesaj gönderildi.")
                    break  # Mesaj gönderildikten sonra diğer isimlere bakma
                except Exception as e:
                    print(f"{dialog.name} için hata oluştu: {e}")


# API endpoint'i
@app.route("/send-invites", methods=["GET"])
async def send_invites_route():  # async def ile fonksiyonu asenkron hale getirin
    await send_invites()  # Asenkron fonksiyonu çağırın
    return jsonify({"status": "success", "message": "Invites sent!"})


# Flask uygulamasını başlat
if __name__ == "__main__":
    app.run(port=5000)
