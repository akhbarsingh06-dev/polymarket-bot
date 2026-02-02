#!/usr/bin/env python3
"""
🤖 Polymarket Telegram Auto-Poster - FIXED FINAL VERSION
======================================================
CLEAN • NO DUPLICATES • NO CRASHES • HEALTH CHECK ENABLED
"""

import os
import time
import requests
import threading
from datetime import datetime, timedelta
from collections import defaultdict
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
    category = market["category"]
    question = market["question"].replace("?", "").strip()
    slug = market.get("slug", "")

    # Date extraction
    date_str = ""
    if " on " in question.lower():
        date_part = question.lower().split(" on ")[-1]
        date_str = f" on {date_part}"

    subject = question.split(" on ")[0]
    subject = subject.replace("will ", "").replace("the ", "").strip()

    ql = question.lower()
    if "above" in ql:
        condition = "ABOVE"
    elif "below" in ql:
        condition = "UNDER"
    elif "win" in ql:
        condition = "WIN"
    else:
        condition = ""

    subject = f"{subject} {condition}".strip()

    # Volume formatting
    if volume >= 1_000_000:
        vol = f"${volume/1_000_000:.1f}M"
    elif volume >= 1_000:
        vol = f"${volume/1_000:.1f}K"
    else:
        vol = f"${int(volume)}"

    # Link
    link = f'<a href="https://polymarket.com/market/{slug}">market</a>' if slug else "market"

    # Emoji and tag
    emoji = "🚨" if tier == "JUST IN" else "🔥"
    tag = "#Polymarket #Alert"

    return (
        f"{emoji} {tier}: {prob:.0f}% chance: {subject}{date_str} "
        f"📊 {vol} | 📁 {category} | {link} {tag}"
    )

# ==================== SEND ====================
def send_telegram(text):
    if not TELEGRAM_TOKEN:
        print(f"   ❌ ERROR: TELEGRAM_TOKEN not set!")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHANNEL_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
        if r.json().get('ok', False):
            print(f"   ✅ Telegram post successful!")
            return True
        else:
            print(f"   ❌ Telegram API error: {r.json().get('description', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"   ❌ Telegram send failed: {str(e)}")
        return False

# ==================== DATA ====================
def get_fresh_markets():
    try:
        r = requests.get(f"{DATA_API}/trades", params={"limit": 200}, timeout=15)
        trades = r.json()
    except Exception:
        return []

    markets = {}
    now = datetime.now()
    cutoff = now - timedelta(hours=24)

    for t in trades:
        title = t.get("title", "Unknown")
        slug = t.get("slug", "")
        outcome = t.get("outcome", "")
        size = float(t.get("size", 0))
        ts = t.get("timestamp", 0)

        if title not in markets:
            markets[title] = {
                "question": title,
                "slug": slug,
                "category": "General",
                "outcomes": defaultdict(int),
                "total": 0,
                "last": ts,
            }

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

        fresh.append({
            "question": m["question"],
            "slug": m["slug"],
            "category": m["category"],
            "volumeNum": str(m["total"]),
            "top_prob": prob,
            "last_trade": m["last"],
        })

    fresh.sort(key=lambda x: x["top_prob"], reverse=True)
    return fresh

# ==================== HEALTH CHECK ====================
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        pass

def start_health_server(port=None):
    port = int(os.environ.get('PORT', port or 8080))
    server = HTTPServer(('0.0.0.0', port), HealthHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"✅ Health check server running on port {port}")
    return server

# ==================== MAIN ====================
def run_monitor():
    print("\n" + "="*60)
    print("🚀 POLYMARKET TELEGRAM BOT (FIXED)")
    print("="*60)
    print(f"📺 Channel: {TELEGRAM_CHANNEL_ID}")
    print("="*60 + "\n")
    
    # Start health check server
    try:
        start_health_server()
    except Exception as e:
        print(f"⚠️ Health server failed: {e}")
    
    posted = set()
    posts_today = 0
    day_start = datetime.now().date()
    
    while True:
        try:
            if datetime.now().date() != day_start:
                posted.clear()
                posts_today = 0
                day_start = datetime.now().date()
            
            if posts_today >= MAX_POSTS_PER_DAY:
                time.sleep(POST_INTERVAL_MIN * 60)
                continue
            
            print(f"\n🔍 [{datetime.now().strftime('%H:%M')}] Checking...")
            markets = get_fresh_markets()
            
            if not markets:
                print("   No activity")
                time.sleep(POST_INTERVAL_MIN * 60)
                continue
            
            print(f"   {len(markets)} markets found")
            
            # Probability breakdown
            high_prob = [m for m in markets if m['top_prob'] >= 90]
            med_prob = [m for m in markets if 60 <= m['top_prob'] < 90]
            low_prob = [m for m in markets if 50 <= m['top_prob'] < 60]
            print(f"   📊 90%+: {len(high_prob)}, 60-90%: {len(med_prob)}, 50-60%: {len(low_prob)}")
            
            just_in = high_prob
            breaking = med_prob
            
            if not just_in and not breaking:
                print(f"   ⚠️ No markets meet posting criteria")
            
            for m in just_in[:1]:
                key = m['question'][:30]
                if key not in posted:
                    post = format_post(m, "JUST IN")
                    if send_telegram(post):
                        posted.add(key)
                        posts_today += 1
                        print(f"   ✅ JUST IN: {m['question'][:40]}...")
            
            for m in breaking[:1]:
                key = m['question'][:30]
                if key not in posted:
                    post = format_post(m, "BREAKING")
                    if send_telegram(post):
                        posted.add(key)
                        posts_today += 1
                        print(f"   ✅ BREAKING: {m['question'][:40]}...")
            
            print(f"   📊 Today: {posts_today}/{MAX_POSTS_PER_DAY}")
            time.sleep(POST_INTERVAL_MIN * 60)
            
        except KeyboardInterrupt:
            print("\n👋 Stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_monitor()
