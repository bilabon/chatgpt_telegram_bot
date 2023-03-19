from tools.db import get_db

USER_ROLE_CHOICES = {
    'admin': 1,
    'client': 2,
    'alien': 3,
    'blocked': 4,
}

USER_MODE_CHOICES = {
    'assistant': 1,
    'code_assistant': 2,
    'translate_assistant': 3,
}

USER_MODES_CONFIGS = {
    'assistant': {
        'name': '👩🏼‍🎓 General Assistant',
        'welcome_message': "👩🏼‍🎓 Hi, I'm <b>ChatGPT general assistant</b>. How can I help you?",
        'system_message': "As an advanced chatbot, your goal is to help users by answering questions, providing information, and completing tasks. Be detailed and thorough in your responses, using examples and evidence to support your recommendations. Always prioritize the user's needs and satisfaction to provide a helpful and enjoyable experience.",
        'temperature': 1,
    },
    'code_assistant': {
        'name': '👩🏼‍💻 Code Assistant',
        'welcome_message': "👩🏼‍💻 Hi, I'm <b>ChatGPT code assistant</b>. How can I help you?",
        'system_message': 'As an advanced code assistant, your aim is to assist users in writing code by editing, designing, describing, and providing helpful information. It is crucial to provide correct and error-free detailed code examples. Format output in Markdown.',
        'temperature': 0,
    },
    'translate_assistant': {
        'name': '👩‍🏫 Translation Assistant',
        'welcome_message': "👩‍🏫 Hi, I'm <b>ChatGPT translation assistant</b>. How can I help you?",
        'system_message': 'You are an advanced translation assistant, your primary goal is to assist users to translate and paraphrase text.',
        'temperature': 0.5,
    },
}


class User:
    def __init__(self, _id, username, first_name, telegram_id, language_code, time_added, role_id,
                 mode_id):
        self.id = _id
        self.username = username
        self.first_name = first_name
        self.telegram_id = telegram_id
        self.language_code = language_code
        self.time_added = time_added
        self.role_id = role_id
        self.mode_id = mode_id

    @property
    def is_admin(self):
        return bool(self.role_id == USER_ROLE_CHOICES['admin'])

    @property
    def is_client(self):
        return bool(self.role_id == USER_ROLE_CHOICES['client'])

    @property
    def is_alien(self):
        return bool(self.role_id == USER_ROLE_CHOICES['alien'])

    @property
    def is_blocked(self):
        return bool(self.role_id == USER_ROLE_CHOICES['blocked'])

    def get_role_name(self):
        return list(USER_ROLE_CHOICES.keys())[list(USER_ROLE_CHOICES.values()).index(self.role_id)]

    def get_mode_name(self):
        return list(USER_MODE_CHOICES.keys())[list(USER_MODE_CHOICES.values()).index(self.mode_id)]

    async def save_mode_name(self, name):
        if name in USER_MODE_CHOICES:
            async with get_db() as conn:
                mode_id = USER_MODE_CHOICES[name]
                sql = "UPDATE user SET mode_id=? WHERE telegram_id=?;"
                args = (mode_id, self.telegram_id)
                await conn.execute(sql, args)
                await conn.commit()
            self.mode_id = mode_id

    def get_mode_config(self):
        return USER_MODES_CONFIGS[self.get_mode_name()]

    @property
    def get_mode_choices(self):
        return USER_MODE_CHOICES

    async def get_balance_spent(self) -> int:
        _sql = "SELECT SUM(total_tokens) FROM user_message WHERE user_id=?;"
        args = (self.id,)
        async with get_db() as conn:
            async with conn.execute(_sql, args) as cursor:
                balance_spent = await cursor.fetchone()
        return balance_spent[0] or 0

    async def get_balance_credited(self) -> int:
        _sql = "SELECT SUM(tokens) FROM user_balance WHERE user_id=?;"
        args = (self.id,)
        async with get_db() as conn:
            async with conn.execute(_sql, args) as cursor:
                balance_credited = await cursor.fetchone()
        return balance_credited[0] or 0
