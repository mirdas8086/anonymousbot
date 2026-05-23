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

# =========================
# BOT CONFIG
# =========================

TOKEN = "8903257700:AAEInd7G_-6z-wccRN5X3_L93qY6olUfelg"
ADMIN_ID = 1812185709

# =========================
# FLASK FOR RENDER
# =========================

web = Flask(__name__)

@web.route('/')
def home():
    return "MalluMate Bot Running"

def run_web():
    web.run(host="0.0.0.0", port=10000)

Thread(target=run_web).start()

# =========================
# DATABASE
# =========================

waiting_male = []
waiting_female = []

active_chats = {}

profiles = {}

daily_limit = {}

premium_users = []

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id not in profiles:
        profiles[user_id] = {
            "name": update.effective_user.first_name,
            "age": "Not Set",
            "gender": "Not Set",
            "bio": "No bio",
        }

    await update.message.reply_text(
        "👋 Welcome to MalluMate\n\n"
        "/setprofile name age gender bio\n"
        "Example:\n"
        "/setprofile Mirdas 20 Male Hi\n\n"
        "/profile - View profile\n"
        "/find - Find Partner\n"
        "/next - Next Partner\n"
        "/stop - Stop Chat\n"
        "/users - Total Users (Admin)"
    )

# =========================
# SET PROFILE
# =========================

async def setprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    try:
        data = context.args

        name = data[0]
        age = data[1]
        gender = data[2]
        bio = " ".join(data[3:])

        profiles[user_id] = {
            "name": name,
            "age": age,
            "gender": gender,
            "bio": bio,
        }

        await update.message.reply_text("✅ Profile Updated")

    except:
        await update.message.reply_text(
            "❌ Usage:\n"
            "/setprofile name age gender bio"
        )

# =========================
# VIEW PROFILE
# =========================

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in profiles:
        p = profiles[user_id]

        await update.message.reply_text(
            f"👤 Name: {p['name']}\n"
            f"🎂 Age: {p['age']}\n"
            f"🚻 Gender: {p['gender']}\n"
            f"📝 Bio: {p['bio']}"
        )

# =========================
# FIND
# =========================

async def find(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id not in daily_limit:
        daily_limit[user_id] = 0

    if user_id not in premium_users:
        if daily_limit[user_id] >= 200:
            await update.message.reply_text(
                "❌ Daily Limit Reached.\nPremium Required."
            )
            return

    daily_limit[user_id] += 1

    if user_id in active_chats:
        await update.message.reply_text("⚠ Already connected.")
        return

    gender = profiles[user_id]["gender"].lower()

    # Male searching female
    if gender == "male":

        if waiting_female:
            partner = waiting_female.pop(0)

            active_chats[user_id] = partner
            active_chats[partner] = user_id

            await context.bot.send_message(
                user_id,
                "✅ Connected with Female Partner"
            )

            await context.bot.send_message(
                partner,
                "✅ Connected with Male Partner"
            )

            await show_partner_profile(user_id, partner, context)
            await show_partner_profile(partner, user_id, context)

        else:
            waiting_male.append(user_id)

            await update.message.reply_text(
                "⏳ Waiting for female partner..."
            )

    # Female searching male
    elif gender == "female":

        if waiting_male:
            partner = waiting_male.pop(0)

            active_chats[user_id] = partner
            active_chats[partner] = user_id

            await context.bot.send_message(
                user_id,
                "✅ Connected with Male Partner"
            )

            await context.bot.send_message(
                partner,
                "✅ Connected with Female Partner"
            )

            await show_partner_profile(user_id, partner, context)
            await show_partner_profile(partner, user_id, context)

        else:
            waiting_female.append(user_id)

            await update.message.reply_text(
                "⏳ Waiting for male partner..."
            )

    else:
        await update.message.reply_text(
            "❌ Set gender first using /setprofile"
        )

# =========================
# SHOW PARTNER PROFILE
# =========================

async def show_partner_profile(user, partner, context):
    p = profiles[partner]

    await context.bot.send_message(
        user,
        f"👤 Partner Profile\n\n"
        f"Name: {p['name']}\n"
        f"Age: {p['age']}\n"
        f"Gender: {p['gender']}\n"
        f"Bio: {p['bio']}"
    )

# =========================
# STOP CHAT
# =========================

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in active_chats:

        partner = active_chats[user_id]

        del active_chats[user_id]
        del active_chats[partner]

        await context.bot.send_message(
            user_id,
            "❌ Chat Ended"
        )

        await context.bot.send_message(
            partner,
            "❌ Partner Left"
        )

    else:
        await update.message.reply_text(
            "⚠ No Active Chat"
        )

# =========================
# NEXT CHAT
# =========================

async def next_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await stop(update, context)
    await find(update, context)

# =========================
# HANDLE MESSAGES
# =========================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.chat_id

    if user_id in active_chats:

        partner = active_chats[user_id]

        await context.bot.send_message(
            partner,
            update.message.text
        )

# =========================
# ADMIN USERS
# =========================

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id == ADMIN_ID:

        total = (
            len(waiting_male)
            + len(waiting_female)
            + len(active_chats)
        )

        await update.message.reply_text(
            f"👥 Total Users: {total}"
        )

# =========================
# PREMIUM
# =========================

async def premium(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.chat_id == ADMIN_ID:

        try:
            uid = int(context.args[0])

            premium_users.append(uid)

            await update.message.reply_text(
                "✅ Premium Added"
            )

        except:
            await update.message.reply_text(
                "/premium USER_ID"
            )

# =========================
# BOT START
# =========================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("setprofile", setprofile))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("find", find))
app.add_handler(CommandHandler("stop", stop))
app.add_handler(CommandHandler("next", next_chat))
app.add_handler(CommandHandler("users", users))
app.add_handler(CommandHandler("premium", premium))

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

print("Bot Running...")

app.run_polling()
