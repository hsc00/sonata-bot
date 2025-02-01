import json
import os

def setup(bot):
    @bot.command(name='setfm')
    async def setfm(ctx, last_fm_username: str):
        # Create the cache directory if it doesn't exist
        if not os.path.exists('cache'):
            os.makedirs('cache')

        # Define the path to the JSON file
        cache_file = 'cache/lastfm-cache.json'

        # Load the existing data
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        else:
            data = {}

        # Update the data with the new user information
        data[str(ctx.author.id)] = last_fm_username

        # Save the updated data to the JSON file
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=4)

        # Create the hyperlink for the Last.fm username
        last_fm_profile_url = f"https://www.last.fm/user/{last_fm_username}"
        await ctx.send(f"{ctx.author.mention} last.fm has been set to [{last_fm_username}]({last_fm_profile_url})")
