import discord


async def get_user_avatar(ctx, user_id):
    try:
        user = await ctx.guild.fetch_member(user_id)
        avatar_url = user.avatar.url
    except discord.NotFound:
        avatar_url = None
    
    return avatar_url

async def get_user_username(ctx, user_id):
    try:
        user = await ctx.guild.fetch_member(user_id)
        username = user.name
    except discord.NotFound:
        try:
            user = await ctx.bot.fetch_user(user_id)
            username = user.name
        except discord.NotFound:
            username = None
        except discord.HTTPException as e:
            print(f"Error fetching user: {e}")
            username = None
    except discord.HTTPException as e:
        print(f"Error fetching member: {e}")
        username = None

    return username