import os
import requests
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION = os.environ["TELEGRAM_SESSION"]

SOURCE_NAME = "Genie Loot"
DESTINATION = "@LootNecks"

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH
)

async def main():
    print("Connecting to Telegram...")

    await client.connect()

    if not await client.is_user_authorized():
        print("ERROR: Telegram session is not authorized.")
        return

    print("Connected successfully.")

    dialogs = await client.get_dialogs()

    source = None

    for dialog in dialogs:
        if dialog.is_channel and dialog.name == SOURCE_NAME:
            source = dialog.entity
            break

    if source is None:
        print("ERROR: Source channel not found.")
        return

    print("Source channel found:", SOURCE_NAME)

    messages = await client.get_messages(source, limit=1)

    if not messages:
        print("No messages found.")
        return

    message = messages[0]

    text = message.message or ""

    if not text:
        print("Latest message has no text.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": DESTINATION,
            "text": text
        },
        timeout=30
    )

    print("Telegram response:", response.text)


with client:
    client.loop.run_until_complete(main())
