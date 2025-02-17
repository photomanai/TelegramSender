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


@app.route("/send-code", methods=["POST"])
async def send_code():
    try:
        data = request.json
        phone_number = data.get("phone_number")
        if not phone_number:
            return (
                jsonify({"status": "error", "message": "Telefon numarası gerekli"}),
                400,
            )

        client = get_client(phone_number)
        await client.connect()

        if await client.is_user_authorized():
            return jsonify({"status": "success", "message": "Zaten giriş yapılmış"})

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
            return jsonify({"status": "error", "message": "Eksik bilgi"}), 400

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
        return jsonify({"status": "success", "message": "Giriş başarılı"})

    except Exception as e:
        logger.error(f"Verify error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/send-invites", methods=["POST"])
async def send_invites():
    try:
        data = request.json
        phone_number = data.get("phone_number")
        message = data.get("message", "Merhaba! Bu bir test mesajıdır.")
        recipients = data.get("recipients", [])

        if not phone_number:
            return (
                jsonify({"status": "error", "message": "Telefon numarası gerekli"}),
                400,
            )

        client = get_client(phone_number)
        await client.connect()

        if not await client.is_user_authorized():
            logger.warning(f"Unauthorized session for {phone_number}")
            return jsonify({"status": "error", "message": "Yetkisiz giriş"}), 401

        results = {"success": [], "errors": []}

        for recipient in recipients:
            try:
                # Kullanıcıyı direkt olarak bulmaya çalış
                entity = await client.get_entity(recipient)
                await client.send_message(entity, message)
                results["success"].append(recipient)
                logger.info(f"Sent to {recipient}")
            except (ValueError, errors.FloodWaitError) as e:
                results["errors"].append({recipient: str(e)})
                logger.error(f"Error sending to {recipient}: {str(e)}")
            except Exception as e:
                results["errors"].append({recipient: "Beklenmeyen hata"})
                logger.error(f"Unexpected error: {str(e)}")

        return jsonify({"status": "success", "results": results})

    except Exception as e:
        logger.error(f"Send invites error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
