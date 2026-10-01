import os
import re
import requests
from PIL import Image
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

def parse_number(s):
    s = s.lower().replace(',', '').replace('₹','').strip()
    try:
        if 'k' in s:
            return float(s.replace('k','')) * 1000
        return float(s)
    except:
        return 0

def make_clean_caption(original_text):
    if not original_text:
        return "", ""

    links = re.findall(r'https?://[^\s]+', original_text)
    main_link = ""
    more_link = ""
    for l in links:
        if "amzn" in l or "amazon" in l:
            if not main_link: main_link = l.strip()
            else: more_link = l.strip()

    def add_tag(link):
        if not link: return ""
        if 'tag=' in link:
            return re.sub(r'tag=[^&\s]+', f'tag={AFFILIATE_TAG}', link)
        sep = '&' if '?' in link else '?'
        return f"{link}{sep}tag={AFFILIATE_TAG}"

    main_link = add_tag(main_link)
    more_link = add_tag(more_link)

    # দাম বের করা
    sale_str = ""; regular_str = ""
    m = re.search(r'₹\s?([0-9,]+)\s*\|\s*Regular:\s*([0-9,.k]+)', original_text, re.I)
    if m:
        sale_str = m.group(1).strip()
        regular_str = m.group(2).strip()
    else:
        m2 = re.search(r'Lowest Price\s*:\s*₹\s?([0-9,]+)', original_text, re.I)
        if m2: sale_str = m2.group(1).strip()

    # % OFF হিসাব
    off_text = ""
    if sale_str and regular_str:
        s_val = parse_number(sale_str)
        r_val = parse_number(regular_str)
        if s_val > 0 and r_val > s_val:
            off = int(((r_val - s_val) / r_val) * 100)
            off_text = f"🔥 {off}% OFF"

    # Title
    lines = [l.strip() for l in original_text.split('\n') if l.strip()]
    title = "Loot Deal"
    for l in lines:
        if not l.startswith('http') and '₹' not in l and 'Regular' not in l and 'Loot' not in l and 'Jaldi' not in l and '@' not in l and len(l) > 10:
            title = l.replace('**','').strip()
            break
    if len(title) > 70: title = title[:70]

    # Final Caption - বেশি হাবিজাবি না, শুধু দরকারি টা
    if regular_str:
        price_line = f"💰 Loot: ₹{sale_str} | MRP: ₹{regular_str}"
    else:
        price_line = f"💰 Price: ₹{sale_str}"

    caption = f"🛍️ {title}\n\n{price_line}"
    if off_text:
        caption += f"\n{off_text}"
    caption += f"\n\n🛒 👉 {main_link}"
    if more_link:
        caption += f"\n\n👜 more : {more_link}"

    return caption, main_link

@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', None)
        if chat_title == SOURCE_NAME:
            if not event.raw_text or "amzn" not in event.raw_text.lower(): return

            clean_caption, _ = make_clean_caption(event.raw_text)

            if event.message.photo or event.message.document:
                file_path = await event.message.download_media()
                # ছবি ছোট করা - 400px
                try:
                    with Image.open(file_path) as img:
                        img.thumbnail((400, 400))
                        img.save(file_path)
                except: pass

                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                with open(file_path, 'rb') as f:
                    requests.post(url, data={"chat_id": DESTINATION, "caption": clean_caption}, files={"photo": f}, timeout=30)
                os.remove(file_path)
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                requests.post(url, data={"chat_id": DESTINATION, "text": clean_caption, "disable_web_page_preview": True}, timeout=30)

    except Exception as e:
        print("Error:", e)

async def main():
    print("Bot LIVE - Small Image + Emoji Mode...")
    await client.connect()
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
