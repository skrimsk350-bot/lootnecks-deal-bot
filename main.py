import os
import re
import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION = os.environ["TELEGRAM_SESSION"]
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "sahinoorstore-21")

SOURCE_NAME = "Genie Loot"
DESTINATION = "@LootNecks"

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH
)

def make_clean_caption(original_text):
    if not original_text:
        return original_text

    # 1. Link বের করা
    link_match = re.findall(r'https?://[^\s]+', original_text)
    amazon_link = ""
    for l in link_match:
        if "amazon" in l or "amzn" in l:
            amazon_link = l
            break

    # Affiliate Tag Add করা
    if amazon_link:
        if 'tag=' in amazon_link:
            amazon_link = re.sub(r'tag=[^&]+', f'tag={AFFILIATE_TAG}', amazon_link)
        else:
            sep = '&' if '?' in amazon_link else '?'
            amazon_link = f"{amazon_link}{sep}tag={AFFILIATE_TAG}"

    # 2. দাম বের করা
    prices = re.findall(r'₹\s?(\d+)', original_text)
    sale_price = prices[0] if len(prices) > 0 else ""
    reg_price = prices[1] if len(prices) > 1 else ""

    # 3. Title - প্রথম 2 লাইন থেকে, Description বাদ
    lines = original_text.split('\n')
    # "This outfit is Manufactured..." এই লাইনগুলো বাদ
    title = lines[0].replace('**', '').strip()
    if len(title) > 80:
        title = title[:80]

    # 4. নতুন Clean Caption
    clean_text = f"""🔥 {title}

💰 Loot Price: ₹{sale_price}"""

    if reg_price:
        clean_text += f" | Reg: ₹{reg_price}\n"
    else:
        clean_text += "\n"

    if amazon_link:
        clean_text += f"\n👉 Buy Now: {amazon_link}\n"

    clean_text += f"\n⏰ Limited Stock - Jaldi Looto!\n\n@LootNecks"

    return clean_text, amazon_link

@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', None)

        if chat_title == SOURCE_NAME:
            original_text = event.raw_text
            if not original_text:
                return

            print(f"New message from {SOURCE_NAME}")

            clean_caption, _ = make_clean_caption(original_text)

            # যদি ছবি থাকে, তাহলে ছবি সহ পাঠাও
            if event.message.photo or event.message.document:
                # ফাইল ডাউনলোড করে Bot API দিয়ে পাঠানো
                file_path = await event.message.download_media()

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                with open(file_path, 'rb') as f:
                    files = {'photo': f}
                    data = {'chat_id': DESTINATION, 'caption': clean_caption}
                    response = requests.post(url, data=data, files=files, timeout=30)
                os.remove(file_path)
                print("Photo sent:", response.text)
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": DESTINATION,
                    "text": clean_caption,
                    "disable_web_page_preview": False
                }
                response = requests.post(url, data=payload, timeout=30)
                print("Message sent:", response.text)

    except Exception as e:
        print("Error:", e)

async def main():
    print("Connecting...")
    await client.connect()
    if not await client.is_user_authorized():
        print("ERROR: Session not authorized.")
        return
    print("Connected. LootNecks Bot is Live with Clean Format...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
