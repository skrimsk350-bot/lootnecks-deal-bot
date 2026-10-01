from flask import Flask
from threading import Thread
import os
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Flask Keep Alive - Railway Crush Fix
app = Flask('')
@app.route('/')
def home():
    return "LootNecks Bot is Alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# Telegram Bot Token - Railway Variable থেকে নেবে
BOT_TOKEN = os.environ.get("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! LootNecks Bot Ready hai 🔥\nAmazon Link bhejo, main deal image bana dunga.")

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    # Yaha tumhara purana image banane ka code rahega
    await update.message.reply_text(f"Link mila: {url}\nImage bana raha hu...")

def main():
    Thread(target=run_flask).start()
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    application.run_polling()

if __name__ == "__main__":
    main()
