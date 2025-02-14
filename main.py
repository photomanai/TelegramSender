from telethon import TelegramClient
from dotenv import load_dotenv
import os

# .env dosyasını yükleyin
load_dotenv()

# API ID ve API Hash'i .env dosyasından alın
api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

client = TelegramClient("invite_app_session", api_id, api_hash)


async def send_invites():
    await client.start()
    print("Client giriş yaptı!")

    selected_names = ["Fulii", "10c¹ Zahid", "Roofmom/2"]  # Mesaj göndəriləcək adlar

    dialogs = (
        await client.get_dialogs()
    )  # İstifadəçinin bütün dialoglarını alır (gruplar ve kişiler)
    print(f"{len(dialogs)} diyalog bulundu.")

    for dialog in dialogs:
        # Dialog'un adını yazdırarak kontrol edelim
        print(
            f"Dialog Adı: {dialog.name}, Kullanıcı Adı: {getattr(dialog, 'username', 'Yok')}"
        )

        # Dialog adı ile kontrol yap
        for name in selected_names:
            if name.lower() in dialog.name.lower():
                try:
                    message = f"Salam {dialog.name}! Yeni dəvət tətbiqimə baxmağı tövsiyə edirəm."
                    await client.send_message(dialog.id, message)  # Mesajı göndərir
                    print(f"{dialog.name} adlı istifadəçiyə mesaj göndərildi.")
                    break  # Mesaj gönderildikten sonra diğer isimlere bakmayı durdur
                except Exception as e:
                    print(f"{dialog.name} üçün səhv baş verdi: {e}")
            else:
                print(f"{dialog.name} bu listede değil, mesaj gönderilmedi.")


with client:
    client.loop.run_until_complete(send_invites())
