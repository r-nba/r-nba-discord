import config

import discord
from discord.ext import commands

import sys, traceback

def get_prefix(bot, message):

    prefixes = ['!']

    if not message.guild:
        return '?'

    return commands.when_mentioned_or(*prefixes)(bot, message)

initial_extensions = ['cogs.sidebar_image',
                      'cogs.game_channels']

bot = commands.Bot(command_prefix=get_prefix, description='r/nba discord bot')

if __name__ == '__main__':
    for extension in initial_extensions:
        try:
            bot.load_extension(extension)
        except Exception as e:
            print(f'Failed to load extension {extension}.', file=sys.stderr)
            traceback.print_exc()

@bot.event
async def on_ready():
    print(f'\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    await bot.change_presence(activity=discord.Game(name='as /u/brexbre'))
    print(f'Successfully logged in and booted...!')
    
bot.run(config.discord_token, bot=True, reconnect=True)
