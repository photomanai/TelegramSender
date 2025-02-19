from flask import Flask, request, jsonify
from telethon import TelegramClient, errors
from telethon.tl.types import InputPeerUser, InputPeerChannel
from dotenv import load_dotenv
import os
import logging
from flask_cors import CORS


# Loglama ayarı
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

api_id = os.getenv("API_ID")
api_hash = os.getenv("API_HASH")

app = Flask(__name__)
CORS(app)

# Session dosyaları için mutlak yol
SESSION_DIR = os.path.join(os.getcwd(), "sessions")
os.makedirs(SESSION_DIR, exist_ok=True)


def get_client(phone_number):
    """TelegramClient oluştururken telefon numarasını normalize edelim"""
    clean_phone = phone_number.strip().replace(" ", "").replace("-", "")
    session_path = os.path.join(SESSION_DIR, f"{clean_phone}.session")
    return TelegramClient(session_path, api_id, api_hash)


@app.route("/")
def hello_world():
    return "Hello, World!"


@app.route("/send-code", methods=["POST"])
async def send_code():
    try:
        data = request.json
        phone_number = data.get("phone_number")
        if not phone_number:
            return (
                jsonify({"status": "error", "message": "Phone number required"}),
                400,
            )

        client = get_client(phone_number)
        await client.connect()

        if await client.is_user_authorized():
            return jsonify({"status": "success", "message": "Already logged in"})

        sent_code = await client.send_code_request(phone_number)
        return jsonify(
            {"status": "success", "phone_code_hash": sent_code.phone_code_hash}
        )

    except Exception as e:
        logger.error(f"Send code error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/verify-code", methods=["POST"])
async def verify_code():
    try:
        data = request.json
        phone_number = data.get("phone_number")
        code = data.get("code").strip()
        phone_code_hash = data.get("phone_code_hash")
        password_2fa = data.get("password_2fa")  # 2FA şifresi için

        if not all([phone_number, code, phone_code_hash]):
            return (
                jsonify({"status": "error", "message": "Incomplete information"}),
                400,
            )

        client = get_client(phone_number)
        await client.connect()

        try:
            await client.sign_in(
                phone_number, code=code, phone_code_hash=phone_code_hash
            )
        except errors.SessionPasswordNeededError:
            if not password_2fa:
                return (
                    jsonify({"status": "error", "message": "2FA şifresi gerekli"}),
                    402,
                )
            await client.sign_in(password=password_2fa)

        # Session'ı manuel kaydetme
        client.session.save()
        return jsonify({"status": "success", "message": "Login successful"})

    except Exception as e:
        logger.error(f"Verify error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/send-invites", methods=["POST"])
async def send_invites():
    try:
        data = request.json
        phone_number = data.get("phone_number")
        base_message = data.get("message", "You are invited to the event.")
        recipients = data.get("recipients", [])

        if not phone_number:
            return jsonify({"status": "error", "message": "Phone number required"}), 400

        client = get_client(phone_number)
        async with client:
            if not await client.is_user_authorized():
                return jsonify({"status": "error", "message": "Unauthorized"}), 401

            results = {"success": [], "errors": []}

            for recipient in recipients:
                try:
                    # Recipient objesinin validasyonu
                    if "send" not in recipient or "display_name" not in recipient:
                        raise ValueError(
                            "Recipient formatı hatalı. 'send' ve 'display_name' alanları zorunlu."
                        )

                    send_to = recipient["send"]  # Kullanıcı adı veya telefon numarası
                    display_name = recipient["display_name"]  # Mesajda görünecek isim

                    # Kullanıcıyı bul (username veya telefon numarası ile)
                    entity = await client.get_entity(send_to)

                    # Mesajı kişiselleştir (Örnek: "Zahid, You are invited to the event.")
                    personalized_message = f"{display_name}, {base_message}"

                    await client.send_message(entity, personalized_message)
                    results["success"].append(send_to)
                    logger.info(f"Sent to {send_to}")

                except (ValueError, errors.FloodWaitError) as e:
                    error_msg = str(e)
                    results["errors"].append({send_to: error_msg})
                    logger.error(f"Error sending to {send_to}: {error_msg}")
                except Exception as e:
                    error_msg = "Unexpected error"
                    results["errors"].append({send_to: error_msg})
                    logger.error(f"Unexpected error for {send_to}: {str(e)}")

            return jsonify({"status": "success", "results": results})

    except Exception as e:
        logger.error(f"Send invites error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
