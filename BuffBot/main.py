import discord
from discord.ext import commands
import botconfig
from coins import Coin
from tax import Tax
import asyncio

client = discord.Client()
bot = commands.Bot(command_prefix='?')

startup_extensions = ["commands", "voice", "coins", "blackjack", "channel_mangement", "lottery", "tax", "holdem"]

token = 'NTcxNDY4OTI4MTkxMTY4NTEz.XMS_Mw.L_199C99W5jyAFSHEFPItowYl-4'
@bot.event
async def on_ready():
    print('Logged in as')
    print('------')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    tax = Tax(bot)
    tax_task = asyncio.ensure_future(tax.wealth_tax())

    coins = Coin(bot)
    await coins.give_coin()

    await tax_task
    await client.change_presence(game=discord.Game(name="My Prefix: ?"))





bot.run(token)

