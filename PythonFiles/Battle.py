from discord.ext import commands
import discord
import sqlite3
import csv
import random
from discord.ui import Button
from discord import ButtonStyle
from math import sqrt
from math import floor
from PythonFiles.connections import connections
from PythonFiles.game import game
from PythonFiles.databasecode import databasecode 

class AttackButton(Button):
        def __init__(self, ctx, user_id, creature, rarity, item):
            super().__init__(style=ButtonStyle.green, label="Attack")
            self.ctx = ctx
            self.user_id = user_id
            self.creature = creature
            self.rarity = rarity
            self.item = item

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == self.user_id:
                await Battle.turn(self.ctx, self.user_id, self.creature, self.rarity)
                await interaction.response.send_message("You clicked the Attack button!")
                

class FleeButton(Button):
        def __init__(self, user_id):
            super().__init__(style=ButtonStyle.red, label="Flee")
            self.user_id = user_id

        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id == self.user_id:
                await interaction.response.send_message("You fled the encounter!")
                conn = sqlite3.connect('characters.db')
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM characters WHERE user_id = ?', (self.user_id,))
                player = cursor.fetchone()
                if player:
                    cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (player[2], self.user_id))
                    conn.commit()

class Battle(commands.Cog):
    
    async def turn(ctx, user_id, creature, rarity):
        conn = connections.conn
        cursor = conn.cursor()

        conn1 = connections.conn1
        cursor1 = conn1.cursor()

        # Fetch player data from the database
        cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()

        cmax_hp = creature[2]
        ehp = creature[1]

        while player[2] > 0 and creature[1] > 0:
            scaler = random.randint(10, 15)/random.randint(10, 15)

            damage = Battle.attackScaler(user_id) * scaler
            print(damage)
            ehp -= damage
            ehp = int(round(ehp))

            if(ehp < 0):
                ehp = 0

            cursor1.execute('UPDATE creatures SET HP = ?, max_hp = ? WHERE name = ?', (ehp, cmax_hp, creature[0]))
            conn1.commit()

            # Fetch updated creature values from the database
            cursor1.execute('SELECT * FROM creatures WHERE name = ?', (creature[0],))
            creature = cursor1.fetchone()

            if(ehp <= 0):
                return

            await ctx.send("You attacked the enemy")
            php = player[2]

            scaler = random.randint(10, 15)/random.randint(10, 15)
                            
            cdmg = game.CCreature.creature_damage(creature[0])*scaler - player[5]/3
            php -= cdmg
            php = int(round(php))

            if(php < 0):
                php = 0

            cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (php, user_id))
            conn.commit()

            # Fetch updated player values from the database
            cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
            player = cursor.fetchone()

            if(php <= 0):
                return

            embed = Battle.fight_status(player, creature, rarity)
            await ctx.send(embed = embed)
            
    async def fight(ctx, user_id, creature, rarity, item):
        await ctx.send("fight program in progress")
        conn = sqlite3.connect('characters.db')
        #conn = connections.conn
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()

        embed = Battle.fight_status(player, creature, rarity)
        embed = embed
        await ctx.send(embed = embed)

        attack_button = AttackButton(ctx, user_id, creature, rarity, item)
        flee_button = FleeButton(user_id)
        view = discord.ui.View()
        view.add_item(attack_button)
        view.add_item(flee_button)
        await ctx.send("Do you plan to attack or flee?", view=view)
                
            
        if(player[2] == 0):
            await ctx.send("You died!")

        if(creature[1] == 0):
            Battle.loot_drop(user_id,item)
            print(creature[7])
            Battle.update_player(user_id, creature[7], creature[3])
            await ctx.send("You win!")
        
        cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (player[3], user_id))
        conn.commit()
        conn.close()

    def attackScaler(user_id):
        conn = sqlite3.connect('characters.db')
        c = conn.cursor()
        c.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        rows = c.fetchone()
        level = rows[16]
        attack = rows[6]
        weapon_id = rows[9]
        damage = game.weapon.get_weapon_damage(weapon_id)

        return int((damage/(21 - level)) + (level * attack * 0.5))
        
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
