# Polymarket Telegram Bot

Telegram bot that posts high-probability Polymarket market predictions.

## Features
- Auto-posts markets with 60%+ probability
- Health check endpoint for Railway (/health)
- Clean format with links
- 24/7 uptime on Railway free tier

## Files
- `polymarket_telegram_bot.py` - Main bot
- `requirements.txt` - Python dependencies
- `start.sh` - Startup script
- `railway.json` - Railway deployment config

## Deploy to Railway

### Step 1: Push to GitHub
```bash
cd /Users/ankitkhandelwal/clawd/polymarket-bot-deploy
git add .
git commit -m "Deploy bot"
git push origin main
```

### Step 2: Deploy on Railway
1. Go to https://railway.com/new
2. Connect GitHub: `akhbarsingh06-dev/polymarket-bot`
3. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python3 polymarket_telegram_bot.py`
   - Health Check Path: `/health`
   - Health Check Timeout: `600`
   - Plan: Free

### Step 3: Add Environment Variables
In Railway dashboard, add:
```
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL_ID=@your_channel
POLYMARKET_API_KEY=your_api_key
```

### Step 4: Deploy
Click "Deploy Web Service" - bot will be live in 2-3 minutes!

## Telegram Setup
1. Create bot via @BotFather
2. Get bot token
3. Create channel, add bot as admin
4. Get channel ID (@channelname or -100xxxxxxx)

## API Key
Get from: https://gamma.polymarket.com/api

## License
MIT
