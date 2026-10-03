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

def get_final_link(short_url):
    try:
        r = requests.head(short_url, allow_redirects=True, timeout=10)
        long_url = r.url
        m = re.search(r'/dp/([A-Z0-9]{10})', long_url)
        if m:
            return f"https://www.amazon.in/dp/{m.group(1)}/?tag={AFFILIATE_TAG}"
        return long_url.split("?")[0] + f"?tag={AFFILIATE_TAG}"
    except:
        return short_url

def make_clean_caption(original_text):
    if not original_text:
        return "", ""

    links = re.findall(r'https?://[^\s]+', original_text)
    amazon_link = ""
    for l in links:
        if "amzn.to" in l or "amazon" in l:
            amazon_link = l
            break

    # FIX 1 & 2: সঠিক Affiliate লিংক
    if amazon_link:
        amazon_link = get_final_link(amazon_link)
    else:
        return "", "" # Amazon লিংক না পেলে পোস্ট করবে না

    prices = re.findall(r'₹\s?([0-9,]+)', original_text)
    sale_price = prices[0] if len(prices) > 0 else ""
    reg_price = prices[1] if len(prices) > 1 else ""

    discount_match = re.search(r'(\d+%\s*(?:OFF|off))', original_text, re.IGNORECASE)
    discount_text = discount_match.group(1) if discount_match else ""

    if not discount_text and sale_price and reg_price:
        try:
            s = int(sale_price.replace(',', ''))
            r_ = int(reg_price.replace(',', ''))
            if r_ > s:
                discount_text = f"{int(((r_-s)/r_)*100)}% OFF"
        except:
            pass

    lines = [l.strip() for l in original_text.split('\n') if l.strip()]
    title = "Special Loot Deal"
    for line in lines:
        clean = line.replace('**','').strip()
        if not clean.startswith('http') and '₹' not in clean and len(clean) > 5 and 'http' not in clean.lower():
            title = clean[:80]
            break

    # FIX 3: দাম না থাকলে লেখা দেখাবে না
    clean_text = f"🛍️ {title}\n\n"
    if sale_price:
        clean_text += f"🔥 Deal: ₹{sale_price}"
        if reg_price:
            clean_text += f" | MRP: ₹{reg_price}"
        if discount_text:
            clean_text += f" ({discount_text})"
        clean_text += "\n\n"

    clean_text += f"🛒 👉 {amazon_link}\n\n📢 @LootNecks"
    return clean_text, amazon_link

@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()
        if getattr(chat, 'title', None)!= SOURCE_NAME:
            return
        if not event.raw_text or "amzn.to" not in event.raw_text and "amazon" not in event.raw_text:
            return

        caption, link = make_clean_caption(event.raw_text)
        if not caption or not link:
            return

        print(f"Posting: {caption[:50]}")
        if event.message.photo or event.message.document:
            file_path = await event.message.download_media()
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
            with open(file_path, 'rb') as f:
                requests.post(url, data={'chat_id': DESTINATION, 'caption': caption}, files={'photo': f}, timeout=30)
            os.remove(file_path)
        else:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            requests.post(url, data={'chat_id': DESTINATION, 'text': caption, 'disable_web_page_preview': True}, timeout=30)

    except Exception as e:
        print("Error:", e)

async def main():
    await client.start()
    print("LootNecks Railway Bot Live!")
    await client.run_until_disconnected()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
