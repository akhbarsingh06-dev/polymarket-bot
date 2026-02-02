#!/usr/bin/env python3
"""
🤖 Polymarket Telegram Auto-Poster - CLEAN VERSION
"""

import os
import time
import requests
import threading
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ==================== CONFIG ====================
CONFIG_FILE = "bot_data/telegram_config.env"

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    config[k.strip()] = v.strip()
    return config

CONFIG = load_config()
TELEGRAM_TOKEN = CONFIG.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = CONFIG.get("TELEGRAM_CHANNEL_ID", "@polymarketpredictionsAlert")
DATA_API = "https://data-api.polymarket.com"
POST_INTERVAL_MIN = 5
MAX_POSTS_PER_DAY = 30

# ==================== FORMAT ====================
def format_post(market, tier):
    prob = market["top_prob"]
    volume = float(market["volumeNum"])
    question = market["question"].replace("?", "").strip()
    slug = market.get("slug", "")

    # Volume formatting
    if volume >= 1_000_000:
        vol = f"${volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        vol = f"${volume/1_000:.1f}K"
    else:
        vol = f"${int(volume)}"

    # Link
    link = f'<a href="https://polymarket.com/market/{slug}">market</a>' if slug else "market"

    # Emoji
    emoji = "🚨" if tier == "JUST IN" else "🔥"

    return f"{emoji} {tier}: {prob:.0f}% chance: {question} 📊 {vol} | {link} #Polymarket"

# ==================== DATA ====================
def get_fresh_markets():
    try:
        r = requests.get(f"{DATA_API}/trades", params={"limit": 200}, timeout=15)
        trades = r.json()
    except Exception:
        return []

    from collections import defaultdict
    markets = {}
    now = datetime.now()
    from datetime import timedelta
    cutoff = now - timedelta(hours=24)

    for t in trades:
        title = t.get("title", "Unknown")
        slug = t.get("slug", "")
        outcome = t.get("outcome", "")
        size = float(t.get("size", 0))
        ts = t.get("timestamp", 0)

        if title not in markets:
            markets[title] = {"question": title, "slug": slug, "outcomes": defaultdict(int), "total": 0, "last": ts}

        m = markets[title]
        m["outcomes"][outcome] += 1
        m["total"] += size
        m["last"] = max(m["last"], ts)

    fresh = []
    for m in markets.values():
        if datetime.fromtimestamp(m["last"]) < cutoff:
            continue
        total = sum(m["outcomes"].values())
        if total == 0:
            continue
        top_outcome, top_count = max(m["outcomes"].items(), key=lambda x: x[1])
        prob = (top_count / total) * 100
        fresh.append({"question": m["question"], "slug": m["slug"], "volumeNum": str(m["total"]), "top_prob": prob, "last_trade": m["last"]})

    fresh.sort(key=lambda x: x["top_prob"], reverse=True)
    return fresh

# ==================== TELEGRAM ====================
def send_telegram(text):
    if not TELEGRAM_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    r = requests.post(url, json=payload, timeout=15)
    return r.ok

# ==================== HEALTH ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *_):
        pass

def start_health():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    print(f"✅ Health server on {port}")

# ==================== MAIN ====================
def run_monitor():
    print("🚀 POLYMARKET BOT STARTED")
    start_health()
    posted = set()
    today = datetime.now().date()
    count = 0

    while True:
        if datetime.now().date() != today:
            posted.clear()
            count = 0
            today = datetime.now().date()

        if count >= MAX_POSTS_PER_DAY:
            time.sleep(POST_INTERVAL_MIN * 60)
            continue

        markets = get_fresh_markets()
        for m in markets:
            if m["top_prob"] < 60:
                continue
            key = f"{m['slug']}-{m['last_trade']}"
            if key in posted:
                continue
            tier = "JUST IN" if m["top_prob"] >= 90 else "BREAKING"
            post = format_post(m, tier)
            if send_telegram(post):
                posted.add(key)
                count += 1
                print(f"✅ Posted: {m['question'][:50]}")
            break  # one post per cycle

        time.sleep(POST_INTERVAL_MIN * 60)

# ==================== START ====================
if __name__ == "__main__":
    run_monitor()
