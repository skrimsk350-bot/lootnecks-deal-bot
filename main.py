import os, re, threading, asyncio, requests
from flask import Flask
import deal_bot
from telethon import events

MY_TAG = "sahinoorstore-21" # <-- Your Tag Here

app = Flask(__name__)
@app.route('/')
def home(): return "Running"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

def get_affiliate_link(short_url):
    try:
        r = requests.head(short_url, allow_redirects=True, timeout=10)
        long_url = r.url
        m = re.search(r'/dp/([A-Z0-9]{10})', long_url)
        if m:
            return f"https://www.amazon.in/dp/{m.group(1)}?tag={MY_TAG}"
        return long_url.split("?")[0] + f"?tag={MY_TAG}"
    except:
        return short_url

async def run_bot():
    await deal_bot.client.connect()
    print("Clean English Bot Started")

    @deal_bot.client.on(events.NewMessage(chats=deal_bot.SOURCE_NAME))
    async def handler(event):
        msg = event.message
        text = msg.message or ""
        webpage = msg.media.webpage if msg.media and hasattr(msg.media, 'webpage') else None

        # Price
        m = re.search(r'₹\s*(\d+).*?(\d+)', text)
        offer = m.group(1) if m else ""
        regular = m.group(2) if m and len(m.groups())>1 else ""

        # Link
        s = re.search(r'https://amzn\.to/\w+', text)
        my_link = get_affiliate_link(s.group(0)) if s else ""

        # Product Name (English)
        title = webpage.title if webpage and hasattr(webpage, 'title') else "Amazon Product"
        title = title[:80] # small title

        # Discount
        try: off = int((1-int(offer)/int(regular))*100)
        except: off = 0

        caption = f"""{title}

💰 Price: ₹{offer} | Regular: ₹{regular}
🔥 {off}% OFF - Limited Deal!

👉 {my_link}
"""

        if msg.media and (msg.photo or hasattr(msg.media, 'photo')):
            await deal_bot.client.send_file(deal_bot.DESTINATION, file=msg.media, caption=caption)
        else:
            await deal_bot.client.send_message(deal_bot.DESTINATION, caption, link_preview=True)

    await deal_bot.client.run_until_disconnected()

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    asyncio.run(run_bot())
