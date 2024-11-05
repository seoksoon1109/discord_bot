import discord
from discord.ext import commands
from discord import app_commands

class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="help", description="사용법을 출력합니다.")
    async def print_help(self, interaction:discord.Interaction):
        readme_url = "https://github.com/seoksoon1109/discord_bot/blob/main/README.md"
        await interaction.response.send_message("사용법을 DM으로 전송했습니다.", delete_after=3)
        await interaction.user.send(readme_url)
        
        
        
        
async def setup(bot):
    await bot.add_cog(help_cog(bot))