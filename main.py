def make_clean_caption(text):
    if not text: return ""

    # 1. Amazon Link বের করা
    links = re.findall(r'https?://[^\s]+', text)
    amazon_link = ""
    for l in links:
        if "amzn" in l or "amazon" in l:
            amazon_link = l.split('?')[0]
            break
    if not amazon_link and links:
        amazon_link = links[0].split('?')[0]

    # Tag বসানো
    if amazon_link:
        amazon_link = f"{amazon_link}?tag={AFFILIATE_TAG}"

    # 2. দাম বের করা - Genie Loot এর ফরম্যাট অনুযায়ী
    sale_price = ""
    mrp = ""

    # Loot ₹99 | Regular: 199 এই ফরম্যাটটা ধরবে
    m1 = re.search(r'Loot.*?₹\s?(\d+).*?Regular:\s?(\d+)', text, re.I)
    if m1:
        sale_price = m1.group(1)
        mrp = m1.group(2)
    else:
        # শুধু ₹99 থাকলে
        prices = re.findall(r'₹\s?(\d+)', text)
        if len(prices) >= 1:
            sale_price = prices[0]
        if len(prices) >= 2:
            mrp = prices[1]
        # Regular: 199 without ₹
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
                discount = f"{int(((r-s)/r)*100)}% OFF"
        except: pass

    # 4. Title বের করা - আসল প্রোডাক্টের নাম
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    title = "Loot Deal"
    for l in lines:
        # বাজে লাইনগুলো বাদ দাও
        if 'http' in l: continue
        if '₹' in l: continue
        if 'Loot' in l: continue
        if 'more :' in l.lower(): continue
        if 'ambhedeal' in l.lower(): continue
        if '.in.net' in l.lower(): continue
        if len(l) < 10: continue
        # যেটা থাকবে সেটাই আসল নাম
        title = l[:90]

    # 5. Final Format - Genie Loot এর মতো
    caption = f"🛍️ {title}\n\n"
    if sale_price:
        caption += f"🔥 Deal Price: ₹{sale_price}\n"
    if mrp:
        caption += f"❌ MRP: ₹{mrp}\n"
    if discount:
        caption += f"💥 Discount: {discount}\n"
    caption += f"\n🛒 Buy Now 👉 {amazon_link}\n\n✨ @LootNecks"

    return caption
