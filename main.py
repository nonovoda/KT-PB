import os
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime, timedelta
import aiohttp

# --- Настройки ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "your_bot_token")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "your_chat_id")
KEITARO_API_KEY = os.getenv("KEITARO_API_KEY", "your_keitaro_api_key")
KEITARO_URL = os.getenv("KEITARO_URL", "https://your-tracker.com")

# --- Telegram bot ---
telegram_app = Application.builder().token(TELEGRAM_TOKEN).build()
bot = Bot(token=TELEGRAM_TOKEN)

# --- FastAPI ---
app = FastAPI()


@app.get("/")
async def root():
    return {"status": "ok", "message": "Keitaro Bot Running"}


@app.api_route("/webhook", methods=["GET", "POST"])
async def webhook(request: Request):
    data = dict(request.query_params)
    if request.method == "POST":
        try:
            data = await request.json()
        except:
            data = await request.form()

    # Формируем сообщение
    sub1 = data.get("sub1", "N/A")
    status = data.get("status", "N/A")
    revenue = data.get("revenue", "0")
    currency = data.get("currency", "USD")
    campaign = data.get("campaign", "N/A")
    adset = data.get("adset", "N/A")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    msg = (
        "📥 <b>Новая конверсия!</b>\n\n"
        f"🎯 <b>Событие:</b> <i>{status}</i>\n"
        f"💰 <b>Выплата:</b> <i>{revenue} {currency}</i>\n"
        f"📛 <b>Кампания:</b> <i>{campaign}</i>\n"
        f"📛 <b>Адсет:</b> <i>{adset}</i>\n"
        f"⏰ <b>Время:</b> <i>{timestamp}</i>"
    )

    # Отправка в Telegram
    try:
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=msg, parse_mode="HTML")
        return {"status": "ok"}
    except Exception as e:
        return {"status": "error", "details": str(e)}

# --- Функция для получения статистики за 7 дней ---
async def fetch_7days_stats_from_keitaro():
    headers = {"Api-Key": KEITARO_API_KEY}
    date_to = datetime.now().date()
    date_from = date_to - timedelta(days=6)

    params = {
        "grouping": "day",
        "timezone": "UTC",
        "range": "custom",
        "from": str(date_from),
        "to": str(date_to),
        "columns[]": ["clicks", "unique_clicks", "goal1", "goal2", "goal3", "payout"]
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{KEITARO_URL}/admin_api/v1/statistics", headers=headers, params=params) as resp:
            if resp.status != 200:
                return False, f"Ошибка Keitaro API: {resp.status}"
            data = await resp.json()
            return True, data


# --- Команда /stats_7days ---
async def stats_7days_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏳ Получаю статистику за 7 дней...")

    ok, data = await fetch_7days_stats_from_keitaro()
    if not ok:
        await update.message.reply_text(f"❌ {data}")
        return

    clicks = uniques = reg = dep = rd = 0
    payout = 0.0

    for row in data.get("rows", []):
        clicks += row.get("clicks", 0)
        uniques += row.get("unique_clicks", 0)
        reg += row.get("goal1", 0)
        dep += row.get("goal2", 0)
        rd += row.get("goal3", 0)
        payout += float(row.get("payout", 0))

    msg = (
        "📊 <b>Статистика за последние 7 дней</b>\n\n"
        f"👁 <b>Клики:</b> {clicks} (уник: {uniques})\n"
        f"🆕 <b>Регистрации:</b> {reg}\n"
        f"💵 <b>Депозиты:</b> {dep}\n"
        f"🔁 <b>RD:</b> {rd}\n"
        f"💰 <b>Доход:</b> {payout:.2f} USD"
    )

    await update.message.reply_text(msg, parse_mode="HTML")

# --- Регистрация команды ---
telegram_app.add_handler(CommandHandler("stats_7days", stats_7days_command))


# --- Запуск ---
if __name__ == "__main__":
    import uvicorn
    import asyncio

    loop = asyncio.get_event_loop()
    loop.create_task(telegram_app.initialize())
    loop.create_task(telegram_app.start())
    uvicorn.run(app, host="0.0.0.0", port=PORT)
