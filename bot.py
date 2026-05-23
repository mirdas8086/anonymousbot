from flask import Flask
from threading import Thread

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8903257700:AAEInd7G_-6z-wccRN5X3_L93qY6olUfelg"

# ================= WEB =================

web = Flask(__name__)

@web.route('/')
def home():
    return "Bot Running"

def run():
    web.run(host="0.0.0.0", port=10000)

Thread(target=run).start()

# ================= BOT =================

waiting_users = []
active_chats = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to MalluMate\n\n"
        "/find - Find Partner\n"
        "/next - Next Partner\n"
        "/stop - Stop Chat"
    )

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in active_chats:
        await update.message.reply_text("Already connected.")
        return

    if waiting_users and waiting_users[0] != user_id:

        partner = waiting_users.pop(0)

        active_chats[user_id] = partner
        active_chats[partner] = user_id

        await context.bot.send_message(
            user_id,
            "✅ Connected!"
        )

        await context.bot.send_message(
            partner,
            "✅ Connected!"
        )

    else:
        if user_id not in waiting_users:
            waiting_users.append(user_id)

        await update.message.reply_text(
            "⏳ Waiting for partner..."
        )

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id

    if user_id in active_chats:

        partner = active_chats[user_id]

        del active_chats[user_id]
        del active_chats[partner]

        await context.bot.send_message(
            user_id,
            "❌ Chat stopped."
        )

        await context.bot.send_message(
            partner,
            "❌ Partner disconnected."
        )

    else:
        await update.message.reply_text(
            "No active chat."
        )

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop(update, context)
    await find(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.message.chat_id

    if user_id in active_chats:

        partner = active_chats[user_id]

        await context.bot.send_message(
            partner,
            update.message.text
        )

# ================= START APP =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("find", find))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("next", next_chat))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

print("Bot Running...")

app.run_polling()
