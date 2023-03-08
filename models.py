USER_ROLE_CHOICES = {
    'admin': 1,
    'client': 2,
    'alien': 3,
    'blocked': 4,
}


class User:
    def __init__(self, _id, username, first_name, telegram_id, language_code, time_added, role_id):
        self.id = _id
        self.username = username
        self.first_name = first_name
        self.telegram_id = telegram_id
        self.language_code = language_code
        self.time_added = time_added
        self.role_id = role_id

    @property
    def is_admin(self):
        return bool(self.role_id == USER_ROLE_CHOICES['admin'])

    @property
    def is_client(self):
        return bool(self.role_id == USER_ROLE_CHOICES['client'])

    def get_role_name(self):
        return list(USER_ROLE_CHOICES.keys())[list(USER_ROLE_CHOICES.values()).index(self.role_id)]