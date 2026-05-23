from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 1812185709

AGE, GENDER, INTEREST, BIO = range(4)

users_data = {}
waiting_users = []
active_chats = {}
pending_requests = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in users_data:
        await update.message.reply_text(
            "👋 Welcome Back!\n\n"
            "/find - Find Partner\n"
            "/next - Next Partner\n"
            "/stop - Stop Chat\n"
            "/profile - View Profile\n"
            "/users - Admin Only"
        )
        return ConversationHandler.END

    await update.message.reply_text("🎂 Enter your age:")
    return AGE


async def age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    users_data[user_id] = {}
    users_data[user_id]["age"] = update.message.text

    keyboard = [
        [
            InlineKeyboardButton("👦 Male", callback_data="male"),
            InlineKeyboardButton("👧 Female", callback_data="female"),
        ]
    ]

    await update.message.reply_text(
        "Select your gender:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return GENDER


async def gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.message.chat_id

    users_data[user_id]["gender"] = query.data

    keyboard = [
        [
            InlineKeyboardButton("👦 Boys", callback_data="male"),
            InlineKeyboardButton("👧 Girls", callback_data="female"),
            InlineKeyboardButton("🤝 Both", callback_data="both"),
        ]
    ]

    await query.message.reply_text(
        "Interested in:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )

    return INTEREST


async def interest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.message.chat_id

    users_data[user_id]["interest"] = query.data

    await query.message.reply_text("📝 Write your bio:")
    return BIO


async def bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    users_data[user_id]["bio"] = update.message.text
    users_data[user_id]["premium"] = False
    users_data[user_id]["find_count"] = 0

    await update.message.reply_text(
        "✅ Profile created!\n\n"
        "/find - Find Partner"
    )

    return ConversationHandler.END


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id not in users_data:
        return

    data = users_data[user_id]

    text = (
        f"👤 Your Profile\n\n"
        f"🎂 Age: {data['age']}\n"
        f"🚻 Gender: {data['gender']}\n"
        f"❤️ Interested: {data['interest']}\n"
        f"📝 Bio: {data['bio']}\n"
        f"💎 Premium: {data['premium']}"
    )

    await update.message.reply_text(text)


async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id not in users_data:
        await update.message.reply_text("/start first")
        return

    if not users_data[user_id]["premium"]:
        if users_data[user_id]["find_count"] >= 200:
            await update.message.reply_text(
                "❌ Daily limit reached.\nBuy Premium."
            )
            return

    users_data[user_id]["find_count"] += 1

    for partner in waiting_users:
        if partner != user_id:
            partner_data = users_data[partner]

            keyboard = [
                [
                    InlineKeyboardButton(
                        "✅ Accept",
                        callback_data=f"accept_{partner}"
                    ),
                    InlineKeyboardButton(
                        "❌ Skip",
                        callback_data=f"skip_{partner}"
                    ),
                ]
            ]

            text = (
                f"👤 New Match\n\n"
                f"🎂 Age: {partner_data['age']}\n"
                f"🚻 Gender: {partner_data['gender']}\n"
                f"❤️ Interested: {partner_data['interest']}\n"
                f"📝 Bio: {partner_data['bio']}"
            )

            pending_requests[user_id] = partner

            await update.message.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(keyboard),
            )

            return

    if user_id not in waiting_users:
        waiting_users.append(user_id)

    await update.message.reply_text("⏳ Waiting for partner...")


async def match_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.message.chat_id
    data = query.data

    if data.startswith("accept_"):
        partner = int(data.split("_")[1])

        active_chats[user_id] = partner
        active_chats[partner] = user_id

        if partner in waiting_users:
            waiting_users.remove(partner)

        await query.message.reply_text("✅ Connected!")

        await context.bot.send_message(
            partner,
            "✅ Someone accepted your profile!"
        )

    elif data.startswith("skip_"):
        await query.message.reply_text("❌ Skipped")


async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in active_chats:
        partner = active_chats[user_id]

        del active_chats[user_id]
        del active_chats[partner]

        await context.bot.send_message(user_id, "❌ Chat stopped")
        await context.bot.send_message(
            partner,
            "❌ Partner disconnected"
        )

    else:
        await update.message.reply_text("No active chat")


async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop(update, context)
    await find(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in active_chats:
        partner = active_chats[user_id]

        if update.message.text:
            await context.bot.send_message(
                partner,
                update.message.text
            )

        elif update.message.photo:
            await context.bot.send_photo(
                partner,
                update.message.photo[-1].file_id,
                caption=update.message.caption,
            )

        elif update.message.voice:
            await context.bot.send_voice(
                partner,
                update.message.voice.file_id,
            )


async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💎 Premium Plans\n\n"
        "₹49 - Weekly\n"
        "₹99 - Monthly\n\n"
        "Benefits:\n"
        "✅ Unlimited Matches\n"
        "✅ Gender Filters\n"
        "✅ Priority Matching\n"
        "✅ No Limits"
    )


async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id == ADMIN_ID:
        total = len(users_data)

        premium_users = sum(
            1 for u in users_data.values() if u["premium"]
        )

        await update.message.reply_text(
            f"👥 Total Users: {total}\n"
            f"💎 Premium Users: {premium_users}\n"
            f"🔥 Active Chats: {len(active_chats)//2}"
        )


app = ApplicationBuilder().token(TOKEN).build()

conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, age)],
        GENDER: [CallbackQueryHandler(gender)],
        INTEREST: [CallbackQueryHandler(interest)],
        BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, bio)],
    },
    fallbacks=[],
)

app.add_handler(conv_handler)

app.add_handler(CommandHandler("find", find))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("next", next_chat))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("premium", premium))
app.add_handler(CommandHandler("users", users))

app.add_handler(CallbackQueryHandler(match_response))

app.add_handler(
    MessageHandler(
        filters.TEXT | filters.PHOTO | filters.VOICE,
        handle_message,
    )
)

print("Bot Running...")
app.run_polling()
