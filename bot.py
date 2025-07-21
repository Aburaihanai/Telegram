from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes

# ✅ Replace with your actual Telegram Bot Token
TOKEN = "8013830409:AAEHB4eF2UtNS-YCzw8EVGxt3GyJbGElNXY"

# ✅ This is the command that sends the Mini App button
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton(
            text="🛒 Open Market Locator",
            web_app=WebAppInfo(url=" https://find-shops-naija.onrender.com")  # Change this!
        )]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Welcome! Click the button below to open the Market Locator Mini App:",
        reply_markup=reply_markup
    )

# ✅ This launches your bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
