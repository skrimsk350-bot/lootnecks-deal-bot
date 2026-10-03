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
    if not text:
        return ""

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

    # 2. দাম - Comma সহ
    sale_price = ""
    mrp = ""

    # Loot ₹6,119 | Regular: 341 বা Jaldi ₹6,119
    m1 = re.search(r'Loot.*?₹\s?([\d,]+).*?Regular:\s?([\d,.kK]+)', text, re.I)
    if m1:
        sale_price = m1.group(1)
        mrp = m1.group(2)
    else:
        # শুধু ₹6,119 খুঁজবে
        prices = re.findall(r'₹\s?([\d,]+)', text)
        if len(prices) >= 1:
            sale_price = prices[0]

        m2 = re.search(r'Regular:\s?([\d,.kK]+)', text, re.I)
        if m2:
            mrp = m2.group(1)

    # 3. Discount %
    discount = ""
    m = re.search(r'(\d+)%\s*off', text, re.I)
    if m:
        discount = f"{m.group(1)}% OFF"
    elif sale_price and mrp:
        try:
            s = int(sale_price.replace(',','').replace('.',''))
            r_str = mrp.lower().replace(',','').replace('k','000')
            # 21.5k -> 21500 handle
            if '.' in r_str:
                 r = int(float(r_str))
            else:
                 r = int(r_str)
            if r > s:
                discount = f"{int((r-s)/r*100)}% OFF"
        except:
            pass

    # 4. Title - বাজে লাইন বাদ দিয়ে
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    title = "Loot Deal"
    for l in lines:
        if 'http' in l.lower(): continue
        if '₹' in l: continue
        if 'Loot' in l: continue
        if 'Jaldi' in l: continue
        if 'Fast' in l: continue
        if 'more :' in l.lower(): continue
        if 'ambhedeal' in l.lower(): continue
        if '.in.net' in l.lower(): continue
        if len(l) < 8: continue
        title = l[:90]
        break

    # যদি Title না পাওয়া যায়, তাহলে Amazon Link Preview থেকে নেওয়ার চেষ্টা করবে Bot
    # কিন্তু Caption এ আমরা Title টা পরিষ্কার রাখছি

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
        text = event.message.message
        if not text:
            return

        if "amazon" not in text.lower() and "amzn" not in text.lower() and "₹" not in text:
            return

        final_caption = make_clean_caption(text)

        if event.message.photo or event.message.document:
            await client.send_file(DESTINATION, event.message.media, caption=final_caption)
        else:
            await client.send_message(DESTINATION, final_caption)

        print(f"Posted: {final_caption[:60]}")

    except Exception as e:
        print(f"Error: {e}")

print("Bot Started...")
client.start()
client.run_until_disconnected()
