import discord
from discord.ext import commands
from discord import app_commands

class team_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mainEmbed = discord.Embed(title="팀원 모집", color=discord.Color(0x87CEFA))

    @app_commands.command(name="팀", description="recruit teamate")
    async def recruit_team(self, interaction : discord.Interaction, capacity:int, description:str):
        voice_channel = interaction.user.voice.channel
        if voice_channel:
            embed = self.mainEmbed.copy()
            embed.title = "팀원 모집"
            embed.description = f"{interaction.user.mention}님이 팀원을 모집 중 입니다."
            embed.add_field(name="카테고리", value=voice_channel.category.name if voice_channel.category else "없음")
            embed.add_field(name="채널명", value=f"<#{voice_channel.id}>")
            embed.add_field(name="멤버", value=f"{capacity}명 / 4명")
            embed.add_field(name="설명", value=description)
            view = discord.ui.View()
            join_button = discord.ui.Button(label="채널 참가", style=discord.ButtonStyle.link, url=f"https://discord.com/channels/{interaction.guild.id}/{voice_channel.id}")
            view.add_item(join_button)
            await interaction.response.send_message(embed=embed, view=view)
        else:
            await interaction.response.send_message("음성채널에 접속 후 사용해주세요", ephemeral=True)
            return


async def setup(bot):
    await bot.add_cog(team_cog(bot))