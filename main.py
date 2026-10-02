import os
import threading
import asyncio
from flask import Flask

# তোমার আসল Deal Bot File টা import করছি
import deal_bot
from telethon import events

app = Flask(__name__)

@app.route('/')
def home():
    return "LootNecks Bot is Alive - Forwarding from Genie Loot!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

async def run_telethon_bot():
    await deal_bot.client.connect()
    print("Connected to Telegram, Listening Genie Loot...")

    @deal_bot.client.on(events.NewMessage(chats=deal_bot.SOURCE_NAME))
    async def handler(event):
        try:
            text = event.message.message or event.message.text
            if not text:
                return
            print(f"New deal found: {text[:50]}")
            # তোমার LootNecks চ্যানেলে পাঠাবে
            await deal_bot.client.send_message(deal_bot.DESTINATION, text)
            print("Forwarded to LootNecks!")
        except Exception as e:
            print(f"Error: {e}")

    await deal_bot.client.run_until_disconnected()

def start_bot():
    asyncio.run(run_telethon_bot())

if __name__ == "__main__":
    # 1. Flask আলাদা Thread এ চালাও
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    # 2. Bot Main Thread এ চালাও
    start_bot()
