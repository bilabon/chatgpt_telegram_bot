async def render_list_users(list_users: list) -> str:
    response_text = '\n'.join(
        [f'{u.id} ({u.telegram_id}) {u.username} {u.get_role_name()}' for u in list_users]
    )
    return response_text
