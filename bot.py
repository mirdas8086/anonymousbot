from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

TOKEN = "8903257700:AAEInd7G_-6z-wccRN5X3_L93qY6olUfelg"
ADMIN_ID = 1812185709

waiting_users = []
active_chats = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to Mallu Connect\n\n"
        "/find - Find Partner\n"
        "/next - Next Partner\n"
        "/stop - Stop Chat\n"
        "/users - Total Users (Admin)"
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

        await context.bot.send_message(user_id, "✅ Connected to a partner!")
        await context.bot.send_message(partner, "✅ Connected to a partner!")

    else:
        if user_id not in waiting_users:
            waiting_users.append(user_id)

        await update.message.reply_text("⏳ Waiting for partner...")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in active_chats:
        partner = active_chats[user_id]

        del active_chats[user_id]
        del active_chats[partner]

        await context.bot.send_message(user_id, "❌ Chat stopped.")
        await context.bot.send_message(partner, "❌ Partner disconnected.")
    else:
        await update.message.reply_text("No active chat.")


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


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id == ADMIN_ID:
        total = len(waiting_users) + len(active_chats)
        await update.message.reply_text(f"👥 Users: {total}")


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("find", find))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("next", next_chat))
app.add_handler(CommandHandler("users", users))

app.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)

app.run_polling()
