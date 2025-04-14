import json
import os


def rym_user_data(ctx, rym_user_id):
    cache_file = 'cache/rym-cache.json'

    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}
    else:
        with open(cache_file, 'w') as f:
            json.dump({}, f) 
        data = {}

    # Check if a specific user ID or mention is provided
    if rym_user_id:
        # Extract the user ID from the mention if necessary
        if rym_user_id.startswith('<@') and rym_user_id.endswith('>'):
            rym_user_id = rym_user_id[2:-1]
            if rym_user_id.startswith('!'):
                rym_user_id = rym_user_id[1:]
    else:
        rym_user_id = str(ctx.author.id)

    if rym_user_id in data:
        username = data[rym_user_id]
        link = f"https://rateyourmusic.com/~{username}"
    else:
        username = None
        link = None

    return data, rym_user_id, username, link
