import os
import re
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
SESSION = os.environ["TELEGRAM_SESSION"]
AFFILIATE_TAG = os.environ.get("AFFILIATE_TAG", "lootnecks-21")

DESTINATION = "@LootNecks"
# এখানে শুধু যেখান থেকে নিতে চাও সেটার নাম দাও
ALLOWED_SOURCES = ["GenieLootDeals", "GenieLoot", "genieloot", "genie_loot_deals"]

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

def make_clean_caption(text):
    if not text: return ""
    links = re.findall(r'https?://[^\s]+', text)
    amazon_link = ""
    for l in links:
        if "amzn" in l or "amazon" in l:
            amazon_link = l.split('?')[0]
            break
    if not amazon_link and links:
        amazon_link = links[0].split('?')[0]
    if amazon_link:
        amazon_link = f"{amazon_link}?tag={AFFILIATE_TAG}"

    sale_price = ""
    mrp = ""
    m1 = re.search(r'Loot.*?₹\s?([\d,]+).*?Regular:\s?([\d,.kK]+)', text, re.I)
    if m1:
        sale_price = m1.group(1)
        mrp = m1.group(2)
    else:
        prices = re.findall(r'₹\s?([\d,]+)', text)
        if len(prices) >= 1: sale_price = prices[0]
        m2 = re.search(r'Regular:\s?([\d,.kK]+)', text, re.I)
        if m2: mrp = m2.group(1)

    discount = ""
    m = re.search(r'(\d+)%\s*off', text, re.I)
    if m: discount = f"{m.group(1)}% OFF"
    elif sale_price and mrp:
        try:
            s = int(sale_price.replace(',','').replace('.',''))
            r_str = mrp.lower().replace(',','').replace('k','000')
            r = int(float(r_str)) if '.' in r_str else int(r_str)
            if r > s: discount = f"{int((r-s)/r*100)}% OFF"
        except: pass

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    title = "Loot Deal"
    for l in lines:
        if 'http' in l.lower(): continue
        if '₹' in l: continue
        if 'Loot' in l: continue
        if 'Jaldi' in l: continue
        if 'Fast' in l: continue
        if 'BIGGEST LOOT' in l: continue
        if 'more :' in l.lower(): continue
        if 'ambhedeal' in l.lower(): continue
        if len(l) < 8: continue
        title = l[:90]
        break

    caption = f"🛍️ {title}\n\n"
    if sale_price: caption += f"🔥 Deal Price: ₹{sale_price}\n"
    if mrp: caption += f"❌ MRP: ₹{mrp}\n"
    if discount: caption += f"💥 Discount: {discount}\n"
    caption += f"\n🛒 Buy Now 👉 {amazon_link}\n\n✨ @LootNecks"
    return caption

@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()
        username = getattr(chat, 'username', '') or ''
        # 1. শুধু Genie Loot থেকে নেবে, অন্য Channel থেকে নেবে না
        # 2. নিজের Channel এর মেসেজ Ignore করবে
        if username.lower() == "lootnecks": return
        if username.lower() not in [s.lower() for s in ALLOWED_SOURCES]:
            # যদি ID দিয়ে check করতে হয়
            if str(event.chat_id) not in ALLOWED_SOURCES:
                # Genie Loot এর নামে Title এ "Genie" থাকলে নেবে
                if "genie" not in getattr(chat, 'title', '').lower():
                    return

        text = event.message.message
        if not text: return
        if "amazon" not in text.lower() and "amzn" not in text.lower() and "₹" not in text:
            return

        final_caption = make_clean_caption(text)
        if event.message.photo or event.message.document:
            await client.send_file(DESTINATION, event.message.media, caption=final_caption)
        else:
            await client.send_message(DESTINATION, final_caption)

        print(f"Posted from {username}: {final_caption[:60]}")
    except Exception as e:
        print(f"Error: {e}")

print("Bot Started with Source Filter...")
client.start()
client.run_until_disconnected()
