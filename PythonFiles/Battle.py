from discord.ext import commands
import discord
import sqlite3
import csv
import random
from discord.ui import Button
from discord import ButtonStyle
from math import sqrt
from math import floor
from PythonFiles.Potions import GenericPotion
from PythonFiles.connections import connections
from PythonFiles.game import game
from PythonFiles.databasecode import databasecode 

class AttackButton(Button):
        def __init__(self, ctx, user_id, creature, rarity, item, message):
            super().__init__(style=ButtonStyle.green, label="Attack")
            self.ctx = ctx
            self.user_id = user_id
            self.creature = creature
            self.rarity = rarity
            self.item = item
            self.message = message

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == self.user_id:
                await interaction.response.defer()
                return await Battle.turn(self.ctx, self.user_id, self.creature, self.rarity, self.item, self.message, interaction)
                
class FleeButton(Button):
    def __init__(self, user_id):
        super().__init__(style=ButtonStyle.red, label="Flee")
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            conn = sqlite3.connect('characters.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM characters WHERE user_id = ?', (self.user_id,))
            player = cursor.fetchone()
            if player:
                cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (100, self.user_id))
                conn.commit()
            await interaction.response.send_message("You fled the encounter!")
            await interaction.message.delete()

class ConsumeButton(Button):
    def __init__(self, user_id, creature, rarity, message):
        super().__init__(style=ButtonStyle.blurple, label="Consume")
        self.user_id = user_id
        self.creature = creature
        self.rarity = rarity
        self.message = message

    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id:
            conn = sqlite3.connect('consumables.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM consumables')
            potions = cursor.fetchall()
            view = discord.ui.View()
            for potion in potions:
                if potion[9] == "T":  # Check if the potion can be used in combat
                    button = GenericPotion(self.user_id, potion[1], self.creature, self.rarity, self.message)
                    view.add_item(button)
            await interaction.response.send_message("Please click an available conusmable!", view=view)

            

class Battle(commands.Cog):
    
    async def turn(ctx, user_id, creature, rarity, item, message, interaction):
        conn = connections.conn
        cursor = conn.cursor()

        conn_activecreatures = sqlite3.connect('activecreatures.db')
        cursor_activecreatures = conn_activecreatures.cursor()

        # Fetch player data from the database
        cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()

        cursor_activecreatures.execute('SELECT * FROM activecreatures WHERE CID = ?', (creature[10],))
        creature = cursor_activecreatures.fetchone()

        cmax_hp = creature[2]
        ehp = creature[1]

        if player[2] > 0 and creature[1] > 0:
            scaler = random.randint(10, 15)/random.randint(10, 15)

            damage = Battle.attackScaler(user_id) * scaler
            ehp -= damage
            ehp = int(round(ehp))

            if(ehp < 0):
                ehp = 0

            cursor_activecreatures.execute('UPDATE activecreatures SET HP = ?, max_hp = ? WHERE name = ?', (ehp, cmax_hp, creature[0]))
            conn_activecreatures.commit()

            # Fetch updated creature values from the database
            cursor_activecreatures.execute('SELECT * FROM activecreatures WHERE CID = ?', (creature[10],))
            creature = cursor_activecreatures.fetchone()

            embed = Battle.fight_status(player, creature, rarity)
            await message.edit(content="Do you plan to attack or flee?", embed=embed)

            if(ehp <= 0):
                if(creature[1] == 0):
                    Battle.loot_drop(user_id, item)
                    print(creature[7])
                    Battle.update_player(user_id, creature[7], creature[3])
                    cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (player[3], user_id))
                    conn.commit()
                    await ctx.send("You win!")
                    await interaction.message.delete()
                return
            php = player[2]

            scaler = random.randint(10, 15)/random.randint(10, 15)
        
            cdmg = game.CCreature.creature_damage(creature[10])*scaler - player[5]/2
            php -= cdmg
            php = int(round(php))

            if(php < 0):
                php = 0

            cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (php, user_id))
            conn.commit()

            # Fetch updated player values from the database
            cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
            player = cursor.fetchone()

            embed = Battle.fight_status(player, creature, rarity)
            await message.edit(content="Do you plan to attack or flee?", embed=embed)

            if(php <= 0):
                if(player[2] == 0):
                    await ctx.send("You died!")
                    cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (player[3], user_id))
                    conn.commit()
                    await interaction.message.delete()
                return
        

            
    async def fight(ctx, user_id, creature, rarity, item):
        await ctx.send("fight program in progress")
        conn = sqlite3.connect('characters.db')
        #conn = connections.conn
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()

        embed = Battle.fight_status(player, creature, rarity)
        embed = embed
        message = await ctx.send(embed=embed)

        attack_button = AttackButton(ctx, user_id, creature, rarity, item, message)
        flee_button = FleeButton(user_id)
        consume_button = ConsumeButton(user_id, creature, rarity, message)
        view = discord.ui.View()
        view.add_item(attack_button)
        view.add_item(flee_button)
        view.add_item(consume_button)
        
        await ctx.send("Do you plan to attack or flee?", view=view)
                

    def attackScaler(user_id):
        conn = sqlite3.connect('characters.db')
        c = conn.cursor()
        c.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        rows = c.fetchone()
        level = rows[16]
        attack = rows[6]
        weapon_id = rows[9]
        damage = game.weapon.get_weapon_damage(weapon_id)

        return int((damage) + (level + attack * 0.5))
        
    def loot_drop(user_id, item):
        conn = sqlite3.connect('inventory.db')
        c = conn.cursor()
        c.execute('SELECT * FROM inventory WHERE user_id = ?', (user_id,))
        rows = c.fetchall()

        item_id = item[0]

        for row in rows:
            if not row[1]:
                c.execute("UPDATE inventory SET item_id = ? WHERE user_id = ? AND slot = ?", (item_id, user_id, row[2]))
                conn.commit()
                return "Item inserted into inventory"
        return "Inventory Full"
    
    def update_player(user_id, gold, XP):
        conn = sqlite3.connect('characters.db')
        c = conn.cursor()
        c.execute('SELECT * FROM characters WHERE user_id=?', (user_id,))
        rows = c.fetchone()
        old_level = rows[16]

        if rows:
            c.execute('UPDATE characters SET gold = ? WHERE user_id = ?', (rows[7] + gold, user_id))
            c.execute('UPDATE characters SET XP = ? WHERE user_id = ?', (rows[4] + XP, user_id))
            conn.commit()

            new_level = floor(0.1 * sqrt(rows[4]))
            if(new_level > old_level):
                c.execute('UPDATE characters SET level = ? WHERE user_id = ?', (new_level, user_id))
                conn.commit()

    def fight_status(player, creature, rarity):

        if(rarity == "A"):
            ctitle = "Advanced"
        elif(rarity == "G"):
            ctitle = "Greater"
        else:
            ctitle = "Common"

        embed = discord.Embed(title=f"Battle - {player[1]} vs. {ctitle} {creature[0]}", color=discord.Color.red())
        embed.add_field(name="Player HP", value=f"{player[2]}/{player[3]}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Add an empty field for spacing
        embed.add_field(name="\u00A0Enemy HP", value=f"{creature[1]}/{creature[2]}", inline=True)
        embed.add_field(name="Weapon Slots", value=game.weapon.get_weapon_name(player[9]), inline=True)
        return embed


async def setup(bot):
    await bot.add_cog(Battle())
