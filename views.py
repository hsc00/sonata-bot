import discord
from API.rym_search import handle_like_dislike
from API.album_cache import get_album_from_cache, update_likes_dislikes
from emoji_links import streaming_emojis

class RYMView(discord.ui.View):
    def __init__(self, album_wiki=None, general_embed=None, original_message_id=None, release_name=None, streaming_links=None, performers=None):
        super().__init__()
        self.album_wiki = album_wiki
        self.general_embed = general_embed
        self.original_message_id = original_message_id
        self.release_name = release_name
        self.streaming_links = streaming_links
        self.performers = performers
        self.message_ids = {}
        self.add_item(LikeButton(self.original_message_id, self.release_name))
        self.add_item(DislikeButton(self.original_message_id, self.release_name))
        if album_wiki:
            self.add_item(AlbumInfoButton(album_wiki))
        if performers:
            self.add_item(CreditsButton(self.performers))
        if streaming_links:
            self.add_item(StreamingButton(streaming_links))



class LikeButton(discord.ui.Button):
    def __init__(self, original_message_id, release_name):
        super().__init__(label='❤️', style=discord.ButtonStyle.secondary, custom_id='like_button')
        self.original_message_id = original_message_id
        self.release_name = release_name

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        nickname = interaction.user.display_name

        # Check if the user has already liked the release
        album_data = get_album_from_cache(self.view.link, increment_request_count=False)
        if album_data and user_id in album_data.get('liked_users', []):
            try:
                await interaction.response.send_message('You have already liked this release.', ephemeral=True)
            except discord.errors.NotFound:
                print("Interaction not found or expired.")
            return

        handle_like_dislike(self.view.link, user_id, like=True)

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
        message = await original_message.reply(f'{nickname} liked **{self.release_name}**!')
        self.view.message_ids[(user_id, 'like')] = message.id

        # Update the cache
        update_likes_dislikes(self.view.link, user_id, like=True)

        # Update the embed with the correct number of likes and dislikes
        album_data = album_data = get_album_from_cache(self.view.link, increment_request_count=False)
        new_embed = interaction.message.embeds[0]
        new_embed.clear_fields()
        new_embed.add_field(name="\u200b", value=f"❤️ {album_data['likes']} \t 👎 {album_data['dislikes']}", inline=True)
        await interaction.message.edit(embed=new_embed)

class DislikeButton(discord.ui.Button):
    def __init__(self, original_message_id, release_name):
        super().__init__(label='👎', style=discord.ButtonStyle.secondary, custom_id='dislike_button')
        self.original_message_id = original_message_id
        self.release_name = release_name

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        nickname = interaction.user.display_name

        # Check if the user has already disliked the release
        album_data = get_album_from_cache(self.view.link, increment_request_count=False)
        if album_data and user_id in album_data.get('disliked_users', []):
            try:
                await interaction.response.send_message('You have already disliked this release.', ephemeral=True)
            except discord.errors.NotFound:
                print("Interaction not found or expired.")
            return

        handle_like_dislike(self.view.link, user_id, like=False)

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
        message = await original_message.reply(f'{nickname} disliked **{self.release_name}**!')
        self.view.message_ids[(user_id, 'dislike')] = message.id

        # Update the cache
        update_likes_dislikes(self.view.link, user_id, like=False)

        # Update the embed with the correct number of likes and dislikes
        album_data = get_album_from_cache(self.view.link, increment_request_count=False)
        new_embed = interaction.message.embeds[0]
        new_embed.clear_fields()
        new_embed.add_field(name="\u200b", value=f"❤️ {album_data['likes']} \t 👎 {album_data['dislikes']}", inline=True)
        await interaction.message.edit(embed=new_embed)



class AlbumInfoButton(discord.ui.Button):
    def __init__(self, album_wiki):
        super().__init__(label='Wiki', style=discord.ButtonStyle.primary, custom_id='album_info')
        self.album_wiki = album_wiki

    async def callback(self, interaction: discord.Interaction):
        new_embed = discord.Embed(title=interaction.message.embeds[0].title, description=self.album_wiki, url=interaction.message.embeds[0].url)
        if interaction.message.embeds[0].thumbnail:
            new_embed.set_thumbnail(url=interaction.message.embeds[0].thumbnail.url)
        new_embed.set_footer(text=interaction.message.embeds[0].footer.text)
        self.view.clear_items()
        self.view.add_item(BackButton(self.view.general_embed, self.view.original_message_id, self.view.release_name, self.view.streaming_links, self.view.performers))
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
        self.view.add_item(BackButton(self.view.general_embed, self.view.original_message_id, self.view.release_name, self.view.streaming_links, self.view.performers))
        await interaction.response.edit_message(embed=new_embed, view=self.view)



class StreamingButton(discord.ui.Button):
    def __init__(self, streaming_links):
        super().__init__(label='Streaming', style=discord.ButtonStyle.primary, custom_id='streaming_button')
        self.streaming_links = streaming_links

    async def callback(self, interaction: discord.Interaction):
        embed = interaction.message.embeds[0]
        self.view.clear_items()
        self.view.add_item(BackButton(self.view.general_embed, self.view.original_message_id, self.view.release_name, self.streaming_links, self.view.performers))
        for link in self.streaming_links:
            service_name = link.split('.')[1].capitalize()
            emoji = streaming_emojis.get(service_name, service_name)
            button = discord.ui.Button(label="", emoji=emoji, url=link)
            self.view.add_item(button)
        await interaction.message.edit(embed=embed, view=self.view)



class BackButton(discord.ui.Button):
    def __init__(self, general_embed, original_message_id, release_name, streaming_links, performers):
        super().__init__(label='Back', style=discord.ButtonStyle.secondary, custom_id='back_button')
        self.general_embed = general_embed
        self.original_message_id = original_message_id
        self.release_name = release_name
        self.streaming_links = streaming_links
        self.performers = performers

    async def callback(self, interaction: discord.Interaction):
        self.view.clear_items()
        self.view.add_item(LikeButton(self.original_message_id, self.release_name))
        self.view.add_item(DislikeButton(self.original_message_id, self.release_name))
        self.view.add_item(AlbumInfoButton(self.view.album_wiki))
        self.view.add_item(CreditsButton(self.view.performers))
        if self.streaming_links:
            self.view.add_item(StreamingButton(self.streaming_links))
        await interaction.response.edit_message(embed=self.general_embed, view=self.view)
