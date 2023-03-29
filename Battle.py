from discord.ext import commands
import discord
import sqlite3
import csv
import random
from game import game
from databasecode import databasecode 

class Battle(commands.Cog):
    async def fight(ctx, user_id, creature):
        await ctx.send("fight program in progress")
        conn = sqlite3.connect('characters.db')
        cursor = conn.cursor()

        conn1 = sqlite3.connect('creatures.db')
        cursor1 = conn1.cursor()

        cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()

        embed = Battle.fight_status(player, creature)
        embed = embed
        await ctx.send(embed = embed)

        while(player[2] > 0 and creature[1] > 0):
            await ctx.send("Do you plan to attack or flee? type A or F")

            def check(message):
                return message.author == ctx.author and message.channel == ctx.channel
            
            msg = await ctx.bot.wait_for("message", check=check)
            if(msg.content.lower() == "a"):
                ehp = creature[1]

                damage = game.weapon.get_weapon_damage(player[9])
                ehp -= damage

                cursor1.execute('UPDATE creatures SET HP = ? WHERE name = ?', (ehp, creature[0]))
                conn1.commit()

                # Fetch updated creature values from the database
                cursor1.execute('SELECT * FROM creatures WHERE name = ?', (creature[0],))
                creature = cursor1.fetchone()

                await ctx.send("You attacked the enemy")
                php = player[2] 
                cdmg = game.CCreature.creature_damage(creature[0])

                php -= cdmg

                cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (php, user_id))
                conn.commit()

                # Fetch updated player values from the database
                cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
                player = cursor.fetchone()

                embed = Battle.fight_status(player, creature)
                await ctx.send(embed = embed)
                
            elif(msg.content.lower() == "f"):
                await ctx.send("You fled the encounter!")
                break
            else:
                await ctx.send("Invalid!")

        if(player[2] < 0):
            await ctx.send("You died!")
        if(creature[1] < 0):
            await ctx.send("You win!")

        cursor.execute('UPDATE characters SET HP = ? WHERE user_id = ?', (player[3], user_id))
        conn.commit()

        # Reset the HP of the creature to their maximum HP
        cursor1.execute('UPDATE creatures SET HP = ? WHERE name = ?', (creature[2], creature[0]))
        conn1.commit()
        



    def fight_status(player, creature):
        embed = discord.Embed(title=f"Battle - {player[1]} vs. {creature[0]}", color=discord.Color.red())
        embed.add_field(name="Player HP", value=f"{player[2]}/{player[3]}", inline=True)
        embed.add_field(name="\u200b", value="\u200b", inline=True) # Add an empty field for spacing
        embed.add_field(name="\u00A0Enemy HP", value=f"{creature[1]}/{creature[2]}", inline=True)
        embed.add_field(name="Weapon Slots", value=game.weapon.get_weapon_name(player[9]), inline=True)
        return embed



def setup(bot):
    bot.add_cog(Battle())
