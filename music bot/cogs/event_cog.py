import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime

class EventCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.event_settings = {}  # 서버별 신청 기간 설정
        self.participants = {}  # 서버별 참가자 리스트

    class ApplicationModal(discord.ui.Modal, title="신청 기간 설정"):
        def __init__(self, cog, guild_id):
            super().__init__()
            self.cog = cog
            self.guild_id = guild_id

            self.start_date = discord.ui.TextInput(
                label="시작 일시 (예: 2024-11-20 10:00)",
                placeholder="YYYY-MM-DD HH:MM",
                required=True,
            )
            self.end_date = discord.ui.TextInput(
                label="종료 일시 (예: 2024-11-21 18:00)",
                placeholder="YYYY-MM-DD HH:MM",
                required=True,
            )

            self.add_item(self.start_date)
            self.add_item(self.end_date)

        async def on_submit(self, interaction: discord.Interaction):
            try:
                start = datetime.strptime(self.start_date.value, "%Y-%m-%d %H:%M")
                end = datetime.strptime(self.end_date.value, "%Y-%m-%d %H:%M")

                if start >= end:
                    await interaction.response.send_message("시작 일시는 종료 일시보다 이전이어야 합니다.", ephemeral=True)
                    return

                self.cog.event_settings[self.guild_id] = {"start": start, "end": end}
                self.cog.participants[self.guild_id] = []  # 참가자 리스트 초기화

                await interaction.response.send_message(
                    f"신청 기간이 설정되었습니다!\n시작: {start}\n종료: {end}",
                    ephemeral=True
                )
            except ValueError:
                await interaction.response.send_message("날짜 형식이 잘못되었습니다. YYYY-MM-DD HH:MM 형식으로 입력해주세요.", ephemeral=True)

    @app_commands.command(name="신청시작", description="신청 기간을 설정합니다.")
    async def start_application(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("이 명령어는 서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        modal = self.ApplicationModal(self, interaction.guild.id)
        await interaction.response.send_modal(modal)

    @app_commands.command(name="참가신청", description="현재 신청 기간 중 참가 신청을 합니다.")
    async def apply(self, interaction: discord.Interaction):
        if interaction.guild is None:
            await interaction.response.send_message("이 명령어는 서버에서만 사용할 수 있습니다.", ephemeral=True)
            return

        guild_id = interaction.guild.id

        # 신청 기간 확인
        if guild_id not in self.event_settings:
            await interaction.response.send_message("신청 기간이 설정되지 않았습니다. 관리자가 먼저 신청 기간을 설정해야 합니다.", ephemeral=True)
            return

        now = datetime.now()
        event = self.event_settings[guild_id]
        if not (event["start"] <= now <= event["end"]):
            await interaction.response.send_message("현재는 신청 기간이 아닙니다.", ephemeral=True)
            return

        # 참가자 저장
        nickname = interaction.user.display_name
        try:
            year, name, game_id = nickname.split("/")
            self.participants[guild_id].append((name, game_id))
            await interaction.response.send_message(f"{name}님이 참가 신청을 완료했습니다!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("서버 닉네임이 '년도/이름/게임아이디' 형식이어야 합니다. 관리자에게 문의하세요", ephemeral=True)

    @commands.Cog.listener()
    async def on_ready(self):
        print("EventCog is ready!")


async def setup(bot):
    await bot.add_cog(EventCog(bot))
