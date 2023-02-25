# chatgpt_telegram_bot
#### HOWTO setup
```
git clone git@github.com:bilabon/chatgpt_telegram_bot.git
cd chatgpt_telegram_bot
python3.11 -m venv .env && source .env/bin/activate
pip --no-cache-dir install -U pip && pip --no-cache-dir install -U setuptools && pip --no-cache-dir install -U wheel
pip --no-cache-dir install -U -r requirements.txt
cp settings/config_template.py settings/config.py
```    

And now you neet to set BOT_TOKEN, AI_TOKEN in settings/config.py
- AI_TOKEN from here https://platform.openai.com/account/api-keys
- BOT_TOKEN from https://telegram.me/BotFather
- ADMIN_USERNAME - your username from telegram

#### Commands for deploying to https://fly.io

```
brew install flyctl
flyctl auth signup
# https://www.youtube.com/watch?v=J7Fm7MdZn_E
flyctl launch
flyctl deploy

# how to download db from remote container https://www.autodidacts.io/backup-ghost-on-fly-sftp/
flyctl ssh sftp shell -r -a tbot
get /bot/db.sqlite

# how to connect to remote console https://fly.io/docs/flyctl/ssh-console/
flyctl ssh console -s tbot

# how to restart the remote app, you should do it because after deploying sometimes run 2 instances and you get an error
flyctl apps restart tbot
```
