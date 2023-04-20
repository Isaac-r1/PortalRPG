import enum, random, sys
import csv
import sqlite3
from copy import deepcopy
import random
import itertools
from random import randint, random
import discord
from discord.ext import commands
from discord.ext.commands import bot
from discord.ext.commands.core import command
from PythonFiles.databasecode import databasecode

class Potions(commands.Cog):

    def create_c_inventory(user_id):
        with sqlite3.connect('c_inventory.db') as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='c_inventory'")

            if c.fetchone() is None: #user_id will be used to access the inventory of a player, item_id is to insert an item to inventory at slot
                c.execute('''CREATE TABLE c_inventory(
                    user_id INTEGER,
                    PID INTEGER,
                    slot INTEGER,
                    current_stack INTEGER DEFAULT 0,
                    PRIMARY KEY (user_id, slot),
                    FOREIGN KEY (PID) REFERENCES consumables(PID),
                    CHECK (slot >= 1 AND slot <= 8)
                )''')

            max_slot = 8
            for slot in range(1, max_slot+1):
                c.execute("INSERT OR IGNORE INTO c_inventory (user_id, slot) VALUES (?, ?)", (user_id, slot))

    @commands.command()
    async def c_inv(self, ctx, page:int = 1):        
        user_id = ctx.message.author.id

        if(page > 7):
            await ctx.send("size too big")
            return

        with sqlite3.connect('characters.db') as cconn:
            cc = cconn.cursor()
            cc.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
            rows = cc.fetchall()

            if not rows:
                await ctx.send("Create a new character with `!create`")
                return

        with sqlite3.connect('c_inventory.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM c_inventory WHERE user_id = ?', (user_id,))
            rows = c.fetchall()

            if not rows:
                await ctx.send("Your consumables inventory is empty.")
                return

            inventory_grid = ["\u200b"] * 8
            for row in rows:
                slot = row[2] - 1
                with sqlite3.connect('consumables.db') as conn_items:
                    c_items = conn_items.cursor() 
                    c_items.execute('SELECT name, stack FROM consumables WHERE PID = ?', (row[1],))
                    c_row = c_items.fetchone()
                    c_name = c_row[0] if c_row is not None else "empty slot"
                    stack_count = f" ({row[3]})" if row[3] and row[3] > 0 else ""
                    inventory_grid[slot] = f"{c_name[:20]}{stack_count}"

            embed = discord.Embed(title=f"{ctx.author}'s consumables {page+1}-{page+8}")
            embed.description = "\n".join([str(item) for item in inventory_grid[page:page+9]])

            await ctx.send(embed=embed)

    def use_Health_Potion(user_id):
        with sqlite3.connect('characters.db') as conn:
            c = conn.cursor()
            c.execute('SELECT HP FROM characters WHERE user_id = ?', (user_id,))
            row = c.fetchone()
            oldHP = row[0]
            c.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (oldHP + 30, user_id))
            



async def setup(bot):
    await bot.add_cog(Potions())
