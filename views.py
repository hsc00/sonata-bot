import discord
import unicodedata
import re
from API.album_cache import get_album_from_cache, update_releases_likes_dislikes
from API.artist_cache import get_artist_from_cache ,update_artist_likes_dislikes
from emoji_links import streaming_emojis


class Paginator(discord.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=180)
        self.embeds = embeds
        self.current_page = 0
        
        if len(embeds) > 1:
            self.previous_button = discord.ui.Button(label="Previous", style=discord.ButtonStyle.primary, disabled=True)
            self.previous_button.callback = self.previous_callback
            self.add_item(self.previous_button)
            
            self.next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.primary, disabled=False)
            self.next_button.callback = self.next_callback
            self.add_item(self.next_button)
        
        self.update_buttons()

    async def previous_callback(self, interaction: discord.Interaction):
        await self.change_page(interaction, -1)

    async def next_callback(self, interaction: discord.Interaction):
        await self.change_page(interaction, 1)

    async def change_page(self, interaction: discord.Interaction, increment: int):
        await interaction.response.defer()
        self.current_page = max(0, min(self.current_page + increment, len(self.embeds) - 1))
        self.update_buttons()
        await interaction.edit_original_response(embed=self.embeds[self.current_page], view=self)

    def update_buttons(self):
        if len(self.embeds) > 1:
            self.previous_button.disabled = self.current_page == 0
            self.next_button.disabled = self.current_page == len(self.embeds) - 1


class RYMViewReleases(discord.ui.View):
    def __init__(self, album_wiki=None, general_embed=None, likes=None, dislikes=None, original_message_id=None, artist_name=None, release_name=None, streaming_links=None, performers=None):
        super().__init__()
        self.action_type = "release"
        self.album_wiki = album_wiki
        self.likes = likes
        self.dislikes = dislikes
        self.general_embed = general_embed
        self.original_message_id = original_message_id
        self.artist_name = artist_name
        self.release_name = release_name
        self.streaming_links = streaming_links or []
        self.performers = performers
        self.message_ids = {}
        
        # Initialize only required items
        buttons = [
            LikeButton(self.action_type, self.likes, self.original_message_id, self.artist_name, self.release_name),
            DislikeButton(self.action_type, self.dislikes, self.original_message_id, self.artist_name, self.release_name)
        ]
        
        if album_wiki:
            buttons.append(AlbumInfoButton(album_wiki))
        if performers:
            buttons.append(CreditsButton(self.performers))
        if self.streaming_links:
            buttons.append(StreamingButton(self.streaming_links))
        
        for button in buttons:
            self.add_item(button)


class RYMViewArtists(discord.ui.View):
    def __init__(self, artist_name=None, similar_artists=None, general_embed=None, likes=None, dislikes=None, original_message_id=None, streaming_links=None, release_name=None):
        super().__init__()
        self.action_type = "artist"
        self.artist_name = artist_name
        self.similar_artists = similar_artists or []
        self.general_embed = general_embed
        self.likes = likes
        self.dislikes = dislikes
        self.original_message_id = original_message_id
        self.streaming_links = streaming_links or []
        self.release_name = release_name
        self.message_ids = {}
        
        # Initialize only required items
        buttons = [
            LikeButton(self.action_type, self.likes, self.original_message_id, self.artist_name, self.release_name),
            DislikeButton(self.action_type, self.dislikes, self.original_message_id, self.artist_name, self.release_name)
        ]
        
        if self.similar_artists:
            buttons.append(SimilarArtistsButton(self.similar_artists))
        if self.streaming_links:
            buttons.append(StreamingButton(self.streaming_links))
        
        for button in buttons:
            self.add_item(button)


class LikeButton(discord.ui.Button):
    def __init__(self, action_type, likes, original_message_id, artist_name, release_name):
        self.likes = likes
        super().__init__(label=str(self.likes) + ' ❤️', style=discord.ButtonStyle.secondary, custom_id='like_button')
        self.action_type = action_type
        self.original_message_id = original_message_id
        self.artist_name = artist_name
        self.release_name = release_name

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = interaction.user.name

        # Check if the user has already liked the release/artist
        if self.action_type == "release":
            album_data = get_album_from_cache(f"{self.artist_name} - {self.release_name}", increment_request_count=False)
            if album_data and user_id in album_data.get('liked_users', []):
                if not interaction.response.is_done():
                    await interaction.response.send_message('Your like was removed.', ephemeral=True)
            handle_like_dislike(self.action_type, f"{self.artist_name} - {self.release_name}", user_id, like=True)
            refresh_likes = album_data
        elif self.action_type == "artist":
            artist_data = get_artist_from_cache(self.artist_name, increment_request_count=False)
            if artist_data and user_id in artist_data.get('liked_users', []):
                if not interaction.response.is_done():
                    await interaction.response.send_message('Your like was removed.', ephemeral=True)
            handle_like_dislike(self.action_type, self.artist_name, user_id, like=True)
            refresh_likes = artist_data

        # Refresh like/dislike button numbers  
        if user_id in refresh_likes.get('disliked_users', []):
            for button in self.view.children:
                if button.custom_id == 'dislike_button': 
                    button.label = str(len(refresh_likes['disliked_users']) - 1 ) + ' 👎'
        if user_id in refresh_likes.get('liked_users', []):
            for button in self.view.children:
                if button.custom_id == 'like_button':
                    button.label = str(len(refresh_likes['liked_users']) - 1) + ' ❤️'
        else:
            for button in self.view.children:
                if button.custom_id == 'like_button':
                    button.label = str(len(refresh_likes['liked_users']) + 1) + ' ❤️'

        # Delete the previous dislike message if it exists
        previous_dislike_message_id = self.view.message_ids.get((user_id, 'dislike'))
        if previous_dislike_message_id:
            try:
                previous_message = await interaction.channel.fetch_message(previous_dislike_message_id)
                await previous_message.delete()
            except discord.NotFound:
                pass

        # Send the ephemeral response
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message('Your like has been recorded.', ephemeral=True)
            except discord.errors.NotFound:
                print("Interaction not found or expired.")

        # Send the new like message as a reply to the album embed and store its ID
        original_message = await interaction.channel.fetch_message(self.original_message_id)
        if user_id not in refresh_likes.get('liked_users'):
            if self.action_type == "release": 
                message = await original_message.reply(f'{username} liked **{self.release_name}**!')
            elif self.action_type == "artist": 
                message = await original_message.reply(f'{username} liked **{self.artist_name}**!')
        else:
            if self.action_type == "release": 
                message = await original_message.reply(f"{username} doesn't like **{self.release_name}** anymore!")
            elif self.action_type == "artist": 
                message = await original_message.reply(f"{username} doesn't like **{self.artist_name}** anymore!")
        self.view.message_ids[(user_id, 'like')] = message.id

        # Clear and update embed fields 
        new_embed = interaction.message.embeds[0] 
        new_embed.clear_fields() 

        await interaction.message.edit(embed=new_embed, view=self.view)


class DislikeButton(discord.ui.Button):
    def __init__(self, action_type, dislikes, original_message_id, artist_name, release_name):
        self.dislikes = dislikes
        super().__init__(label=str(self.dislikes) + ' 👎', style=discord.ButtonStyle.secondary, custom_id='dislike_button')
        self.action_type = action_type
        self.original_message_id = original_message_id
        self.artist_name = artist_name
        self.release_name = release_name

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        username = interaction.user.name

        # Check if the user has already disliked the release/artist
        if self.action_type == "release":
            album_data = get_album_from_cache(f"{self.artist_name} - {self.release_name}", increment_request_count=False)
            if album_data and user_id in album_data.get('disliked_users', []):
                if not interaction.response.is_done():
                    await interaction.response.send_message('Your dislike was removed.', ephemeral=True)
            handle_like_dislike(self.action_type, f"{self.artist_name} - {self.release_name}", user_id, like=False)
            refresh_dislikes = album_data
        elif self.action_type == "artist":
            artist_data = get_artist_from_cache(self.artist_name, increment_request_count=False)
            if artist_data and user_id in artist_data.get('disliked_users', []):
                if not interaction.response.is_done():
                    await interaction.response.send_message('Your dislike was removed.', ephemeral=True)
            handle_like_dislike(self.action_type, self.artist_name, user_id, like=False)
            refresh_dislikes = artist_data

        # Refresh like/dislike button numbers  
        if user_id in refresh_dislikes.get('liked_users', []):
            for button in self.view.children:
                if button.custom_id == 'like_button':
                    button.label = str(len(refresh_dislikes['liked_users']) - 1) + ' ❤️'
        if user_id in refresh_dislikes.get('disliked_users', []):
            for button in self.view.children:
                if button.custom_id == 'dislike_button':
                    button.label = str(len(refresh_dislikes['disliked_users']) - 1) + ' 👎'
        else:
            for button in self.view.children:
                if button.custom_id == 'dislike_button': 
                    button.label = str(len(refresh_dislikes['disliked_users']) + 1) + ' 👎'

        # Delete the previous like message if it exists
        previous_like_message_id = self.view.message_ids.get((user_id, 'like'))
        if previous_like_message_id:
            try:
                previous_message = await interaction.channel.fetch_message(previous_like_message_id)
                await previous_message.delete()
            except discord.NotFound:
                pass

        # Send the ephemeral response
        if not interaction.response.is_done():
            try:
                await interaction.response.send_message('Your dislike has been recorded.', ephemeral=True)
            except discord.errors.NotFound:
                print("Interaction not found or expired.")

        # Send the new like message as a reply to the album embed and store its ID
        original_message = await interaction.channel.fetch_message(self.original_message_id)
        if user_id not in refresh_dislikes.get('disliked_users'):
            if self.action_type == "release": 
                message = await original_message.reply(f'{username} disliked **{self.release_name}**!')
            elif self.action_type == "artist": 
                message = await original_message.reply(f'{username} disliked **{self.artist_name}**!')
        else:
            if self.action_type == "release": 
                message = await original_message.reply(f"{username} doesn't dislike **{self.release_name}** anymore!")
            elif self.action_type == "artist": 
                message = await original_message.reply(f"{username} doesn't dislike **{self.artist_name}** anymore!")
        self.view.message_ids[(user_id, 'dislike')] = message.id

        # Clear and update embed fields
        new_embed = interaction.message.embeds[0]
        new_embed.clear_fields()

        await interaction.message.edit(embed=new_embed, view=self.view)


class AlbumInfoButton(discord.ui.Button):
    def __init__(self, album_wiki):
        super().__init__(label='Wiki', style=discord.ButtonStyle.primary, custom_id='album_info')
        self.album_wiki = album_wiki

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Acknowledge the interaction to avoid timeout
        new_embed = discord.Embed(title=interaction.message.embeds[0].title, description=self.album_wiki, url=interaction.message.embeds[0].url)
        if interaction.message.embeds[0].thumbnail:
            new_embed.set_thumbnail(url=interaction.message.embeds[0].thumbnail.url)
        new_embed.set_footer(text=interaction.message.embeds[0].footer.text)
        self.view.clear_items()
        self.view.add_item(BackButton(self.view))
        await interaction.edit_original_response(embed=new_embed, view=self.view)


class SimilarArtistsButton(discord.ui.Button):
    def __init__(self, similar_artists):
        super().__init__(label='Similar Artists', style=discord.ButtonStyle.primary, custom_id='similar_artists')
        self.similar_artists = similar_artists

    async def callback(self, interaction: discord.Interaction):
        similar_artists_text = '\n'.join([f"[{artist}](https://rateyourmusic.com/artist/{normalize_link(artist)})" for artist in self.similar_artists])
        new_embed = discord.Embed(title=f"Similar Artists to {self.view.artist_name}", description=similar_artists_text)
        if interaction.message.embeds[0].thumbnail:
            new_embed.set_thumbnail(url=interaction.message.embeds[0].thumbnail.url)
        new_embed.set_footer(text=interaction.message.embeds[0].footer.text)
        self.view.clear_items()
        self.view.add_item(BackButton(self.view))
        await interaction.response.edit_message(embed=new_embed, view=self.view)


class CreditsButton(discord.ui.Button):
    def __init__(self, performers):
        super().__init__(label='Credits', style=discord.ButtonStyle.primary, custom_id='credits_button')
        self.performers = performers

    async def callback(self, interaction: discord.Interaction):
        new_embed = discord.Embed(title=interaction.message.embeds[0].title, description=self.performers, url=interaction.message.embeds[0].url)
        if interaction.message.embeds[0].thumbnail:
            new_embed.set_thumbnail(url=interaction.message.embeds[0].thumbnail.url)
        new_embed.set_footer(text=interaction.message.embeds[0].footer.text)
        self.view.clear_items()
        self.view.add_item(BackButton(self.view))
        await interaction.response.edit_message(embed=new_embed, view=self.view)

class StreamingButton(discord.ui.Button):
    def __init__(self, streaming_links):
        super().__init__(label='Streaming', style=discord.ButtonStyle.primary, custom_id='streaming_button')
        self.streaming_links = streaming_links
        self.buttons = [
            discord.ui.Button(
                label="",
                emoji=self.get_valid_emoji(link),
                url=link
            ) for link in self.streaming_links
        ]

    def get_valid_emoji(self, link):
        if "spotify" in link:
            return streaming_emojis["Spotify"]
        elif "apple" in link:
            return streaming_emojis["Apple"]
        elif "bandcamp" in link:
            return streaming_emojis["Bandcamp"]
        elif "soundcloud" in link:
            return streaming_emojis["Soundcloud"]
        elif "youtube" in link or "music.youtube" in link:
            return streaming_emojis["Youtube"]
        else:
            return '🔗'  # Default emoji

    async def callback(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]

        # Clear items only if necessary
        if self.view.children:
            self.view.clear_items()
            self.view.add_item(BackButton(self.view))

        # Add pre-generated buttons
        for button in self.buttons:
            self.view.add_item(button)

        await interaction.message.edit(embed=embed, view=self.view)


class BackButton(discord.ui.Button):
    def __init__(self, view):
        super().__init__(label='Back', style=discord.ButtonStyle.secondary, custom_id='back_button')
        self._view = view

    async def callback(self, interaction: discord.Interaction):
        self._view.clear_items()
        self._view.add_item(LikeButton(self._view.action_type, self._view.likes, self._view.original_message_id, self._view.artist_name, self._view.release_name))
        self._view.add_item(DislikeButton(self._view.action_type, self._view.dislikes, self._view.original_message_id, self._view.artist_name, self._view.release_name))

        if self._view.action_type == "release":
            if self._view.album_wiki:
                self._view.add_item(AlbumInfoButton(self._view.album_wiki))
            if self._view.performers:
                self._view.add_item(CreditsButton(self._view.performers))
                
        if self._view.action_type == "artist":
            if self._view.similar_artists:
                self._view.add_item(SimilarArtistsButton(self._view.similar_artists))

        if self._view.streaming_links:
            self._view.add_item(StreamingButton(self._view.streaming_links))

        await interaction.response.edit_message(embed=self._view.general_embed, view=self._view)


def handle_like_dislike(action_type, query, user_id, like=True):
    if action_type == "release":
        update_releases_likes_dislikes(query, user_id, like)
    elif action_type == "artist":
        update_artist_likes_dislikes(query, user_id, like)

def normalize_link(s):
    # Remove special characters and normalize the string
    s = unicodedata.normalize('NFKD', s)
    s = re.sub(r'[^\w\s-]', '', s)
    s = s.replace(' ', '-').lower()
    return s
