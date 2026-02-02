# Polymarket Telegram Bot

Telegram bot that posts high-probability Polymarket market predictions to your channel.

## Features
- Auto-scans Polymarket markets for high-probability predictions (60%+)
- Posts when probability reaches threshold
- Clear format showing both outcomes
- Supports crypto, sports, politics markets
- 24/7 uptime on Render.com free tier

## Files
- `polymarket_telegram_bot.py` - Main bot script
- `.env.example` - Environment variables template
- `requirements.txt` - Python dependencies

## Quick Deploy to Render.com (Free VPS)

### Step 1: Push to GitHub
```bash
cd /Users/ankitkhandelwal/clawd/polymarket-bot-deploy
git add .
git commit -m "Add env file"
git push origin main
```

### Step 2: Deploy on Render
1. Go to https://render.com
2. New Web Service
3. Connect GitHub: `akhbarsingh06-dev/polymarket-bot`
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python3 polymarket_telegram_bot.py`
   - Plan: Free

### Step 3: Add Environment Variables
In Render dashboard, go to Environment and add:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHANNEL_ID=@your_channel_name
POLYMARKET_API_KEY=your_polymarket_api_key
```

### Step 4: Deploy!
Click "Deploy Web Service" and your bot will be live in 2-3 minutes!

## Telegram Setup
1. Create bot via @BotFather on Telegram
2. Get bot token
3. Create channel, add bot as admin
4. Get channel ID (@channelname or -100xxxxxxx)

## Polymarket API
Get your API key from: https://gamma.polymarket.com/api

## Local Testing
```bash
cp .env.example .env
# Edit .env with your values
python3 polymarket_telegram_bot.py
```

## Telegram Channel
@polymarketpredictionsAlert

## License
MIT

## Credits
Built with ❤️ for Polymarket traders
