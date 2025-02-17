# api/index.py
from flask import Flask, request, jsonify
from telethon import TelegramClient, errors
from telethon.sessions import StringSession
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import logging

# MongoDB bağlantısı
load_dotenv()
mongo_client = MongoClient(os.getenv("MONGO_URI"))
db = mongo_client.telegram_sessions
sessions_collection = db.sessions

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telethon ayarları
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")


def get_client(phone_number):
    """MongoDB'den session'ı al veya yeni oluştur"""
    record = sessions_collection.find_one({"phone": phone_number})

    if record:
        return TelegramClient(StringSession(record["session"]), api_id, api_hash)
    else:
        new_session = StringSession()
        sessions_collection.insert_one(
            {"phone": phone_number, "session": new_session.save(), "active": False}
        )
        return TelegramClient(new_session, api_id, api_hash)


@app.route("/send-code", methods=["POST"])
async def send_code():
    try:
        data = request.json
        phone_number = data.get("phone_number")

        client = get_client(phone_number)
        async with client:
            if await client.is_user_authorized():
                return jsonify({"status": "already_authorized"})

            sent_code = await client.send_code_request(phone_number)
            sessions_collection.update_one(
                {"phone": phone_number},
                {"$set": {"phone_code_hash": sent_code.phone_code_hash}},
            )
            return jsonify(
                {"status": "code_sent", "phone_code_hash": sent_code.phone_code_hash}
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
        password_2fa = data.get("password_2fa")

        record = sessions_collection.find_one({"phone": phone_number})
        if not record or "phone_code_hash" not in record:
            return jsonify({"status": "error", "message": "Session not found"}), 404

        client = get_client(phone_number)
        async with client:
            try:
                await client.sign_in(
                    phone_number, code=code, phone_code_hash=record["phone_code_hash"]
                )
            except errors.SessionPasswordNeededError:
                if not password_2fa:
                    return jsonify({"status": "2fa_required"}), 402
                await client.sign_in(password=password_2fa)

            # Güncellenmiş session'ı kaydet
            session_string = client.session.save()
            sessions_collection.update_one(
                {"phone": phone_number},
                {"$set": {"session": session_string, "active": True}},
            )
            return jsonify({"status": "authorized"})

    except Exception as e:
        logger.error(f"Verify error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/send-invites", methods=["POST"])
async def send_invites():
    try:
        data = request.json
        phone_number = data.get("phone_number")
        message = data.get("message", "Default invitation message")
        recipients = data.get("recipients", [])

        client = get_client(phone_number)
        async with client:
            if not await client.is_user_authorized():
                return jsonify({"status": "unauthorized"}), 401

            results = {"success": [], "errors": []}
            for recipient in recipients:
                try:
                    entity = await client.get_entity(recipient["send"])
                    await client.send_message(
                        entity, f"{recipient['display_name']}, {message}"
                    )
                    results["success"].append(recipient["send"])
                except Exception as e:
                    results["errors"].append(
                        {"recipient": recipient["send"], "error": str(e)}
                    )

            return jsonify({"status": "success", "results": results})

    except Exception as e:
        logger.error(f"Send invites error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run()
