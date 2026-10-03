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

    # 1. Amazon Link
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

    # 2. দাম - Genie Loot ফরম্যাট
    sale_price = ""
    mrp = ""

    m1 = re.search(r'Loot.*?₹\s?(\d+).*?Regular:\s?(\d+)', text, re.I)
    if m1:
        sale_price = m1.group(1)
        mrp = m1.group(2)
    else:
        prices = re.findall(r'₹\s?(\d+)', text)
        if len(prices) >= 1:
            sale_price = prices[0]
        if len(prices) >= 2:
            mrp = prices[1]
        if not mrp:
            m2 = re.search(r'Regular:\s?(\d+)', text, re.I)
            if m2:
                mrp = m2.group(1)

    # 3. Discount %
    discount = ""
    m = re.search(r'(\d+)%\s*off', text, re.I)
    if m:
        discount = f"{m.group(1)}% OFF"
    elif sale_price and mrp:
        try:
            s = int(sale_price.replace(',',''))
            r = int(mrp.replace(',',''))
            if r > s:
                discount = f"{int((r-s)/r*100)}% OFF"
        except: pass

    # 4. Title - আসল নাম
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    title = "Loot Deal"
    for l in lines:
        if 'http' in l: continue
        if '₹' in l: continue
        if 'Loot' in l: continue
        if 'more :' in l.lower(): continue
        if 'ambhedeal' in l.lower(): continue
        if '.in.net' in l.lower(): continue
        if len(l) < 10: continue
        title = l[:90]

    # 5. Final Format
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
        # তোমার Source Channel / Bot থেকে মেসেজ এলেই কাজ করবে
        text = event.message.message
        if not text:
            return

        if "amazon" not in text.lower() and "amzn" not in text.lower() and "₹" not in text:
            return

        final_caption = make_clean_caption(text)

        # যদি ছবি থাকে তাহলে ছবি সহ পাঠাবে
        if event.message.photo or event.message.document:
            await client.send_file(DESTINATION, event.message.media, caption=final_caption)
        else:
            await client.send_message(DESTINATION, final_caption)

        print(f"Posted: {final_caption[:50]}")

    except Exception as e:
        print(f"Error: {e}")

print("Bot Started...")
client.start()
client.run_until_disconnected()
