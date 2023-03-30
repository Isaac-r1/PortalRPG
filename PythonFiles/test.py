import discord
from discord import message
from random import randint, random
import random
import sqlite3
from discord.ext import commands
from discord.ext.commands import bot
from discord.ext.commands.core import command


class test(commands.Cog):
    @commands.command()
    async def hello(self, ctx):
        await ctx.send("hello world")
    
    @commands.command()
    async def coinflip(self, ctx):
        randomN = randint(0,2)
        if(randomN == 1):
            await ctx.send("Heads")
        else:
            await ctx.send("Tails")

def setup(bot):
    bot.add_cog(test())