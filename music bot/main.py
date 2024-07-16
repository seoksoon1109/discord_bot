import asyncio, os
import discord
from discord.ext import commands

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents= intents)


@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online)
    try:
        synced_commands = await bot.tree.sync()
        print(f"synced{len(synced_commands)}commands loaded")
    except Exception as e:
        print("error with syncing app_commands ", e)
    
    print(f'Logged in as {bot.user}')

async def load_extensions():
    for file in os.listdir("cogs"):
        if file.endswith(".py"):
            await bot.load_extension(f"cogs.{file[:-3]}")


@bot.command(name="reload")
async def reload_extension(ctx, extension=None):
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
    else:
        for filename in os.listdir("cogs"):
            if filename.endswith(".py"):
                await unload_function(filename[:-3])
                try:
                    await bot.load_extension(f"cogs.{filename[:-3]}")
                except commands.ExtensionNotFound:
                    await ctx.send(f":x: '{filename[:-3]}'을(를) 파일을 찾을 수 없습니다!")
                except (commands.NoEntryPointError, commands.ExtensionFailed):
                    await ctx.send(f":x: '{filename[:-3]}'을(를) 불러오는 도중 에러가 발생했습니다!")
        await ctx.send(":white_check_mark: reload 작업을 완료하였습니다!")

@bot.command(name = "unload")
async def unload_extension(ctx, extension=None):
    if extension is not None:
        await unload_function(extension)
        await ctx.send(f":white_check_mark: {extension}기능을 종료했습니다")
    else:
        await unload_function(None)
        await ctx.send(f":white_check_mark: 모든 확장기능을 종료했습니다.")



async def unload_function(extension=None):
    if extension is not None:
        try:
            await bot.unload_extension(f"cogs.{extension}")
        except (commands.ExtensionNotLoaded, commands.ExtensionNotFound):
            pass
    else:
        for file in os.listdir("cogs"):
            if file.endswith(".py"):
                try:
                    await bot.unload_extension(f"cogs.{file[:-3]}")
                except (commands.ExtensionNotLoaded, commands.ExtensionNotFound):
                    pass


async def main():
    async with bot:
        await load_extensions()
        file = open("discord_token.txt")
        token = file.readline()
        file.close()
        await bot.start(token)

asyncio.run(main()) 