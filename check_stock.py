import os
import re
import sys
import json
import urllib.request
import urllib.parse

URL = "https://www.hunterboots.com.tr/p-downpour-wellington-unisex-siyah-uzun-bot-hfru0001251-blk"
GTIN = "5063447330630"  # Downpour Siyah - 37 numara
SIZE_LABEL = "37"

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
TEST_MODE = os.environ.get("TEST_MODE") == "true"


def send_telegram(text: str) -> None:
    data = urllib.parse.urlencode({"chat_id": CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data=data)
    with urllib.request.urlopen(req, timeout=20) as r:
        r.read()


def get_stock():
    req = urllib.request.Request(URL, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
        "Accept-Language": "tr-TR,tr;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", errors="ignore")

    # Next.js veriyi kaçışlı (\") JSON olarak gömüyor; ters bölüleri temizle
    clean = html.replace("\\", "")
    m = re.search(rf'"gtin":"{GTIN}","inStock":(true|false),"stock":(-?\d+)', clean)
    if not m:
        return None
    return m.group(1) == "true", int(m.group(2))


def main():
    result = get_stock()

    if result is None:
        msg = f"⚠️ Hunter stok kontrolü: {SIZE_LABEL} numara verisi sayfada bulunamadı. Site yapısı değişmiş olabilir.\n{URL}"
        print(msg)
        send_telegram(msg)
        sys.exit(1)

    in_stock, qty = result
    print(f"inStock={in_stock} stock={qty}")

    if TEST_MODE:
        send_telegram(f"✅ Test mesajı — bot çalışıyor. Şu an {SIZE_LABEL} numara: "
                      f"{'stokta' if in_stock else 'stokta yok'} (adet: {qty})")
        return

    if in_stock and qty > 0:
        send_telegram(f"🎉 Hunter Downpour Siyah {SIZE_LABEL} numara STOKTA! (adet: {qty})\n{URL}")
        # Workflow'a "bildirim gönderildi" sinyali ver
        with open(os.environ.get("GITHUB_OUTPUT", os.devnull), "a") as f:
            f.write("notified=true\n")


if __name__ == "__main__":
    main()
