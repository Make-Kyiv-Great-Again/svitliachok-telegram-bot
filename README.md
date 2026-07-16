# Svitliachok Telegram Bot

A Telegram bot to interface with the Svitliachok API.

## Setup

1. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Setup environment variables:
   Copy `.env.example` to `.env` and fill in your details:
   ```bash
   cp .env.example .env
   # Edit .env with your favorite editor
   ```

## Run

Run the bot using:
```bash
python -m app.main
```
