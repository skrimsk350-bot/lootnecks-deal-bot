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

def add_affiliate_tag(text, tag):
    if not text:
        return text
    
    # অ্যামাজন লিংক বা শর্ট লিংকগুলো খুঁজে বের করার জন্য রেগুলার এক্সপ্রেশন
    # যেমন: amazon.in, amzn.in ইত্যাদি
    pattern = r'https?://(?:www\.)?(?:amazon\.[a-z\.]+|amzn\.[a-z]{2})/[^\s]+'
    
    def replace_url(match):
        url = match.group(0)
        # যদি লিংকে ইতিমধ্যে ট্যাগ থাকে, তবে সেটিকে এড়িয়ে যাওয়া বা ঠিক করা
        if 'tag=' in url:
            return re.sub(r'tag=[^&]+', f'tag={tag}', url)
        else:
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}tag={tag}"
            
    return re.sub(pattern, replace_url, text)

@client.on(events.NewMessage)
async def handler(event):
    try:
        chat = await event.get_chat()
        chat_title = getattr(chat, 'title', None)
        
        if chat_title == SOURCE_NAME:
            text = event.raw_text
            if not text:
                return
            
            print(f"New message received from {SOURCE_NAME}")
            
            # মেসেজের ভেতরের অ্যামাজন লিংকগুলোতে অ্যাফিলিয়েট ট্যাগ যুক্ত করা
            modified_text = add_affiliate_tag(text, AFFILIATE_TAG)
            
            # টেলিগ্রাম বট এপিআই দিয়ে টার্গেট চ্যানেলে পোস্ট পাঠানো
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            payload = {
                "chat_id": DESTINATION,
                "text": modified_text,
                "disable_web_page_preview": False
            }
            
            response = requests.post(url, data=payload, timeout=30)
            print("Telegram response:", response.text)
            
    except Exception as e:
        print("Error handling new message:", e)

async def main():
    print("Connecting to Telegram...")
    await client.connect()

    if not await client.is_user_authorized():
        print("ERROR: Telegram session is not authorized.")
        return

    print("Connected successfully. Bot is now listening for new posts 24/7 with Affiliate Tag integration...")
    
    await client.run_until_disconnected()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())
