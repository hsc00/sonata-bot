import discord
import unicodedata
import re
from API.album_cache import get_album_from_cache, update_releases_likes_dislikes
from API.artist_cache import get_artist_from_cache ,update_artist_likes_dislikes
from emoji_links import streaming_emojis


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
        self.add_item(LikeButton(self.action_type, self.likes, self.original_message_id, self.artist_name, self.release_name))
        self.add_item(DislikeButton(self.action_type, self.dislikes, self.original_message_id, self.artist_name, self.release_name))
        if album_wiki:
            self.add_item(AlbumInfoButton(album_wiki))
        if performers:
            self.add_item(CreditsButton(self.performers))
        if self.streaming_links:
            self.add_item(StreamingButton(self.streaming_links))

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
        self.add_item(LikeButton(self.action_type, self.likes, self.original_message_id, self.artist_name, release_name))
        self.add_item(DislikeButton(self.action_type, self.dislikes, self.original_message_id, self.artist_name, release_name))
        if similar_artists:
            self.add_item(SimilarArtistsButton(self.similar_artists))
        if self.streaming_links:
            self.add_item(StreamingButton(self.streaming_links))



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
        nickname = interaction.user.display_name

        # Check if the user has already liked the release/artist
        if self.action_type == "release":
            album_data = get_album_from_cache(self.artist_name +"-"+ self.release_name, increment_request_count=False)
            if album_data and user_id in album_data.get('liked_users', []):
                try:
                    await interaction.response.send_message('You have already liked this release.', ephemeral=True)
                except discord.errors.NotFound:
                    print("Interaction not found or expired.")
                return
            handle_like_dislike(self.action_type, self.artist_name +"-"+ self.release_name, user_id, like=True)
            refresh_likes = album_data
        elif self.action_type == "artist":
            artist_data = get_artist_from_cache(self.artist_name, increment_request_count=False)
            if artist_data and user_id in artist_data.get('liked_users', []):
                try:
                    await interaction.response.send_message('You have already liked this artist.', ephemeral=True)
                except discord.errors.NotFound:
                    print("Interaction not found or expired.")
                return
            handle_like_dislike(self.action_type, self.artist_name, user_id, like=True)
            refresh_likes = artist_data

        # refresh like/dislike button numbers  
        if user_id in refresh_likes.get('disliked_users', []):
            for button in self.view.children:
                if button.custom_id == 'dislike_button': button.label = str(refresh_likes['dislikes'] - 1 ) + ' 👎'
        for button in self.view.children:
            if button.custom_id == 'like_button': button.label = str(refresh_likes['likes'] + 1) + ' ❤️'

        # Delete the previous dislike message if it exists
        previous_dislike_message_id = self.view.message_ids.get((user_id, 'dislike'))
        if previous_dislike_message_id:
            try:
                previous_message = await interaction.channel.fetch_message(previous_dislike_message_id)
                await previous_message.delete()
            except discord.NotFound:
                pass

        # Send the ephemeral response
        try:
            await interaction.response.send_message('Your like has been recorded.', ephemeral=True)
        except discord.errors.NotFound:
            print("Interaction not found or expired.")

        # Send the new like message as a reply to the album embed and store its ID
        original_message = await interaction.channel.fetch_message(self.original_message_id)
        if self.action_type == "release": 
            message = await original_message.reply(f'{nickname} liked **{self.release_name}**!')
        elif self.action_type == "artist": 
            message = await original_message.reply(f'{nickname} liked **{self.artist_name}**!')
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
        nickname = interaction.user.display_name

        # Check if the user has already disliked the release
        if self.action_type == "release":
            album_data = get_album_from_cache(self.artist_name +"-"+ self.release_name, increment_request_count=False)
            if album_data and user_id in album_data.get('disliked_users', []):
                try:
                    await interaction.response.send_message('You have already disliked this release.', ephemeral=True)
                except discord.errors.NotFound:
                    print("Interaction not found or expired.")
                return
            handle_like_dislike(self.action_type, self.artist_name +"-"+ self.release_name, user_id, like=False)
            refresh_dislikes = album_data

        elif self.action_type == "artist":
            artist_data = get_artist_from_cache(self.artist_name, increment_request_count=False)
            if artist_data and user_id in artist_data.get('disliked_users', []):
                try:
                    await interaction.response.send_message('You have already disliked this artist.', ephemeral=True)
                except discord.errors.NotFound:
                    print("Interaction not found or expired.")
                return
            handle_like_dislike(self.action_type, self.artist_name, user_id, like=False)
            refresh_dislikes = artist_data

        # refresh like/dislike button numbers  
        if user_id in refresh_dislikes.get('liked_users', []):
            for button in self.view.children:
                if button.custom_id == 'like_button': button.label = str(refresh_dislikes['likes'] - 1) + ' ❤️'
        for button in self.view.children:
            if button.custom_id == 'dislike_button': button.label = str(refresh_dislikes['dislikes'] + 1 ) + ' 👎'

        # Delete the previous like message if it exists
        previous_like_message_id = self.view.message_ids.get((user_id, 'like'))
        if previous_like_message_id:
            try:
                previous_message = await interaction.channel.fetch_message(previous_like_message_id)
                await previous_message.delete()
            except discord.NotFound:
                pass

        # Send the ephemeral response
        try:
            await interaction.response.send_message('Your dislike has been recorded.', ephemeral=True)
        except discord.errors.NotFound:
            print("Interaction not found or expired.")

        # Send the new dislike message as a reply to the album embed and store its ID
        original_message = await interaction.channel.fetch_message(self.original_message_id)
        if self.action_type == "release": 
            message = await original_message.reply(f'{nickname} disliked **{self.release_name}**!')
        elif self.action_type == "artist": 
            message = await original_message.reply(f'{nickname} disliked **{self.artist_name}**!')
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
                emoji=streaming_emojis.get(link.split('.')[1].capitalize(), link.split('.')[1].capitalize()),
                url=link
            ) for link in self.streaming_links
        ]

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
