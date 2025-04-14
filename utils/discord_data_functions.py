import discord


async def get_user_avatar(ctx, user_id):
    try:
        user = await ctx.guild.fetch_member(user_id)
        avatar_url = user.avatar.url
    except discord.NotFound:
        avatar_url = None
    
    return avatar_url