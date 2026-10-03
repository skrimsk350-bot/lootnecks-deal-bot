import os
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION"]
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "lootnecks-21")

DESTINATION = "@LootNecks"
ALLOWED_SOURCES = ["GenieLootDeals", "GenieLoot", "genieloot"]

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

def make_final_caption(text, preview_title=""):
    links = re.findall(r'https?://[^\s]+', text)
    amazon_link = ""
    for l in links:
        if "amzn" in l.lower() or "amazon" in l.lower():
            amazon_link = l.split('?')[0].split('&')[0]
            break

    if not amazon_link:
        return None

    final_link = f"{amazon_link}?tag={AFFILIATE_TAG}"

    sale_price = ""
    mrp = ""
    # Fast ₹6,372 | Regular: 12k
    m1 = re.search(r'₹\s*([\d,.\s]+(?:lac|lakh|k)?)\s*\|\s*Regular:\s*([\d,.\s]+k?)', text, re.I)
    if m1:
        sale_price = m1.group(1).strip()
        mrp = m1.group(2).strip()
    else:
        m2 = re.search(r'₹\s*([\d,.\s]+(?:lac|lakh))', text, re.I)
        if m2:
            sale_price = m2.group(1).strip()
        else:
            m3 = re.findall(r'₹\s*([\d,]+)', text)
            if m3:
                sale_price = m3[0]
        m4 = re.search(r'Regular:\s*([\d,.\s]+k?)', text, re.I)
        if m4:
            mrp = m4.group(1).strip()

    discount = ""
    try:
        s_str = re.search(r'[\d,.]+', sale_price)
        r_str = re.search(r'[\d,.]+', mrp)
        if s_str and r_str:
            s_val = float(s_str.group().replace(',',''))
            r_val = float(r_str.group().replace(',',''))
            if 'lac' in sale_price.lower(): s_val *= 100000
            if 'k' in mrp.lower() and r_val < 1000: r_val *= 1000
            if 'k' in sale_price.lower() and s_val < 1000: s_val *= 1000
            if r_val > s_val and r_val > 0:
                discount = f"{int((r_val - s_val) / r_val * 100)}% OFF"
    except:
        pass

    title = preview_title
    if not title:
        m_title = re.search(r'ambhedeal\.in\.net\s*\n(.+)', text, re.I)
        if m_title:
            title = m_title.group(1).strip()
    if not title:
        title = "Special Loot Deal"

    caption = f"🛍️ {title}\n\n"
    if mrp:
        caption += f"💰 MRP: ₹{mrp}\n"
    if sale_price:
        caption += f"🔥 Deal Price: ₹{sale_price}\n"
    if discount:
        caption += f"💥 Discount: {discount} 🎉\n"
    caption += f"\n🛒 Buy Now 👉 {final_link}\n\n✨ @LootNecks | 🎁 Best Loot"

    return caption

@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()
        username = getattr(chat, 'username', '') or ''
        title = getattr(chat, 'title', '') or ''

        if username.lower() == "lootnecks": return
        if "genie" not in title.lower() and username.lower() not in [s.lower() for s in ALLOWED_SOURCES]:
            return

        text = event.message.message or ""
        if "amzn" not in text.lower() and "amazon" not in text.lower():
            return

        preview_title = ""
        try:
            if event.message.media and hasattr(event.message.media, 'webpage') and event.message.media.webpage:
                preview_title = event.message.media.webpage.title or ""
        except:
            pass
        if not preview_title:
            m = re.search(r'ambhedeal\.in\.net\s*\n(.+)', text, re.I)
            if m:
                preview_title = m.group(1).strip()

        final_caption = make_final_caption(text, preview_title)
        if not final_caption:
            return

        # এখানেই আসল ফিক্স: ছবিতে link_preview=False দেবে না
        if event.message.photo or event.message.document:
            await client.send_file(DESTINATION, event.message.media, caption=final_caption)
        else:
            await client.send_message(DESTINATION, final_caption, link_preview=False)

        print(f"Posted: {final_caption[:60]}")

    except Exception as e:
        print(f"Error: {e}")

print("LootNecks Final Bot Started - No Big Preview")
client.start()
client.run_until_disconnected()
