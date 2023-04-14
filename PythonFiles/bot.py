from discord.ext import commands
import discord
import sqlite3
import csv
import sys
import subprocess
import asyncio
import time
from discord.ui import Button
from discord import ButtonStyle
sys.path.append("C:\\Users\\gamin\\PortalRPG")
from PythonFiles.config import TOKEN
import random
from PythonFiles.game import game
from PythonFiles.databasecode import databasecode
from PythonFiles.Battle import Battle
from PythonFiles.connections import connections
from PythonFiles.Inventory import Inventory


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', case_insensitive=True, 
                   help_command=commands.DefaultHelpCommand(dm_help=False), 
                   intents=intents, owner_ids={605418818864414762, 678401615333556277})
bot.case_insensitive = True
bot.command_prefix = ['!']

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
        inventory INTEGER,
        w INTEGER,
        armor INTEGER,
        accessory INTEGER,
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

@bot.command()
@commands.is_owner()
async def insert(ctx, member: discord.Member, item_id: int, slot: int):
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        # check if the row with the given user_id and slot already exists
        c.execute("SELECT * FROM inventory WHERE user_id = ? AND slot = ?", (member.id, slot))
        existing_row = c.fetchone()
        if existing_row:
            # if the row already exists, update it with the new values
            c.execute("UPDATE inventory SET item_id = ? WHERE user_id = ? AND slot = ?", (item_id, member.id, slot))
        else:
            # if the row doesn't exist, insert a new row
            c.execute("INSERT INTO inventory (user_id, item_id, slot) VALUES (?, ?, ?)", (member.id, item_id, slot))
        conn.commit()

@bot.command(name="drop_item")
async def drop_item(ctx, slot: int):
    user_id = ctx.message.author.id
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM inventory WHERE user_id = ? AND slot = ?', (user_id, slot))
        row = c.fetchone()

        if row is None:
            await ctx.send("Invalid slot number.")
            return

        c.execute('UPDATE inventory SET item_id = NULL WHERE user_id = ? AND slot = ?', (user_id, slot))
        conn.commit()
        await ctx.send(f"Item in slot {slot} removed from your inventory.")
    
@bot.command(name = "delete_user")
@commands.is_owner()
async def delete_user(ctx, member: discord.Member):
    with sqlite3.connect('characters.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM characters WHERE user_id=?", (member.id,))
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        c.execute("DELETE FROM inventory WHERE user_id=?", (member.id,))
    

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

    if new_region.lower() not in ["ocean", "forest", "swamp", "mountain"]:
        await ctx.send("invalid region")
        raise commands.CommandError("invalid region!")

    game.Character.changeRegion(new_region.lower(), user_id)  
    await ctx.send("Region changed to " + new_region.lower() + "!")

@bot.command(name = "hunt")
@commands.cooldown(1, 3, commands.BucketType.user)
async def hunt(ctx):
    user_id = ctx.message.author.id
    if game.Character.getRegion(user_id) is None:
        await ctx.send("Enter a region!")
        raise commands.CommandError("Invalid region")

    if game.Character.getMode(user_id).lower() != "adventure":
        await ctx.send("Change your mode to **adventure** to hunt!")
        raise commands.CommandError("**Invalid mode**")
    

    region = game.Character.getRegion(user_id)
    level = game.Character.getLevel(user_id)
    rarity = game.CCreature.how_rare()

    if(rarity == "A"):
        ctitle = "Advanced"
    elif(rarity == "G"):
        ctitle = "Greater"
    else:
        ctitle = "Common"

    creature, item = game.CCreature.spawnCreature(region, level, rarity)

    print(creature[10])

    await ctx.send("An encounter has spawned!")
    if creature:
        embed = discord.Embed(title= ctitle + " " + f"{creature[0]} Status", color=discord.Color.green())
        embed.add_field(name="HP", value=f"{creature[1]}/{creature[2]}", inline=True)
        embed.add_field(name="XP", value=creature[3], inline=True)
        embed.add_field(name="Defense", value=creature[4], inline=True)
        embed.add_field(name="Damage", value=creature[5], inline=True)
        embed.add_field(name="Attack", value=creature[6], inline=True)
        embed.add_field(name="Gold", value=creature[7], inline=True)
        await ctx.send(embed=embed)

    battle_button = BattleButton(ctx, user_id, creature, rarity, item)
    flee_button = FleeButton(user_id)
    view = discord.ui.View()
    view.add_item(battle_button)
    view.add_item(flee_button)
    await ctx.send("Do you wish to battle your encounter?", view=view)

class BattleButton(discord.ui.Button):
    def __init__(self, ctx, user_id, creature, rarity, item):
        super().__init__(style=discord.ButtonStyle.green, label="Battle")
        self.ctx = ctx
        self.user_id = user_id
        self.creature = creature
        self.rarity = rarity
        self.item = item
        self.clicked = False

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id and not self.clicked:
            self.clicked = True
            await Battle.fight(self.ctx, self.user_id, self.creature, self.rarity, self.item)

class FleeButton(discord.ui.Button):
    def __init__(self,user_id):
        super().__init__(style=discord.ButtonStyle.red, label="Flee")
        self.clicked = False
        self.user_id = user_id
    
    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id == self.user_id and not self.clicked:
            self.clicked = True
            await interaction.response.send_message("You clicked the Flee button!")


class MyButton(discord.ui.Button):
    def __init__(self):
        super().__init__(style=discord.ButtonStyle.green, label="Click me!")

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("You clicked the button!")

@bot.command()
async def test(ctx):
    button = MyButton()
    view = discord.ui.View()
    view.add_item(button)
    await ctx.send("Click the button below:", view=view)

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
        Inventory.create_inventory(user_id)
        new_character = game.Character(name=name, HP=100, max_HP=100, XP=0, defense=0, attack=0, gold=10, inventory= user_id, w = Wchoice(chtype, user_id), armor = None, accessory = None, ctype=chtype, battling=False, mode="AT HOME", region=None,  level=1, user_id=user_id)
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
        embed.add_field(name="Weapon Slots", value= game.weapon.get_name(row[9]), inline=True)
        embed.add_field(name="Armor", value=game.weapon.get_name(row[10]), inline=True)
        embed.add_field(name="Accessory", value= game.weapon.get_name(row[11]), inline=True)
        embed.add_field(name="Class", value=row[12], inline=True)
        embed.add_field(name="Mode", value=row[14], inline=False)
        embed.add_field(name="Region", value=row[15], inline=True)
        embed.add_field(name="Level", value=row[16], inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send("You don't have a character yet. Use `!create` to create one.")

@bot.command()
async def equip_armor(ctx, slot: int):
    user_id = ctx.message.author.id
    with sqlite3.connect('characters.db') as conn:
        c = conn.cursor()
        c.execute('SELECT ctype FROM characters WHERE user_id = ?', (user_id,))
        class_type = c.fetchone()[0]
    
    with sqlite3.connect('inventory.db') as conn1:
        c1 = conn1.cursor()
        c1.execute('SELECT * FROM inventory WHERE user_id=?', (user_id,))
        inventory_data = c1.fetchall()
        item_data = inventory_data[slot - 1] #item_data accesses the item information within the correct slot
        item_id = item_data[1]
    
    with sqlite3.connect('items.db') as conn2:
        c2 = conn2.cursor()
        c2.execute('SELECT * FROM items WHERE item_id = ?', (item_id,))
        result = c2.fetchone()
    
    if result is None:
        await ctx.send("Item not found")
        return
    
    if result[8][0] != class_type[0]:
        await ctx.send(f"You can't equip {result[1]} because it's not suitable for your class.")
        return
    
    if result[2] != 'armor':
        await ctx.send("This item is not an armor piece")
        return

     # Equip the accessory and display the name
    with sqlite3.connect('characters.db') as conn3:
        c3 = conn3.cursor()
        c3.execute('SELECT armor FROM characters WHERE user_id = ?', (user_id,))
        old_armor = c3.fetchone()[0]
        if old_armor:
            # Remove equipped accessory and add it to the user's inventory
            c1.execute('UPDATE inventory SET item_id = ? WHERE user_id = ? AND slot = ?', (old_armor, user_id, slot))
            conn1.commit()  # commit changes made to inventory table
            c3.execute('UPDATE characters SET armor = ? WHERE user_id = ?', (item_id, user_id))
            conn3.commit()  # commit changes made to characters table
            update_player_stats(item_id,user_id, "swapA")
            await ctx.send(f"Swapped {result[1]} with {old_armor}.")
        else:
            # Equip the accessory and display the name
            c1.execute('UPDATE inventory SET item_id = NULL WHERE user_id = ? AND slot = ?', (user_id, slot))
            conn1.commit()  # commit changes made to inventory table
            c3.execute('UPDATE characters SET armor = ? WHERE user_id = ?', (item_id, user_id))
            conn3.commit()  # commit changes made to characters table
            update_player_stats(item_id,user_id, None)
            await ctx.send(f"Equipped {result[1]}!")

@bot.command()
async def equip_weapon(ctx, slot: int):
    user_id = ctx.message.author.id
    with sqlite3.connect('characters.db') as conn:
        c = conn.cursor()
        c.execute('SELECT ctype FROM characters WHERE user_id = ?', (user_id,))
        class_type = c.fetchone()[0]
    
    with sqlite3.connect('inventory.db') as conn1:
        c1 = conn1.cursor()
        c1.execute('SELECT * FROM inventory WHERE user_id=?', (user_id,))
        inventory_data = c1.fetchall()
        item_data = inventory_data[slot - 1] #item_data accesses the item information within the correct slot
        item_id = item_data[1]
    
    with sqlite3.connect('items.db') as conn2:
        c2 = conn2.cursor()
        c2.execute('SELECT * FROM items WHERE item_id = ?', (item_id,))
        result = c2.fetchone()
    
    if result is None:
        await ctx.send("Item not found")
        return
    
    if result[8][0].lower() != class_type[0].lower():
        await ctx.send(f"You can't equip {result[1]} because it's not suitable for your class.")
        return
    
    if result[2] != 'weapon':
        await ctx.send("This item is not an weapon!")
        return

     # Equip the accessory and display the name
    with sqlite3.connect('characters.db') as conn3:
        c3 = conn3.cursor()
        c3.execute('SELECT w FROM characters WHERE user_id = ?', (user_id,))
        old_weapon = c3.fetchone()[0]
        if old_weapon:
            update_player_stats(item_id,user_id, "swapW")
            # Remove equipped accessory and add it to the user's inventory
            c1.execute('UPDATE inventory SET item_id = ? WHERE user_id = ? AND slot = ?', (old_weapon, user_id, slot))
            conn1.commit()  # commit changes made to inventory table
            c3.execute('UPDATE characters SET w = ? WHERE user_id = ?', (item_id, user_id))
            conn3.commit()  # commit changes made to characters table
            await ctx.send(f"Swapped {result[1]} with {old_weapon}.")
        else:
            update_player_stats(item_id,user_id, None)
            # Equip the accessory and display the name
            c1.execute('UPDATE inventory SET item_id = NULL WHERE user_id = ? AND slot = ?', (user_id, slot))
            conn1.commit()  # commit changes made to inventory table
            c3.execute('UPDATE characters SET w = ? WHERE user_id = ?', (item_id, user_id))
            conn3.commit()  # commit changes made to characters table
            await ctx.send(f"Equipped {result[1]}!")

@bot.command()
async def equip_accessory(ctx, slot: int):
    user_id = ctx.message.author.id
    with sqlite3.connect('inventory.db') as conn:
        c = conn.cursor()
        c.execute('SELECT * FROM inventory WHERE user_id=?', (user_id,))
        inventory_data = c.fetchall()
        item_data = inventory_data[slot - 1] #item_data accesses the item information within the correct slot
        item_id = item_data[1]

    with sqlite3.connect('items.db') as conn1:
        c1 = conn1.cursor()
        c1.execute('SELECT * FROM items WHERE item_id = ?', (item_id,))
        result = c1.fetchone()

    if result is None:
        await ctx.send("Item not found.")
        return

    if result[2] != 'accessory':
        await ctx.send("This item is not an accessory.")
        return

    # Equip the accessory and display the name
    with sqlite3.connect('characters.db') as conn3:
        c3 = conn3.cursor()
        c3.execute('SELECT accessory FROM characters WHERE user_id = ?', (user_id,))
        old_accessory = c3.fetchone()[0]
        if old_accessory:
            # Remove equipped accessory and add it to the user's inventory
            c.execute('UPDATE inventory SET item_id = ? WHERE user_id = ? AND slot = ?', (old_accessory, user_id, slot))
            conn.commit()  # commit changes made to inventory table
            c3.execute('UPDATE characters SET accessory = ? WHERE user_id = ?', (item_id, user_id))
            conn3.commit()  # commit changes made to characters table
            update_player_stats(item_id,user_id, "swapAC")
            await ctx.send(f"Swapped {result[1]} with {old_accessory}.")
        else:
            # Equip the accessory and display the name
            c.execute('UPDATE inventory SET item_id = NULL WHERE user_id = ? AND slot = ?', (user_id, slot))
            conn.commit()  # commit changes made to inventory table
            c3.execute('UPDATE characters SET accessory = ? WHERE user_id = ?', (item_id, user_id))
            conn3.commit()  # commit changes made to characters table
            update_player_stats(item_id,user_id, None)
            await ctx.send(f"Equipped {result[1]}!")

def update_player_stats(item_id, user_id, swap):
    print(item_id)
    conn = sqlite3.connect('characters.db')
    c = conn.cursor()
    c.execute('SELECT attack, defense FROM characters WHERE user_id = ?', (user_id,))
    player_stats = c.fetchone() #this is the original attack and def (base stats)

    c.execute('SELECT w, armor, accessory FROM characters WHERE user_id=?', (user_id,))
    active_stats = c.fetchone() #This is checking the current weapon, armor, accessory slots if they're full
    if(swap == "swapW"):
        subtract = active_stats[0] #if we're swapping a weapon, we set subtract as the WID
    elif(swap == "swapA"): 
        subtract = active_stats[1] #if armor, subtract = AID
    elif(swap == "swapAC"):
        subtract = active_stats[2] #if accessory, subtract = ACID
    else:
        subtract = None #if we're just inserting an item, subtract is jsut none

    conn1 = sqlite3.connect('items.db')
    c1 = conn1.cursor()
    c1.execute('SELECT attack, defense FROM items WHERE item_id = ?', (subtract,)) #Now, we check the attack and defense values from subtract (which is a ID)
    sub_values = c1.fetchone() 
    c1.execute('SELECT attack, defense FROM items WHERE item_id = ?', (item_id,)) #We also check the attack and defense values from the item in inventory
    item_stats = c1.fetchone()
    
    if(subtract == None):
        sub_values = (0, 0)

    print(item_stats[0])
    print(player_stats[0])
    print(sub_values[0])
    new_att = item_stats[0] + player_stats[0] - sub_values[0] #sub_values[0] is the current slot being swapped out, item_stats[0] is the item being insertedm player[0] is base stats
    new_def = item_stats[1] + player_stats[1] - sub_values[1]

    c.execute('UPDATE characters SET attack = ?, defense = ? WHERE user_id = ?', (new_att, new_def, user_id))
    conn.commit()
    conn.close()



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


async def load_extensions():
    #await bot.load_extension("jishaku")
    await bot.load_extension("game")
    await bot.load_extension("databasecode")
    await bot.load_extension("Battle")
    await bot.load_extension("Inventory")


async def main():
    await load_extensions()
    await bot.login(TOKEN)
    await bot.connect()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())

bot.run(TOKEN)
