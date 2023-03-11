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

And now you neet to set BOT_TOKEN, AI_TOKEN, ADMIN_USERNAME in settings/config.py
- AI_TOKEN from here https://platform.openai.com/account/api-keys
- BOT_TOKEN from https://telegram.me/BotFather
- ADMIN_USERNAME - your username from telegram without @
- GPT_MODEL - model `gpt-3.5-turbo` or `text-davinci-003` from here https://platform.openai.com/docs/models/overview 

#### Info
- The first thing an admin needs to do in a chat room is to execute the command `/start`. This command will create a database.
- Each user who contacts the chat for the first time will be added to the database and assigned the role of `alien`. There are four roles in the bot: `admin`, `client`, `alien` and `blocked`. To communicate with ChatGPT, a user needs to have the role of `admin` or `client`.
- A user with the role of `admin` can assign roles to other users, for example: `/setrole username client`.
- The command `/list` will show all users (id and username). This command is only available for users with the role of `admin`.
- The command `/context on` will turn on the context support. [Example](https://github.com/bilabon/chatgpt_telegram_bot#-1).
- The command `/context off` will turn off the context support. 

#### ![pic1](https://i.ibb.co/dJSLCQW/Screenshot-2023-02-25-at-23-37-31.png)

#### ![pic2](https://i.ibb.co/mhVLGhd/Screenshot-2023-03-11-at-18-36-54.png)

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

# to stop app:
# https://community.fly.io/t/is-it-possible-to-disable-an-app-without-deleting-it/3662/2
flyctl scale count 0
fly status --all
fly vm stop e2dc2b0c

# to start app:
flyctl scale count 1
```
