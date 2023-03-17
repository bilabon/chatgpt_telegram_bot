from prettytable import PrettyTable


async def render_list_users(list_users: list) -> str:
    table = PrettyTable()
    table.field_names = ['(id) username', 'role', 'bC', 'bU']
    for u in list_users:
        role = u.get_role_name()
        balance_credited = await u.get_balance_credited()
        balance_spent = await u.get_balance_spent()
        table.add_row([f"{u.id} {u.username}", role, f"{int(balance_credited / 1000)}k", balance_spent])
    return f'<pre>{table}</pre>'
