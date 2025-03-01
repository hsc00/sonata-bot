import discord
from discord.ext import commands
from urllib.parse import urlencode
import requests
import config
import time


client_id = config.spotify_id
client_secret = config.spotify_secret
redirect_uri = 'https://sotao.maeva.garden/'

# Initialize the TokenManager globally
from classes.token_manager import TokenManager
token_manager = TokenManager()

awaiting_token = {}

def setup(bot):
    @bot.command(name='setspotify')
    async def authorize(ctx):
        # Step 1: Send the user to the Spotify authorization URL via DM
        auth_url = 'https://accounts.spotify.com/authorize'
        auth_params = {
            'client_id': client_id,
            'response_type': 'code',
            'redirect_uri': redirect_uri,
            'scope': 'user-read-playback-state user-read-currently-playing',
        }
        auth_request_url = f"{auth_url}?{urlencode(auth_params)}"
        try:
            await ctx.author.send(f"Please authorize the application by clicking [here]({auth_request_url})")
            await ctx.reply("Authorization link has been sent to your DM!")
            time.sleep(5)
            await ctx.author.send(f"When you finish send me the code you received from spotify ^_^")

            # Store state that we're awaiting a token for this user
            awaiting_token[ctx.author.id] = True
        except discord.Forbidden:
            await ctx.reply("I couldn't send you a DM. Please enable DMs from server members and try again :/")

    async def callback(ctx, code: str):
        user_id = ctx.author.id

        # Step 2: Exchange the authorization code for an access token
        token_url = 'https://accounts.spotify.com/api/token'
        token_data = {
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': redirect_uri,
            'client_id': client_id,
            'client_secret': client_secret,
        }
        token_response = requests.post(token_url, data=token_data)
        token_info = token_response.json()

        if 'access_token' in token_info and 'refresh_token' in token_info:
            access_token = token_info['access_token']
            refresh_token = token_info['refresh_token']
            expires_in = token_info['expires_in']

            # Debug: Print tokens before updating
            print(f"Updating tokens for user {user_id}")

            # Update tokens in the manager using user_id
            token_manager.update_tokens(user_id, access_token, refresh_token, expires_in)

            await ctx.author.send("Authorization successful. You can now use the bot commands!! ^_^")
        else:
            await ctx.author.send("Error fetching access token :(")

    @bot.event
    async def on_message(message):
        user_id = message.author.id

        if isinstance(message.channel, discord.DMChannel):
            if user_id in awaiting_token and awaiting_token[user_id]:
                code = message.content.strip()
                ctx = await bot.get_context(message)
                await callback(ctx, code)
                awaiting_token[user_id] = False
        await bot.process_commands(message)
