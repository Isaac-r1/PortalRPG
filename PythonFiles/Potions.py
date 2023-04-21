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
from PythonFiles.game import game
from PythonFiles.connections import connections
from discord.ui import Button
from discord import ButtonStyle

class GenericPotion(Button):
    def __init__(self, user_id, name, creature, rarity, message):
        super().__init__(style=ButtonStyle.blurple, label=name)
        self.user_id = user_id
        self.name = name
        self.creature = creature
        self.rarity = rarity
        self.message = message
    
    async def callback(self, interaction: discord.Interaction):

        if interaction.user.id == self.user_id:
            if(self.name == "Elixir of Vitality"):
                if Potions.use_Health_Potion(self.user_id) is False:
                    await interaction.response.send_message("You have no " + self.name + "!")
                    await interaction.message.delete()
                else:
                    conn = connections.conn
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM characters WHERE user_id = ?', (self.user_id,))
                    player = cursor.fetchone()
                    embed = Potions.fight_status(player, self.creature, self.rarity)
                    await self.message.edit(content="Do you plan to attack or flee?", embed=embed)

            await interaction.response.send_message("You consumed " + self.name + "!")
            await interaction.message.delete()
            
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
        with sqlite3.connect('c_inventory.db') as conni:
            ci = conni.cursor()
            for slot in range(1,9):
                ci.execute('SELECT PID, current_stack FROM c_inventory WHERE slot = ? AND user_id = ?', (slot, user_id))
                crow = ci.fetchone()
                if(crow[0] == 1):
                    with sqlite3.connect('characters.db') as conn:
                        c = conn.cursor()
                        c.execute('SELECT HP FROM characters WHERE user_id = ?', (user_id,))
                        row = c.fetchone()
                        newHP = row[0] + 30
                        if(newHP > 100):
                            newHP = 100
                        c.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (newHP, user_id))
                        conn.commit()
                        if crow[1] - 1 == 0:
                            ci.execute('UPDATE c_inventory SET PID = NULL, current_stack = 0 WHERE slot = ? AND user_id = ?', (slot, user_id))
                        else:
                            ci.execute('UPDATE c_inventory SET current_stack = ? WHERE slot = ? AND user_id = ?', (crow[1] - 1, slot, user_id))
                        conni.commit()
                        return True
            return False

    def fight_status(player, creature, rarity):

        if(rarity == "A"):
            ctitle = "Advanced"
        elif(rarity == "G"):
            ctitle = "Greater"
        else:
            ctitle = "Common"

        conn_activecreatures = sqlite3.connect('activecreatures.db')
        cursor_activecreatures = conn_activecreatures.cursor()
        cursor_activecreatures.execute('SELECT * FROM activecreatures WHERE CID = ?', (creature[10],))
        creature = cursor_activecreatures.fetchone()

        embed = discord.Embed(title=f"Battle - {player[1]} vs. {ctitle} {creature[0]}", color=discord.Color.red())
        embed.add_field(name="Player HP", value=f"{player[2]}/{player[3]}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Add an empty field for spacing
        embed.add_field(name="\u00A0Enemy HP", value=f"{creature[1]}/{creature[2]}", inline=True)
        embed.add_field(name="Weapon Slots", value=game.weapon.get_weapon_name(player[9]), inline=True)
        return embed




                        



async def setup(bot):
    await bot.add_cog(Potions())
