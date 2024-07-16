import discord
from discord.ext import commands
from discord import ButtonStyle, SelectOption, ui, app_commands
from youtubesearchpython import VideosSearch
from yt_dlp import YoutubeDL
import asyncio
import json

SETTINGS_FILE = 'settings.json'

class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.mainEmbed = discord.Embed(title="재생목록에 노래를 추가해 보세요!", color=discord.Color(0x00FF00))
        self.mainEmbed.add_field(name="제작자", value="석순(seoksoon_)")
        self.mainEmbed.add_field(name="사용법", value="/play")
        self.defaultEmbed = self.mainEmbed
        self.mainMessages = {}  # 각 서버별 메시지 딕셔너리
        self.is_playing = {}   # 각 서버별 플레이 여부 딕셔너리
        self.is_paused = {}    # 각 서버별 일시정지 여부 딕셔너리
        self.channel = {}      # 각 서버별 채널 정보 딕셔너리
        self.vcs = {}         # 각 서버별 음성 클라이언트 딕셔너리
        self.music_queue = {}
        self.YDL_OPTIONS = {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
        }
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn',
        }
        self.ytdl = YoutubeDL(self.YDL_OPTIONS)
        asyncio.create_task(self.setup_message_and_main_message())


    async def setup_message_and_main_message(self):
        await self.bot.wait_until_ready()
        try:
            with open(SETTINGS_FILE, 'r') as f:
                message_data = json.load(f)

            for guild_id, data in message_data.items():
                channel_id = data.get('channel_id')
                main_message_id = data.get('message_id')

                if channel_id and main_message_id:
                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        try:
                            self.mainMessages[guild_id] = await channel.fetch_message(main_message_id)
                            await self.mainMessages[guild_id].edit(embed=self.mainEmbed, view=self.create_view(guild_id = None))
                            print(f"Main message updated successfully for guild {guild_id}.")
                        except discord.NotFound:
                            print(f"Main message not found for guild {guild_id}, creating a new one.")
                            self.mainMessages[guild_id] = await channel.send(embed=self.mainEmbed, view=self.create_view(guild_id = None))
                            self._save_main_message()  # 저장 추가
                    else:
                        print(f"Channel not found for guild {guild_id}.")
                else:
                    print(f"Message ID or Channel ID not found in settings for guild {guild_id}.")

        except FileNotFoundError:
            print(f"File '{SETTINGS_FILE}' not found. Using default settings.")
        except json.JSONDecodeError:
            print(f"Error decoding JSON from file '{SETTINGS_FILE}'. Using default settings.")

    def _save_main_message(self):
        message_data = {}
        for guild_id, message in self.mainMessages.items():
            message_data[guild_id] = {
                'message_id': message.id,
                'channel_id': message.channel.id,
            }
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(message_data, f, indent=4)

    def create_view(self, guild_id):
        view = ui.View()
        view.add_item(ui.Button(label="⏹️", style=ButtonStyle.danger, custom_id="stop"))
        view.add_item(ui.Button(label="⏸️", style=ButtonStyle.primary, custom_id="pause"))
        view.add_item(ui.Button(label="▶️", style=ButtonStyle.success, custom_id="resume"))
        view.add_item(ui.Button(label="⏭️", style=ButtonStyle.secondary, custom_id="skip"))
        view.add_item(self.create_select_menu(guild_id))
        return view

    def create_select_menu(self,guild_id):
        options = []
        if guild_id==None or not self.music_queue[guild_id]:
            options.append(SelectOption(label="재생 목록이 비어 있습니다.", value="empty", default=True))
            select = ui.Select(placeholder="재생 목록이 비어 있습니다.", options=options, custom_id="select_song", disabled=True)
        else:
            for idx, (song, requester) in enumerate(self.music_queue.get(guild_id)):
                options.append(SelectOption(label=song['title'], description=f"Requested by {requester.display_name}", value=str(idx)))
            select = ui.Select(placeholder="곡 선택", options=options, custom_id="select_song")
        return select

    async def update_main_message(self, guild_id):
        try:
            message = self.mainMessages.get(guild_id)
            if message:
                # Ensure bot has permissions to edit messages
                if message.guild.me.guild_permissions.manage_messages:
                    await message.edit(embed=self.mainEmbed, view=self.create_view(guild_id))
                    print("Main message updated successfully.")
                else:
                    print("Bot does not have permission to edit messages.")
            else:
                print(f"Main message not found for guild {guild_id}")
        except discord.errors.Forbidden:
            print("Bot does not have permission to edit this message.")
        except Exception as e:
            print(f"Unexpected error: {e}")

    @app_commands.command(name="set", description="재생목록 정보를 표시할 채널을 설정합니다.")
    async def set_channel(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        self.channel[guild_id] = interaction.channel.id
        self.mainMessages[guild_id] = await interaction.channel.send(embed=self.mainEmbed, view=self.create_view(guild_id=None))

        # mainMessage의 ID를 저장
        self._save_main_message()
        await interaction.response.send_message(f"#{interaction.channel.id} 채널로 설정되었습니다!", ephemeral=True)

    def search_yt(self, item):
        if item.startswith("https://"):
            title = self.ytdl.extract_info(item, download=False)["title"]
            return {'source': item, 'title': title}
        search = VideosSearch(item, limit=1)
        return {
            'source': search.result()["result"][0]["link"],
            'title': search.result()["result"][0]["title"],
            'thumbnail': search.result()["result"][0]["thumbnails"][0]["url"],
        }

    async def song_update(self, guild_id, data, requester_name, next_song=None):
        title = data['title']
        length_seconds = data['duration']
        length_minutes = length_seconds // 60
        length_seconds %= 60
        embed = discord.Embed(title="현재 재생 중", color=discord.Color(0xF3F781))
        embed.add_field(name="제목", value=f"{title}")
        embed.add_field(name="길이", value=f"{length_minutes}:{length_seconds:02}")
        embed.add_field(name="요청자", value=f"{requester_name}")
        embed.set_image(url=data['thumbnail'])
        if next_song:
            next_title = next_song['title']
            embed.add_field(name="다음 곡", value=f"{next_title}", inline=False)
        self.mainEmbed = embed
        await self.update_main_message(guild_id)

    async def play_next(self):
        for guild_id, vcs in self.vcs.items():
            if vcs and guild_id in self.music_queue and len(self.music_queue[guild_id]) > 0:
                self.is_playing[guild_id] = True
                song_data = self.music_queue[guild_id][0][0]
                requester_name = self.music_queue[guild_id][0][1].display_name
                self.music_queue[guild_id].pop(0)
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(song_data['source'], download=False))
                song_url = data['url']
                next_song = self.music_queue[guild_id][0][0] if len(self.music_queue[guild_id]) > 0 else None
                vcs.play(discord.FFmpegPCMAudio(song_url, **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
                await self.song_update(guild_id, data, requester_name, next_song)
            else:
                self.is_playing[guild_id] = False
                message = self.mainMessages.get(guild_id)
                await message.edit(embed = self.defaultEmbed)

    @app_commands.command(name="play", description="Plays a selected song from youtube")
    async def play(self, interaction: discord.Interaction, *, title_or_url: str):
        try:
            guild_id = str(interaction.guild.id)
            voice_channel = interaction.user.voice.channel
        except AttributeError:
            await interaction.response.send_message('음성채널에 입장한 후 사용해 주세요.', ephemeral=True)
            return

        if self.is_paused.get(guild_id):
            self.vcs[guild_id].resume()
        else:
            song = self.search_yt(title_or_url)
            if type(song) == type(True):
                await interaction.response.send_message('음원 다운로드 실패. 다른 키워드로 다시 시도해 주세요', ephemeral=True)
            else:
                if guild_id not in self.music_queue:
                    self.music_queue[guild_id] = []
                self.music_queue[guild_id].append([song, interaction.user])
                await interaction.response.send_message(f"'{song['title']}' 재생목록에 추가되었습니다.", ephemeral=True)
                if not self.is_playing.get(guild_id):
                    await self.play_music(interaction)
                else:
                    await self.update_main_message(guild_id)

    async def play_music(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        if len(self.music_queue[guild_id]) > 0:
            self.is_playing[guild_id] = True
            song_data = self.music_queue[guild_id][0][0]
            voice_channel = self.music_queue[guild_id][0][1].voice.channel
            requester_name = self.music_queue[guild_id][0][1].display_name
            if self.vcs.get(guild_id) == None or not self.vcs[guild_id].is_connected():
                self.vcs[guild_id] = await voice_channel.connect()
                if self.vcs[guild_id] == None:
                    await interaction.response.send_message('음성 채널에 연결할 수 없습니다.', ephemeral=True)
                    return
            else:
                await self.vcs[guild_id].move_to(voice_channel)
            self.music_queue[guild_id].pop(0)

            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(song_data['source'], download=False))
            song_url = data['url']
            next_song = self.music_queue[guild_id][0][0] if len(self.music_queue[guild_id]) > 0 else None
            self.vcs[guild_id].play(discord.FFmpegPCMAudio(song_url, **self.FFMPEG_OPTIONS), after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop))
            await self.song_update(guild_id, data, requester_name, next_song)
        else:
            self.is_playing[guild_id] = False

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data['custom_id']
            guild_id = str(interaction.guild.id)

            if custom_id == 'stop':
                if self.vcs.get(guild_id):
                    self.vcs[guild_id].stop()
                    self.is_playing[guild_id] = False
                    self.music_queue[guild_id] = []
                    await self.vcs[guild_id].disconnect()
                    await self.mainMessages[guild_id].edit(embed=self.defaultEmbed, view=self.create_view(guild_id))
                    await interaction.response.send_message('재생을 중지합니다.', ephemeral=True)
                    return
                else:
                    await interaction.response.send_message('재생 중 일때만 정지할 수 있습니다.', ephemeral=True)
                    return

            elif custom_id == 'pause':
                if self.vcs.get(guild_id) and self.vcs[guild_id].is_playing():
                    self.vcs[guild_id].pause()
                    self.is_paused[guild_id] = True
                    await interaction.response.send_message('재생을 일시정지합니다.', ephemeral=True)
                    return
                else:
                    await interaction.response.send_message('재생 중 일때만 일시정지할 수 있습니다.', ephemeral=True)
                    return

            elif custom_id == 'resume':
                if self.vcs.get(guild_id) and self.vcs[guild_id].is_paused():
                    self.vcs[guild_id].resume()
                    self.is_paused[guild_id] = False
                    await interaction.response.send_message('다시 재생합니다.', ephemeral=True)
                    return
                else:
                    await interaction.response.send_message('일시정지 중이 아닙니다.', ephemeral=True)
                    return

            elif custom_id == 'skip':
                if self.vcs.get(guild_id) and self.vcs[guild_id].is_playing():
                    self.vcs[guild_id].stop()
                    await interaction.response.send_message('다음 곡을 재생합니다.', ephemeral=True)
                    return
                else:
                    await interaction.response.send_message('재생 중 일때만 스킵할 수 있습니다.', ephemeral=True)
                    return

            elif custom_id == 'select_song':
                selected_index = int(interaction.data['values'][0])
                if selected_index < len(self.music_queue.get(guild_id, [])):
                    self.music_queue[guild_id] = self.music_queue[guild_id][selected_index:] + self.music_queue[guild_id][:selected_index]
                    if self.vcs.get(guild_id):
                        self.vcs[guild_id].stop()
                    await interaction.response.send_message('선택한 곡으로 건너뜁니다.', ephemeral=True)
                    return
                else:
                    return

            await self.update_main_message(guild_id)  # 추가된 코드: 업데이트

async def setup(bot):
    await bot.add_cog(music_cog(bot))
