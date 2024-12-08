import requests
from user_agent import generate_user_agent
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio
import time

# In-memory user database to store user sessions (use a persistent database in a real app)
user_sessions = {}

# Function to handle login process
def login_ig(email, password):
    url = 'https://www.instagram.com/api/v1/web/accounts/login/ajax/'
    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate',
        'accept-language': 'en-US,en;q=0.8',
        'content-length': '303',
        'content-type': 'application/x-www-form-urlencoded',
        'cookie': 'mid=ZQZC9QAEAAG9NicS3jBHkYqHlp8C; ig_nrcb=1; ig_did=AC6A65E6-8577-4CDE-8F3F-4B24D5787A91; datr=D0MGZZ_cUrCctc7jPE92HUgb; csrftoken=NYaOlpVmXUwzESZVfuFOYqbJ0gHzcvks',
        'dpr': '1',
        'origin': 'https://www.instagram.com',
        'referer': 'https://www.instagram.com/',
        'user-agent': str(generate_user_agent()),
        'viewport-width': '808',
        'x-asbd-id': '129477',
        'x-csrftoken': 'NYaOlpVmXUwzESZVfuFOYqbJ0gHzcvks',
        'x-ig-app-id': '936619743392459',
        'x-ig-www-claim': '0',
        'x-instagram-ajax': '1008686036',
        'x-requested-with': 'XMLHttpRequest',
    }
    
    timestamp = str(time.time()).split('.')[0]
    data = {
        'enc_password': f'#PWD_INSTAGRAM_BROWSER:0:{timestamp}:{password}',
        'optIntoOneTap': 'false',
        'queryParams': '{}',
        'trustedDeviceRecords': '{}',
        'username': email,
    }
    
    response = requests.post(url, headers=headers, data=data)
    if "userId" in response.text:
        session_id = response.cookies.get("sessionid", "No session ID found")
        return f"Your Instagram Session ID:\n```\n{session_id}\n```"
    else:
        return f"Login failed: {response.text}"

# Command handler for /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📝 Login to Instagram", callback_data="login")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="help")],
        [InlineKeyboardButton("👤 Check Session", callback_data="check_session")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome to the IG Login Bot! \n\n"
        "I can help you log in to Instagram and retrieve your session ID.\n"
        "Use the buttons below to get started:\n\n"
        "✨ Use /login <email> <password> to log in manually.\n\n"
        "Choose an option below to proceed.",
        reply_markup=reply_markup
    )

# Callback query handler
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "login":
        await query.message.reply_text(
            "📧 Send your login details in the following format:\n"
            "`/login <email> <password>`\n\n"
            "Make sure to replace `<email>` and `<password>` with your actual details.",
            parse_mode="Markdown"
        )
    elif query.data == "help":
        await query.message.reply_text(
            "ℹ️ This bot helps you log in to Instagram and retrieve your session ID.\n"
            "Commands:\n"
            "/start - Show the welcome message\n"
            "/login - Log in to Instagram and get your session ID\n"
            "/check_session - Check if you have a valid session\n"
        )
    elif query.data == "check_session":
        user_id = str(query.from_user.id)
        if user_id in user_sessions:
            session_id = user_sessions[user_id]
            await query.message.reply_text(
                f"🛡️ Your current session ID is:\n```\n{session_id}\n```",
                parse_mode="Markdown"
            )
        else:
            await query.message.reply_text("❌ You don't have a session ID. Please log in first.")

# Command handler for /login
async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: /login <email> <password>")
        return
    
    email = context.args[0]
    password = ' '.join(context.args[1:])
    result = login_ig(email, password)
    
    # Check if login was successful and store the session
    if "Your Instagram Session ID:" in result:
        user_id = str(update.message.from_user.id)
        session_id = result.split("\n")[1].strip("`")
        user_sessions[user_id] = session_id  # Save session ID in memory
        await update.message.reply_text(
            f"✅ Login successful! Your session ID has been stored.\n"
            "You can check your session using the button below or the /check_session command.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(result, parse_mode="Markdown")

async def run_bot():
    bot_token = "7642316354:AAGLmFJaATCNwuq36SvWNOM7LvlEmkW3wsQ"
    app = Application.builder().token(bot_token).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CommandHandler("login", login))
    
    print("Bot is running...")
    await app.initialize()  # Initialize application
    await app.start()       # Start the bot
    await app.updater.start_polling()  # Start polling
    await asyncio.Event().wait()  # Keeps the bot running indefinitely

if __name__ == "__main__":
    try:
        asyncio.run(run_bot())
    except RuntimeError as e:
        if "This event loop is already running" in str(e):
            print("Detected a running event loop. Using existing loop.")
            loop = asyncio.get_event_loop()
            loop.create_task(run_bot())
            loop.run_forever()
        else:
            raise