DB_NAME = 'db.sqlite'
BOT_TOKEN = 'setup in config_local.py'
AI_TOKEN = 'setup in config_local.py'
ADMIN_USERNAME = 'bilabon'

try:
    from settings.config_local import BOT_TOKEN, AI_TOKEN
except ModuleNotFoundError:
    raise ModuleNotFoundError("Create settings/config_local.py firstly with variables: BOT_TOKEN and AI_TOKEN")
