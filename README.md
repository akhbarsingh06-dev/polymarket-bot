# Polymarket Telegram Bot

Telegram bot that posts high-probability Polymarket market predictions

## Features
- Auto-scans Polymarket markets
- Posts when probability reaches 60%+
- Clear format showing both outcomes
- Supports crypto, sports, politics markets

## Files
- `polymarket_telegram_bot.py` - Main bot
- `telegram_config.env` - Telegram credentials

## Deploy to Render.com (Free VPS)
1. Push this repo to GitHub
2. Go to https://render.com
3. Sign up/Login
4. New Web Service
5. Connect GitHub repo
6. Settings:
   - Build Command: `pip install requests`
   - Start Command: `python3 polymymarket_telegram_bot.py`
7. Deploy!

## Telegram Channel
@polymarketpredictionsAlert

## License
MIT
