# chatgpt_telegram_bot
HOWTO setup
```
git clone git@github.com:bilabon/chatgpt_telegram_bot.git
cd chatgpt_telegram_bot
python3.11 -m venv .env && source .env/bin/activate && pip freeze && python3.11 -V
pip --no-cache-dir install -U pip && pip --no-cache-dir install -U setuptools && pip --no-cache-dir install -U wheel
pip --no-cache-dir install -U -r requirements.txt && pip list --outdated --format=columns
cp settings/config_template.py settings/config.py
```    

And now you neet to set BOT_TOKEN, AI_TOKEN in settings/config.py
- AI_TOKEN from here https://platform.openai.com/account/api-keys
- BOT_TOKEN from https://telegram.me/BotFather

