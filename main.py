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

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH
)

def make_clean_caption(original_text):
    if not original_text:
        return ""

    # 1. সব অ্যামাজন লিংক বের করা এবং ট্যাগ যুক্ত করা
    link_match = re.findall(r'https?://[^\s]+', original_text)
    amazon_link = ""
    for l in link_match:
        if "amazon" in l or "amzn" in l:
            amazon_link = l
            break
    
    if not amazon_link and link_match:
        amazon_link = link_match[0]

    # সব লিংকে নিখুঁতভাবে আপনার ট্যাগ বসানো
    if amazon_link:
        if 'tag=' in amazon_link:
            amazon_link = re.sub(r'tag=[^&]+', f'tag={AFFILIATE_TAG}', amazon_link)
        else:
            sep = '&' if '?' in amazon_link else '?'
            amazon_link = f"{amazon_link}{sep}tag={AFFILIATE_TAG}"

    # 2. দাম নিখুঁতভাবে বের করা (বর্তমান দাম এবং আগের MRP দাম)
    prices = re.findall(r'₹\s?([0-9,]+)', original_text)
    sale_price = prices[0] if len(prices) > 0 else ""
    reg_price = prices[1] if len(prices) > 1 else ""

    # 3. ছাড়ের পার্সেন্টেজ (% OFF) বের করা বা হিসাব করা
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

    # 4. আসল প্রোডাক্টের নাম (Title) বের করা ("more" বা ফালতু শব্দ বাদ দিয়ে)
    lines = [line.strip() for line in original_text.split('\n') if line.strip()]
    title = "Loot Deal"
    for line in lines:
        # যে লাইনগুলোতে লিংক, দাম বা 'more' আছে সেগুলোকে বাদ দিয়ে আসল নাম খোঁজা
        if not line.startswith('http') and '₹' not in line and 'more' not in line.lower() and 'apply' not in line.lower() and len(line) > 5:
            title = line.replace('**', '').replace('Loot :', '').replace('Loot', '').strip()
            break
    
    if len(title) > 80:
        title = title[:80]
    if not title:
        title = "Special Loot Deal"

    # 5. চূড়ান্ত সুন্দর ও গোছানো ফরম্যাট
    clean_text = f"🛍️ {title}\n\n"
    clean_text += f"🔥 Deal Price: ₹{sale_price}"
    
    if reg_price:
        clean_text += f" | ❌ MRP: ₹{reg_price}"
        
    if discount_text:
        clean_text += f" ({discount_text})"
        
    clean_text += f"\n\n🛒 👉 {amazon_link}\n\n📢 @LootNecks"

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

            # ছবিসহ পোস্ট পাঠানো যাতে ডাবল লিংক বা বড় প্রিভিউ বক্স ঝামেলা না করে
            if event.message.photo or event.message.document:
                file_path = await event.message.download_media()
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
                with open(file_path, 'rb') as f:
                    files = {'photo': f}
                    data = {'chat_id': DESTINATION, 'caption': clean_caption}
                    response = requests.post(url, data=data, files=files, timeout=30)
                os.remove(file_path)
                print("Photo sent perfectly:", response.text)
            else:
                url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                payload = {
                    "chat_id": DESTINATION,
                    "text": clean_caption,
                    "disable_web_page_preview": True
                }
                response = requests.post(url, data=payload, timeout=30)
                print("Message sent without preview:", response.text)

    except Exception as e:
        print("Error:", e)

async def main():
    print("Connecting...")
    await client.connect()
    if not await client.is_user_authorized():
        print("ERROR: Session not authorized.")
        return
    print("Connected. LootNecks Perfect Bot is Live...")
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
