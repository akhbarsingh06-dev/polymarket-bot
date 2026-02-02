#!/usr/bin/env python3
"""
🤖 Polymarket Telegram Auto-Poster - FINAL CLEAN VERSION
======================================================
NO prefixes, NO duplicates, CLEAR format, HYPERLINKS

Format:
🚨 JUST IN: 77% chance: Ethereum ABOVE $2K on 2026-02-01
📊 $346 | 📁 Eth | market

🔥 BREAKING: 83% chance: West Ham WIN on 2026-02-01  
📊 $889 | 📁 EPL | market
"""

import os
import sys
import time
import requests
from datetime import datetime, timedelta
from collections import defaultdict

# ==================== CONFIG ====================
CONFIG_FILE = "bot_data/telegram_config.env"

def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    return config

CONFIG = load_config()
TELEGRAM_TOKEN = CONFIG.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHANNEL_ID = CONFIG.get('TELEGRAM_CHANNEL_ID', '@polymarketpredictionsAlert')
DATA_API = CONFIG.get('DATA_API', 'https://data-api.polymarket.com')
POST_INTERVAL = 5
MAX_POSTS_PER_DAY = 30

# ==================== FORMAT FUNCTION (CLEAN!) ====================
def format_post(market, tier):
    """Generate CLEAN post - NO PREFIX, PROBABILITY FIRST"""
    prob = market['top_prob']
    volume = float(market['volumeNum'])
    category = market['category']
    q = market['question']
    outcome = market['top_outcome']
    slug = market.get('slug', '')
    
    # Clean question
    q_clean = q.replace('?', '').strip()
    
    # Extract date
    date_str = ""
    if ' on ' in q_clean.lower():
        date_part = q_clean.lower().split(' on ')[-1].split()[0]
        date_str = f" on {date_part}"
    
    # Extract subject
    if 'will ' in q_clean.lower():
        subject = q_clean.lower().split('will ')[-1].replace(date_str, '').strip('?')
    else:
        subject = q_clean[:40]
    
    # Determine condition (ABOVE/UNDER/WIN/LOSE)
    q_lower = q.lower()
    if 'above' in q_lower:
        condition = "ABOVE"
        target = q_lower.split('above')[-1].strip().split()[0]
        subject = f"{subject} {target}"
    elif 'below' in q_lower:
        condition = "UNDER"
        target = q_lower.split('below')[-1].strip().split()[0]
        subject = f"{subject} {target}"
    elif 'win' in q_lower or outcome.lower() in ['yes', 'team a', team_a.lower()] if ' vs ' in q else False:
        condition = "WIN"
    elif 'lose' in q_lower or outcome.lower() in ['no', 'team b', team_b.lower()] if ' vs ' in q else False:
        condition = "LOSE"
    elif outcome.lower() in ['up', 'yes', 'rise']:
        condition = "ABOVE"
    elif outcome.lower() in ['down', 'no', 'fall']:
        condition = "UNDER"
    else:
        condition = outcome.upper()
    
    # Clean subject
    subject = subject.replace('will ', '').replace('the ', '').strip('?').strip()
    
    # Volume format
    if volume >= 1000000:
        vol_str = f"${volume/1000000:.1f}M"
    elif volume >= 1000:
        vol_str = f"${volume/1000:.1f}K"
    else:
        vol_str = f"${volume:.0f}"
    
    # Link
    link = f'<a href="https://polymarket.com/market/{slug}">market</a>' if slug else "market"
    
    # Generate based on tier
    if tier == "JUST IN":
        return f"""🚨 JUST IN: {prob:.0f}% chance: {subject}{date_str}

📊 {vol_str} | 📁 {category} | {link}

#Polymarket #Trading"""
    
    elif tier == "BREAKING":
        return f"""🔥 BREAKING: {prob:.0f}% chance: {subject}{date_str}

📊 {vol_str} | 📁 {category} | {link}

#Polymarket #Breaking"""
    
    else:  # WATCH
        return f"""⚠️ WATCH: {prob:.0f}% chance: {subject}{date_str}

📊 {vol_str} | 📁 {category} | {link}

#Polymarket #Alert"""

# ==================== DATA FETCH ====================
def get_fresh_markets():
    try:
        r = requests.get(f"{DATA_API}/trades", params={"limit": 200}, timeout=15)
        if r.status_code != 200:
            return []
        trades = r.json()
        if not trades:
            return []
        
        markets = {}
        now = datetime.now()
        
        for t in trades:
            title = t.get('title', 'Unknown')
            slug = t.get('slug', '')
            event_slug = t.get('eventSlug', '')
            outcome = t.get('outcome', 'Unknown')
            size = float(t.get('size', 0))
            timestamp = t.get('timestamp', 0)
            
            if title not in markets:
                markets[title] = {
                    'question': title, 'slug': slug, 'eventSlug': event_slug,
                    'category': event_slug.split('-')[0].title() if event_slug else 'General',
                    'trades': 0, 'outcomes': defaultdict(float), 'total_size': 0,
                    'last_trade': 0
                }
            
            m = markets[title]
            m['trades'] += 1
            m['outcomes'][outcome] += 1
            m['total_size'] += size
            if timestamp > m['last_trade']:
                m['last_trade'] = timestamp
        
        fresh = []
        recent_cutoff = now - timedelta(hours=24)
        
        for title, data in markets.items():
            last_trade = datetime.fromtimestamp(data['last_trade'])
            if last_trade >= recent_cutoff:
                total = sum(data['outcomes'].values())
                if total > 0:
                    sorted_outcomes = sorted(data['outcomes'].items(), key=lambda x: x[1], reverse=True)
                    top_outcome = sorted_outcomes[0][0]
                    top_count = sorted_outcomes[0][1]
                    prob = (top_count / total) * 100
                    
                    fresh.append({
                        'question': data['question'],
                        'slug': data['slug'],
                        'category': data['category'],
                        'volumeNum': str(data['total_size']),
                        'trades_count': data['trades'],
                        'outcomes': dict(data['outcomes']),
                        'top_outcome': top_outcome,
                        'top_prob': prob,
                        'last_trade': data['last_trade']
                    })
        
        fresh.sort(key=lambda x: x['trades_count'], reverse=True)
        return fresh
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

# ==================== TELEGRAM ====================
def send_telegram(text):
    if not TELEGRAM_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHANNEL_ID, "text": text, "parse_mode": "HTML"}, timeout=15)
        return r.json().get('ok', False)
    except:
        return False

# ==================== MAIN ====================
def run_monitor():
    print("\n" + "="*60)
    print("🚀 POLYMARKET TELEGRAM BOT (FINAL CLEAN)")
    print("="*60)
    print(f"📺 Channel: {TELEGRAM_CHANNEL_ID}")
    print("📝 NO PREFIX | CLEAN FORMAT | HYPERLINKS")
    print("="*60 + "\n")
    
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
                time.sleep(POST_INTERVAL * 60)
                continue
            
            print(f"\n🔍 [{datetime.now().strftime('%H:%M')}] Checking...")
            markets = get_fresh_markets()
            
            if not markets:
                print("   No activity")
                time.sleep(POST_INTERVAL * 60)
                continue
            
            print("   " + str(len(markets)) + " markets found")
            
            just_in = [m for m in markets if m['top_prob'] >= 90]
            breaking = [m for m in markets if 60 <= m['top_prob'] < 90]
            
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
            time.sleep(POST_INTERVAL * 60)
            
        except KeyboardInterrupt:
            print("\n👋 Stopped")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_monitor()
