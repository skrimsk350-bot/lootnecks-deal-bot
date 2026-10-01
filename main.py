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

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

def make_clean_caption(original_text):
    if not original_text:
        return "", ""

    # 1. সব লিংক বের করা - amzn.to এবং fkrt.to দুটোই
    links = re.findall(r'https?://[^\s]+', original_text)
    final_link = ""
    for l in links:
        if "amzn" in l or "amazon" in l or "fkrt" in l or "flipkart" in l:
            final_link = l.strip()
            break
    if not final_link and links:
        final_link = links[0]

    # Affiliate Tag - শুধু Amazon এর জন্য
    if final_link and ("amzn" in final_link or "amazon" in final_link):
        if 'tag=' in final_link:
            final_link = re.sub(r'tag=[^&\s]+', f'tag={AFFILIATE_TAG}', final_link)
        else:
            sep = '&' if '?' in final_link else '?'
            final_link = f"{final_link}{sep}tag={AFFILIATE_TAG}"

    # 2. দাম বের করা - তোমার Screenshot এর মতো
    # ₹200 | Regular: 955 এই ফরম্যাটটা খুঁজে বের করবে
    price_line = ""
    price_match = re.search(r'(₹[\d\.k]+\s*\|\s*Regular:.*)', original_text, re.IGNORECASE)
    if price_match:
        price_line = price_match.group(1).strip()
    else:
        # যদি ওই ফরম্যাট না থাকে, নিজে বানাবে
        prices = re.findall(r'₹\s?([\d\.k]+)', original_text)
        if len(prices) >= 2:
            price_line = f"₹{prices[0]} | Regular: {prices[1]}"
        elif len(prices) == 1:
            price_line = f"₹{prices[0]}"

    # 3. Loot / Jaldi Tag
    tag = "Loot 🔥"
    if "jaldi" in original_text.lower():
        tag = "Jaldi 💥"

    if price_line:
        clean_text = f"{tag} {price_line}\n\n{final_link}"
    else:
        clean_text = f"{tag}\n\n{final_link}"

    return clean_text, final_link

@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', None)
        if chat_title == SOURCE_NAME:
            original_text = event.raw_text
            if not original_text or "https://" not in original_text:
                return

            print(f"New post from {SOURCE_NAME}")
            clean_caption, _ = make_clean_caption(original_text)

            if event.message.photo or event.message.document:
                file_path = await event.message.download_media()
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                with open(file_path, 'rb') as f:
                    files = {'photo': f}
                    data = {'chat_id': DESTINATION, 'caption': clean_caption}
                    requests.post(url, data=data, files=files, timeout=30)
                os.remove(file_path)
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {"chat_id": DESTINATION, "text": clean_caption, "disable_web_page_preview": False}
                requests.post(url, data=payload, timeout=30)

    except Exception as e:
        print("Error:", e)

async def main():
    await client.connect()
    print("Bot Live - Genie Loot Style Format Active...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
        
