import asyncio
import os
import discord
from discord.ext import commands

# === 경로 설정 ===
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # main.py가 있는 디렉토리
COGS_DIR = os.path.join(BASE_DIR, "cogs")
TOKEN_PATH = os.path.join(BASE_DIR, "discord_token.txt")

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    try:
        synced_commands = await bot.tree.sync()
        print(f"synced {len(synced_commands)} commands loaded")
    except Exception as e:
        print("error with syncing app_commands ", e)

    print(f'Logged in as {bot.user}')


async def load_extensions():
    # COGS_DIR 안의 .py 파일들을 전부 확장으로 로드
    for file in os.listdir(COGS_DIR):
        if file.endswith(".py"):
            ext_name = file[:-3]  # .py 제거
            await bot.load_extension(f"cogs.{ext_name}")


@bot.command(name="reload")
async def reload_extension(ctx, extension=None):
    # 특정 확장만 reload
    if extension is not None:
        await unload_function(extension)
        try:
            await bot.load_extension(f"cogs.{extension}")
        except commands.ExtensionNotFound:
            await ctx.send(f":x: '{extension}'을(를) 파일을 찾을 수 없습니다!")
        except (commands.NoEntryPointError, commands.ExtensionFailed):
            await ctx.send(f":x: '{extension}'을(를) 불러오는 도중 에러가 발생했습니다!")
        else:
            await ctx.send(f":white_check_mark: '{extension}'을(를) 다시 불러왔습니다!")
        return

    # 전체 reload
    for filename in os.listdir(COGS_DIR):
        if filename.endswith(".py"):
            cog_name = filename[:-3]
            await unload_function(cog_name)
            try:
                await bot.load_extension(f"cogs.{cog_name}")
            except commands.ExtensionNotFound:
                await ctx.send(f":x: '{cog_name}'을(를) 파일을 찾을 수 없습니다!")
            except (commands.NoEntryPointError, commands.ExtensionFailed):
                await ctx.send(f":x: '{cog_name}'을(를) 불러오는 도중 에러가 발생했습니다!")

    await ctx.send(":white_check_mark: reload 작업을 완료하였습니다!")


@bot.command(name="unload")
async def unload_extension(ctx, extension=None):
    if extension is not None:
        await unload_function(extension)
        await ctx.send(f":white_check_mark: {extension} 기능을 종료했습니다")
    else:
        await unload_function(None)
        await ctx.send(f":white_check_mark: 모든 확장기능을 종료했습니다.")


async def unload_function(extension=None):
    # 특정 확장만 unload
    if extension is not None:
        try:
            await bot.unload_extension(f"cogs.{extension}")
        except (commands.ExtensionNotLoaded, commands.ExtensionNotFound):
            pass
        return

    # 전체 unload
    for file in os.listdir(COGS_DIR):
        if file.endswith(".py"):
            cog_name = file[:-3]
            try:
                await bot.unload_extension(f"cogs.{cog_name}")
            except (commands.ExtensionNotLoaded, commands.ExtensionNotFound):
                pass


async def main():
    async with bot:
        # cogs 먼저 로드
        await load_extensions()

        # 토큰 읽기
        with open(TOKEN_PATH, "r", encoding="utf-8") as f:
            token = f.readline().strip()

        # 봇 스타트
        await bot.start(token)


if __name__ == "__main__":
    asyncio.run(main())
