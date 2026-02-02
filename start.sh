#!/bin/bash
# Polymarket Telegram Bot - Startup Script for Railway

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Starting Polymarket Telegram Bot..."
python3 polymarket_telegram_bot.py
