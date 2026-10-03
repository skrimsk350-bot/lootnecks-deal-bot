import os
import re
import requests
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
SESSION = os.environ["TELEGRAM_SESSION"]
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "lootnecks-21")

SOURCE_NAME = "Genie Loot"
DESTINATION = "@LootNecks"

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

def make_clean_caption(text):
    if not text: return ""

    # 1. একটাই Amazon লিংক বের করবো
    links = re.findall(r'https?://[^\s]+', text)
    amazon_link = ""
    for l in links:
        if "amzn" in l or "amazon" in l:
            amazon_link = l.split('?')[0] #? এর আগের লিংক নেবো
            break
    if not amazon_link and links:
        amazon_link = links[0].split('?')[0]

    # Tag বসানো
    if amazon_link:
        amazon_link = f"{amazon_link}?tag={AFFILIATE_TAG}"

    # 2. দাম বের করা
    prices = re.findall(r'₹\s?([0-9,]+)', text)
    sale_price = prices[0] if len(prices)>0 else ""
    mrp = prices[1] if len(prices)>1 else ""

    # 3. Discount %
    discount = ""
    m = re.search(r'(\d+)\s*%\s*off', text, re.I)
    if m:
        discount = f"{m.group(1)}% OFF"
    elif sale_price and mrp:
        try:
            s = int(sale_price.replace(',',''))
            r = int(mrp.replace(',',''))
            if r > s:
                discount = f"{int((r-s)/r*100)}% OFF"
        except: pass

    # 4. Title
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    title = "Loot Deal"
    for line in lines:
        if 'http' not in line and '₹' not in line and len(line)>5 and 'Loot' not in line:
            title = re.sub(r'[*#_]', '', line)[:90]
            break

    # 5. Final Clean Format - তোমার পছন্দ মতো
    caption = f"🛍️ {title}\n\n"
    if sale_price:
        caption += f"🔥 Deal Price: ₹{sale_price}\n"
    if mrp:
        caption += f"❌ MRP: ₹{mrp}\n"
    if discount:
        caption += f"💥 Discount: {discount}\n"
    caption += f"\n🛒 Buy Now 👉 {amazon_link}\n\n✨ @LootNecks"

    return caption

@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()
        if getattr(chat, 'title', '')!= SOURCE_NAME:
            return

        text = event.raw_text
        if not text: return

        clean_caption = make_clean_caption(text)
        print(f"New Deal: {clean_caption[:50]}")

        # ছবি দিয়ে পাঠাবো, তাই বড় Preview আসবে না
        if event.message.photo:
            path = await event.message.download_media()
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(path, 'rb') as f:
                requests.post(url, data={'chat_id': DESTINATION, 'caption': clean_caption}, files={'photo': f}, timeout=30)
            os.remove(path)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, data={'chat_id': DESTINATION, 'text': clean_caption, 'disable_web_page_preview': True}, timeout=30)

    except Exception as e:
        print("Error:", e)

async def main():
    await client.start()
    print("LootNecks Railway Bot Live!")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
