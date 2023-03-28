from discord.ext import commands
import discord
import sqlite3
import csv
from config import TOKEN
import random
from game import game
from databasecode import databasecode

bot = commands.Bot(command_prefix = "!")

databasecode.create_player_weapons_table()

conn = sqlite3.connect('characters.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='characters'")
table_exists = cursor.fetchone() is not None

if not table_exists:
    cursor.execute('''CREATE TABLE characters (
        id INTEGER,
        name TEXT,
        HP INTEGER,
        max_HP INTEGER,
        XP INTEGER,
        defense INTEGER,
        attack INTEGER,
        gold INTEGER,
        inventory TEXT,
        w INTEGER,
        armor TEXT,
        accessory TEXT,
        ctype TEXT,
        battling INTEGER,
        mode TEXT,
        region TEXT,
        level INTEGER,
        user_id BIGINT PRIMARY KEY 
    )''')

def Wchoice(chtype, user_id):
    if(chtype == "mage"):
        WID = 19
    elif(chtype == "archer"):
        WID = 10
    elif(chtype == "swordsman"):
        WID = 1
    else:
        
        raise ValueError("Not a valid class!")
        
    # Insert the weapon into the database
    databasecode.insert_player_weapon(user_id, WID, 1)
    
    print(f"Class: {chtype}, WID: {WID}")
    return WID

@bot.command(name = "mode")
async def mode(ctx, new_mode: str):
    user_id = ctx.message.author.id
    if not (new_mode == "ADVENTURE" or new_mode == "ATHOME"):
        await ctx.send("invalid mode")
        raise commands.CommandError("invalid mode!")
    
    if game.Character.getMode(user_id) == new_mode:
        await ctx.send("You're already in this state!")
        raise commands.CommandError("Invalid mode!")
    
    game.Character.changeMode(new_mode, user_id)
    await ctx.send("Mode changed to " + new_mode + "!")

@bot.command(name = "region")
async def region(ctx, new_region: str):
    user_id = ctx.message.author.id

    if game.Character.getMode(user_id) != "ADVENTURE":
        await ctx.send("Change your mode to ADVENTURE!")
        raise commands.CommandError("Invalid mode")

    if new_region not in ["tundra", "ocean", "forest", "swamp", "mountains"]:
        await ctx.send("invalid region")
        raise commands.CommandError("invalid region!")

    game.Character.changeRegion(new_region, user_id)  
    await ctx.send("Region changed to " + new_region + "!")

@bot.command(name = "hunt")
async def hunt(ctx):
    user_id = ctx.message.author.id

    if game.Character.getMode(user_id) != "ADVENTURE":
        await ctx.send("Change your mode to ADVENTURE to hunt!")
        raise commands.CommandError("Invalid mode")

    region = game.Character.getRegion(user_id)
    level = game.Character.getLevel(user_id)
    creature = game.CCreature.spawnCreature(region, level)
    await ctx.send("An encounter has spawned!")
    if creature:
        embed = discord.Embed(title=f"{creature[0]} Status", color=discord.Color.green())
        embed.add_field(name="HP", value=f"{creature[1]}/{creature[2]}", inline=True)
        embed.add_field(name="XP", value=creature[3], inline=True)
        embed.add_field(name="Defense", value=creature[4], inline=True)
        embed.add_field(name="Damage", value=creature[5], inline=True)
        embed.add_field(name="Attack", value=creature[6], inline=True)
        embed.add_field(name="Gold", value=creature[7], inline=True)
        await ctx.send(embed=embed)

    await ctx.send("Do you wish to battle your encounter?")
    

@bot.command(name = "create")
async def create(ctx, chtype: str, name: str):
    user_id = ctx.message.author.id
    
    
    if not (chtype == "mage" or chtype == "archer" or chtype == "swordsman"):
        await ctx.send("please pick one of the three following classes: mage, archer, swordsman then provide a name!")
        raise commands.CommandError("Not a valid class!")
    
    

    cursor.execute('SELECT * FROM characters WHERE id = ?', (user_id,))
    result = cursor.fetchone()

    if result is None:
        new_character = game.Character(name=name, HP=100, max_HP=100, XP=0, defense=0, attack=3, gold=10, inventory= "Empty", w = Wchoice(chtype, user_id), armor = None, accessory = None, ctype=chtype, battling=False, mode="AT HOME", region=None,  level=1, user_id=user_id)
        cursor.execute('INSERT INTO characters (name, HP, max_HP, XP, defense, attack, gold, inventory, w, armor, accessory, ctype, battling, mode, region, level, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (new_character.name, new_character.HP, new_character.max_HP, new_character.XP, new_character.defense, new_character.attack, int(new_character.gold), new_character.inventory, new_character.w, new_character.armor, new_character.accessory, new_character.ctype, new_character.battling, new_character.mode, new_character.region, new_character.level, new_character.user_id))
        conn.commit()
        await ctx.send("Your character, " + name + ",has been created, type: " + chtype)
    else:
        raise commands.CommandError("You already own an account!")

@bot.command(name = "status")
async def status(ctx):
    user_id = ctx.message.author.id
    cursor.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    if row:
        embed = discord.Embed(title=f"{row[1]}'s Status", color=0x00ff00)
        embed.add_field(name="HP", value=f"{row[2]}", inline=True)
        embed.add_field(name="Max_HP", value=f"{row[3]}", inline=True)
        embed.add_field(name="XP", value=row[4], inline=True)
        embed.add_field(name="Defense", value=row[5], inline=True)
        embed.add_field(name="Attack", value=row[6], inline=True)
        embed.add_field(name="Gold", value=row[7], inline=True)
        embed.add_field(name="Inventory", value=row[8], inline=False)
        embed.add_field(name="Weapon Slots", value=get_weapon_name(row[9]), inline=True)
        embed.add_field(name="Armor", value=row[10], inline=True)
        embed.add_field(name="Accessory", value=row[11], inline=True)
        embed.add_field(name="Class", value=row[12], inline=True)
        embed.add_field(name="Mode", value=row[14], inline=False)
        embed.add_field(name="Region", value=row[15], inline=True)
        embed.add_field(name="Level", value=row[16], inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send("You don't have a character yet. Use `!create` to create one.")


def get_weapon_name(WID):
    with sqlite3.connect('weapons.db') as conn:
        c = conn.cursor()
        print("Executing query with WID:", WID)
        c.execute('SELECT name FROM weapons WHERE WID = ?', (WID,))
        result = c.fetchone()
        if result:
            return result[0]
        else:
            return "Unknown Weapon"

@bot.command(name="weaponInfo")
async def weaponInfo(ctx, WID: int):
    try:
        with sqlite3.connect('weapons.db') as conn:
            c = conn.cursor()
            c.execute('SELECT * FROM weapons WHERE WID = ?', (WID,))
            row = c.fetchone()
            if row:
                embed = discord.Embed(title=f"{row[0]}'s Information", color=0x00ff00)
                embed.add_field(name="rarity", value=f"{row[1]}", inline=True)
                embed.add_field(name="damage", value=f"{row[2]}", inline=True)
                embed.add_field(name="defense", value=f"{row[4]}", inline=True)
                embed.add_field(name="attack", value=f"{row[3]}", inline=True)
                embed.add_field(name="ctype", value=f"{row[5]}", inline=True)
                embed.add_field(name="description", value=f"{row[6]}", inline=True)
                await ctx.send(embed=embed)
            else:
                await ctx.send("Weapon not found.")
    except sqlite3.Error as e:
        print(e)
        await ctx.send("An error occurred while retrieving weapon information.")


bot.load_extension("game")
bot.load_extension("databasecode")


bot.run(TOKEN)