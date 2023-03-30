from discord.ext import commands
import discord
import sqlite3
import csv
import sys
sys.path.append("C:\\Users\\gamin\\PortalRPG")
from PythonFiles.config import TOKEN
import random
from PythonFiles.game import game
from PythonFiles.databasecode import databasecode
from PythonFiles.Battle import Battle

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', case_insensitive=True, 
                   help_command=commands.DefaultHelpCommand(dm_help=True), 
                   intents=intents)
bot.case_insensitive = True
bot.command_prefix = ['!']

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
    if not (new_mode.lower() == "adventure" or new_mode.lower() == "athome"):
        await ctx.send("invalid mode")
        raise commands.CommandError("invalid mode!")
    
    if(new_mode == "ATHOME"):
        game.Character.changeRegion("None", user_id)
    
    if game.Character.getMode(user_id) == new_mode:
        await ctx.send("You're already in this state!")
        raise commands.CommandError("Invalid mode!")
    
    game.Character.changeMode(new_mode.upper(), user_id)
    await ctx.send("Mode changed to " + new_mode.upper() + "!")

@bot.command(name = "delete_user")
@commands.is_owner()
async def delete_user(ctx, member: discord.Member):
    with sqlite3.connect('characters.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM characters WHERE user_id=?", (member.id,))
    with sqlite3.connect('player_weapons.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM player_weapons WHERE user_id=?", (member.id,))
    await ctx.send(f"User with ID {member.id} has been deleted from the database.")

@bot.command(name = "uid")
async def uid(ctx, member: discord.Member):
    await ctx.send(member.id)

@bot.command(name = "region")
async def region(ctx, new_region: str):
    user_id = ctx.message.author.id

    if game.Character.getMode(user_id) != "ADVENTURE":
        await ctx.send("Change your mode to ADVENTURE!")
        raise commands.CommandError("Invalid mode")

    if new_region.lower() not in ["tundra", "ocean", "forest", "swamp", "mountain"]:
        await ctx.send("invalid region")
        raise commands.CommandError("invalid region!")

    game.Character.changeRegion(new_region.lower(), user_id)  
    await ctx.send("Region changed to " + new_region.lower() + "!")

@bot.command(name = "hunt")
@commands.cooldown(1, 10, commands.BucketType.user)

async def hunt(ctx):
    user_id = ctx.message.author.id

    if game.Character.getMode(user_id).lower() != "adventure":
        await ctx.send("Change your mode to **adventure** to hunt!")
        raise commands.CommandError("**Invalid mode**")
    
    if game.Character.getRegion(user_id) == "None":
        await ctx.send("Enter a region!")
        raise commands.CommandError("Invalid region")

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

    await ctx.send("Do you wish to battle your encounter? Type Y/N")

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel
    
    msg = await bot.wait_for("message", check=check)
    if(msg.content.lower() == "y"):
        await Battle.fight(ctx, user_id, creature)
    else:
        await ctx.send("You fled the encounter!")

@bot.command(name = "create")
async def create(ctx, chtype: str, name: str):
    user_id = ctx.message.author.id
    
    if not (chtype == "mage" or chtype == "archer" or chtype == "swordsman"):
        await ctx.send("please pick one of the three following classes: mage, archer, swordsman then provide a name!")
        raise commands.CommandError("Not a valid class!")
    
    if len(name) >= 30:
        await ctx.send("Your name is too long!")
        raise commands.CommandError("Not a valid name!")
    

    cursor.execute('SELECT * FROM characters WHERE id = ?', (user_id,))
    result = cursor.fetchone()

    if result is None:
        new_character = game.Character(name=name, HP=100, max_HP=100, XP=0, defense=0, attack=3, gold=10, inventory= "Empty", w = Wchoice(chtype, user_id), armor = None, accessory = None, ctype=chtype, battling=False, mode="AT HOME", region=None,  level=1, user_id=user_id)
        cursor.execute('INSERT INTO characters (name, HP, max_HP, XP, defense, attack, gold, inventory, w, armor, accessory, ctype, battling, mode, region, level, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', (new_character.name, new_character.HP, new_character.max_HP, new_character.XP, new_character.defense, new_character.attack, int(new_character.gold), new_character.inventory, new_character.w, new_character.armor, new_character.accessory, new_character.ctype, new_character.battling, new_character.mode, new_character.region, new_character.level, new_character.user_id))
        conn.commit()
        await ctx.send("Your character, " + name + ",has been created, type: " + chtype)
    else:
        await ctx.send("You already own an account!")
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
        embed.add_field(name="Weapon Slots", value= game.weapon.get_weapon_name(row[9]), inline=True)
        embed.add_field(name="Armor", value=row[10], inline=True)
        embed.add_field(name="Accessory", value=row[11], inline=True)
        embed.add_field(name="Class", value=row[12], inline=True)
        embed.add_field(name="Mode", value=row[14], inline=False)
        embed.add_field(name="Region", value=row[15], inline=True)
        embed.add_field(name="Level", value=row[16], inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send("You don't have a character yet. Use `!create` to create one.")


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

@bot.command(name="restart")
async def restart(ctx):
    adminstrator_users=["851122648574328862","776953958890995784"]
    if str(ctx.author.id) not in adminstrator_users:
        await ctx.send("You're not allowed to use this... stupid.")
        return
    await ctx.send("Restarting the bot!")
    await bot.close()

bot.load_extension("game")
bot.load_extension("databasecode")
bot.load_extension("Battle")


bot.run(TOKEN)