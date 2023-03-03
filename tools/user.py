async def render_list_users(list_users: list) -> str:
    response_text = ''
    for u in list_users:
        response_text += f'{u.id} ({u.telegram_id}) {u.username} {u.get_role_name()}\n'
    return response_text
