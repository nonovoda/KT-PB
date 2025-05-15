import os
from fastapi import FastAPI, Request
from telegram import Bot
from datetime import datetime

# Telegram config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID")  # числовой ID

bot = Bot(token=TELEGRAM_TOKEN)

# FastAPI app
app = FastAPI()


@app.get("/")
async def root():
    return {"status": "ok", "message": "Keitaro Postback Bot is running!"}


@app.api_route("/webhook", methods=["GET", "POST"])
async def webhook(request: Request):
    # Получаем данные из запроса
    data = dict(request.query_params)
    if request.method == "POST":
        try:
            data = await request.json()
        except:
            data = await request.form()

    # Формируем сообщение
    sub1 = data.get("sub1", "N/A")
    status = data.get("status", "N/A")
    payout = data.get("payout", "0")
    currency = data.get("currency", "USD")
    campaign = data.get("campaign", "N/A")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    msg = (
        "📥 <b>Keitaro Postback</b>\n\n"
        f"👤 <b>sub1:</b> <i>{sub1}</i>\n"
        f"🎯 <b>Status:</b> <i>{status}</i>\n"
        f"💰 <b>Payout:</b> <i>{payout} {currency}</i>\n"
        f"📛 <b>Campaign:</b> <i>{campaign}</i>\n"
        f"⏰ <b>Time:</b> <i>{timestamp}</i>"
    )

    # Отправка в Telegram
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="HTML")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}
