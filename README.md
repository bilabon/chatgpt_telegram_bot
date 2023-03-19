# chatgpt_telegram_bot

#### News
- _v1.31 19 Mar 2023_ - Add VOICE_LIMIT_DURATION_SEC to configs for limitation duration of voice messages, please check config_template.py and update config.py
- _v1.30 19 Mar 2023_ - Add telegram commands to post_init(). Run the bot in async mode. Bugfixes, improvements. Please reinstall requirements.txt. Add logging to files.
- _v1.21 15 Mar 2023_ - Add `/retry` command to regenerate last bot answer.
- _v1.20 15 Mar 2023_ - Add balances logic. Add checking negative token balance. Add FREE_TOKENS after registration. Use
  async openai API requests. DB migration. Improvement. Add commands: `/balance`, `/addbalance`. Update
  commands: `/help`, `/setrole`.
- _v1.11 14 Mar 2023_ - Use ParseMode.MARKDOWN for Code Assistant mode, minor fixes and improvements.
- _v1.10 14 Mar 2023_ - Support voice messages. (To work, you need to install this
  package: `sudo apt-get install -y ffmpeg`).
- _v1.00 14 Mar 2023_ - Support `/mode` command. You can select from 3 special chat modes: General Assistant, Code
  Assistant, Translation Assistant. The modes work with/without context. To enable context just use `/contexton`
  command. By default the context is disabled.
- _v0.19 14 Mar 2023_ - Stylized bot answers with emoji. Add tables user.total_tokens and user_message.total_tokens and
  save total_tokens in user_message.total_tokens.
- _v0.18 12 Mar 2023_ - Refactoring & bugfixes.
- _v0.17 11 Mar 2023_ - Handle Edit events at telegramm.

#### HOWTO setup

```
sudo apt-get update && sudo apt-get install -y ffmpeg

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

- Each user who contacts the chat for the first time will be added to the database and assigned the role of `alien`.
  There are four roles in the bot: `admin`, `client`, `alien` and `blocked`. To communicate with ChatGPT, a user needs
  to have the role of `admin` or `client`.
- A user with the role of `admin` can assign roles to other users, for example: `/setrole username client`.
- The command `/list` will show all users (id and username). This command is only available for users with the role
  of `admin`.
- The command `/context on` will turn on the context
  support. [Example](https://github.com/bilabon/chatgpt_telegram_bot#-1).
- The command `/context off` will turn off the context support.
- The command `/mode` – will show chat modes. You can select from 3 special chat modes: General Assistant, Code
  Assistant, Translation Assistant.
- The command `/retry` - will regenerate last bot answer.

#### ![pic1](https://i.ibb.co/dJSLCQW/Screenshot-2023-02-25-at-23-37-31.png)

#### ![pic2](https://i.ibb.co/gmBrYNL/Screenshot-2023-03-12-at-12-58-12.png)

#### Configure command hints (optional, but fancy)

At [@BotFather](https://telegram.me/BotFather), use command /mybots -> select your bot -> Edit Bot -> Edit Commands.
Then paste the following text to the BotFather:

```
retry - Regenerate last bot answer
mode - Select chat mode
contexton - Messaging with context
contextoff - Messaging without context
balance - Show balance
help - Show help
```

After that, you will be able to utilize menu shortcuts or receive prompts while entering commands.

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
