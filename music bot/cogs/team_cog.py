import discord
from discord.ext import commands

class team_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot



async def setup(bot):
    await bot.add_cog(team_cog(bot))