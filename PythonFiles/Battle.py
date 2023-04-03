from discord.ext import commands
import discord
import sqlite3
import csv
import random
from PythonFiles.game import game
from PythonFiles.databasecode import databasecode 

class Battle(commands.Cog):
    async def fight(ctx, user_id, creature, rarity, item):
        await ctx.send("fight program in progress")
        conn = sqlite3.connect('characters.db')
        cursor = conn.cursor()

        conn1 = sqlite3.connect('creatures.db')
        cursor1 = conn1.cursor()

        cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()

        embed = Battle.fight_status(player, creature, rarity)
        embed = embed
        await ctx.send(embed = embed)

        while(player[2] > 0 and creature[1] > 0):
            await ctx.send("Do you plan to attack or flee? type A or F")

            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel
            
            msg = await ctx.bot.wait_for("message", check=check)
            if(msg.content.lower() == "a"):
                ehp = creature[1]

                scaler = random.randint(10, 15)/random.randint(10, 15)

                damage = game.weapon.get_weapon_damage(player[9])  * scaler
                ehp -= damage
                ehp = int(round(ehp))

                if(ehp < 0):
                    ehp = 0

                cursor1.execute('UPDATE creatures SET HP = ? WHERE name = ?', (ehp, creature[0]))
                conn1.commit()

                # Fetch updated creature values from the database
                cursor1.execute('SELECT * FROM creatures WHERE name = ?', (creature[0],))
                creature = cursor1.fetchone()

                if(ehp <= 0):
                    break

                await ctx.send("You attacked the enemy")
                php = player[2]

                scaler = random.randint(10, 15)/random.randint(10, 15)
                
                cdmg = game.CCreature.creature_damage(creature[0])*scaler
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
                    break

                embed = Battle.fight_status(player, creature, rarity)
                await ctx.send(embed = embed)
                
            elif(msg.content.lower() == "f"):
                await ctx.send("You fled the encounter!")
                break
            else:
                await ctx.send("Invalid!")
        
        embed = Battle.fight_status(player, creature, rarity)
        await ctx.send(embed = embed)
            
        if(player[2] == 0):
            cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (player[3], user_id))
            conn.commit()

            # Reset the HP of the creature to their maximum HP
            cursor1.execute('UPDATE creatures SET HP = ? WHERE name = ?', (creature[2], creature[0]))
            conn1.commit()
            await ctx.send("You died!")

        if(creature[1] == 0):
            Battle.loot_drop(user_id,item)
            cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (player[3], user_id))
            conn.commit()

            # Reset the HP of the creature to their maximum HP
            cursor1.execute('UPDATE creatures SET HP = ? WHERE name = ?', (creature[2], creature[0]))
            conn1.commit()
            await ctx.send("You win!")
            

        

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



def setup(bot):
    bot.add_cog(Battle())
