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
        return ""

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

    # 2. দাম বের করা (বর্তমান দাম এবং আগের দাম)
    prices = re.findall(r'₹\s?([0-9,]+)', original_text)
    sale_price = prices[0] if len(prices) > 0 else ""
    reg_price = prices[1] if len(prices) > 1 else ""

    # 3. ছাড়ের পার্সেন্টেজ (Discount %) বের করা বা হিসাব করা
    discount_match = re.search(r'(\d+%\s*(?:OFF|off|discount))', original_text, re.IGNORECASE)
    discount_text = discount_match.group(1) if discount_match else ""
    
    if not discount_text and sale_price and reg_price:
        try:
            s_val = int(sale_price.replace(',', ''))
            r_val = int(reg_price.replace(',', ''))
            if r_val > s_val:
                discount_pct = int(((r_val - s_val) / r_val) * 100)
                discount_text = f"{discount_pct}% OFF"
        except:
            pass

    # 4. Title বের করা (প্রোডাক্টের নাম)
    lines = [line.strip() for line in original_text.split('\n') if line.strip()]
    title = "Loot Deal"
    for line in lines:
        if not line.startswith('http') and '₹' not in line and '✨' not in line and 'Loot' not in line and not line.startswith('@'):
            title = line.replace('**', '').strip()
            break
    
    if len(title) > 80:
        title = title[:80]

    # 5. আকর্ষণীয় ইমোজি ও ফরম্যাট তৈরি
    clean_text = f"🛍️ {title}\n\n"
    clean_text += f"🔥 Deal Price: ₹{sale_price}"
    
    if reg_price:
        clean_text += f" | ❌ MRP: ₹{reg_price}"
        
    if discount_text:
        clean_text += f" ({discount_text})"
        
    clean_text += f"\n\n🛒 👉 {amazon_link}"

    return clean_text

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

            clean_caption = make_clean_caption(original_text)

            # টেলিগ্রাম Bot API দিয়ে টেক্সট পাঠানো যাতে ছোট প্রিভিউ কার্ড আসে
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": DESTINATION,
                "text": clean_caption,
                "disable_web_page_preview": False
            }
            response = requests.post(url, data=payload, timeout=30)
            print("Message sent with full emojis and pricing:", response.text)

    except Exception as e:
        print("Error:", e)

async def main():
    print("Connecting...")
    await client.connect()
    if not await client.is_user_authorized():
        print("ERROR: Session not authorized.")
        return
    print("Connected. LootNecks Pro Bot is Live...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
