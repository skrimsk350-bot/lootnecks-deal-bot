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

def make_final_caption(text, preview_title="", preview_desc=""):
    # Link
    links = re.findall(r'https?://[^\s]+', text)
    amazon_link = ""
    for l in links:
        if "amzn" in l.lower() or "amazon" in l.lower():
            amazon_link = l.split('?')[0].split('&')[0]
            break
    if not amazon_link:
        return None
    final_link = f"{amazon_link}?tag={AFFILIATE_TAG}"

    # Price
    sale_price = ""
    mrp = ""
    # 1. Fast ₹1,200 | Regular: 2k
    m1 = re.search(r'₹\s*([\d,.\s]+(?:lac|lakh|k)?)\s*\|\s*Regular:\s*([\d,.\s]+k?)', text, re.I)
    if m1:
        sale_price = m1.group(1).strip()
        mrp = m1.group(2).strip()
    else:
        # 2. Lowest Price : ₹118
        m_low = re.search(r'Lowest Price\s*:\s*₹\s*([\d,]+)', text, re.I)
        if m_low:
            sale_price = m_low.group(1).strip()
        else:
            # 3. Just ₹351
            all_p = re.findall(r'₹\s*([\d,]+)', text)
            if all_p:
                sale_price = all_p[0]
                if len(all_p) > 1:
                    mrp = all_p[1]

    # Regular price separate search
    if not mrp:
        m_reg = re.search(r'Regular:\s*([\d,.\s]+k?)', text, re.I)
        if m_reg:
            mrp = m_reg.group(1).strip()

    # Discount
    discount = ""
    try:
        s_num = float(re.search(r'[\d.]+', sale_price.replace(',','')).group()) if sale_price else 0
        r_num = float(re.search(r'[\d.]+', mrp.replace(',','')).group()) if mrp else 0
        if 'lac' in sale_price.lower(): s_num *= 100000
        if 'k' in mrp.lower() and r_num < 1000: r_num *= 1000
        if 'k' in sale_price.lower() and s_num < 1000: s_num *= 1000
        if r_num > s_num and r_num > 0:
            discount = f"{int((r_num - s_num) / r_num * 100)}% OFF"
    except:
        pass

    # Title Fix - Main Change
    title = ""
    # preview_desc এ থাকে "Parachute Advansed Shampoo 1.2L"
    if preview_desc and len(preview_desc) > 3:
        title = preview_desc
    elif preview_title and "ambhedeal" not in preview_title.lower() and len(preview_title) > 3:
        title = preview_title

    # Fallback: ambhedeal.in.net লাইনের পরের লাইন
    if not title:
        m = re.search(r'ambhedeal\.in\.net\s*\n(.+)', text, re.I)
        if m:
            title = m.group(1).strip()

    if not title:
        title = "Special Loot Deal"

    title = title[:90].strip()

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
        t = getattr(chat, 'title', '') or ''
        if username.lower() == "lootnecks": return
        if "genie" not in t.lower() and username.lower() not in [s.lower() for s in ALLOWED_SOURCES]:
            return

        text = event.message.message or ""
        if "amzn" not in text.lower() and "amazon" not in text.lower():
            return

        preview_title = ""
        preview_desc = ""
        try:
            if event.message.media and hasattr(event.message.media, 'webpage') and event.message.media.webpage:
                wp = event.message.media.webpage
                preview_title = wp.title or ""
                preview_desc = wp.description or ""
        except:
            pass

        final_caption = make_final_caption(text, preview_title, preview_desc)
        if not final_caption:
            return

        if event.message.photo or event.message.document:
            await client.send_file(DESTINATION, event.message.media, caption=final_caption)
        else:
            await client.send_message(DESTINATION, final_caption, link_preview=False)

        print(f"Posted: {final_caption[:70]}")
    except Exception as e:
        print(f"Error: {e}")

print("Bot Started - Title Fixed")
client.start()
client.run_until_disconnected()
