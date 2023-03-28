import csv
import sqlite3
from copy import deepcopy
import random
import itertools
from discord.ext import commands


class game(commands.Cog):

    class inAnimated:
        def __init__(self, name, attack, defense, description):
            self.name = name
            self.attack = attack
            self.defense = defense
            self.description = description

    
    class weapon(inAnimated):
        def __init__(self, name, rarity, damage, attack, defense, ctype, description, WID):
            super().__init__(name, attack, defense, description)
            self.rarity = rarity
            self.damage = damage
            self.ctype = ctype
            self.WID = WID
    
    class Animated:
        def __init__(self, name, HP, max_HP, XP, defense, attack, gold):
            self.name = name #name of the alive character
            self.HP = HP #current health point
            self.max_HP = max_HP #max health points
            self.XP = XP #xp
            self.defense = defense #defense (shielding)
            self.attack = attack #how hard you hit
            self.gold = gold #currency
        
        #def combat(self, other):
    
    global how_rare
    def how_rare():
        randomN = randint(0,100)
        if(randomN >= 95):
            rarity = "A"
        elif(randomN >= 60 <= 95):
                rarity = "G"
        else:
                rarity = "N" 
        return rarity

    global rarity_scaling
    def rarity_scaling(value, r):
        if(r == "N"):
            return value 
        if(r == "G"):
            return value*(randint(10, 15)/10)
        if(r == "A"):
            return value*(randint(15, 20)/10)
    

    class Character(Animated):
        max_level = 20

        def __init__(self, name, HP, max_HP, XP, defense, attack, gold, inventory, w, armor, accessory, ctype, battling, mode, region, level, user_id):
            super().__init__(name, HP, max_HP, XP, defense, attack, gold)
            self.inventory = inventory #player inventory, storage (on the character)
            self.w = w #weapon slot 1
            self.armor = armor
            self.accessory = accessory
            self.ctype = ctype #character type
            self.battling = battling #character battling
            self.mode = mode #gamemode
            self.region = region #biome
            self.level = level #level
            self.user_id = user_id #user id

        def changeMode(new_mode, user_id):
            conn = sqlite3.connect('characters.db')
            c = conn.cursor()
            c.execute("UPDATE characters SET mode=? WHERE user_id=?", (new_mode, user_id))
            conn.commit()

        def changeRegion(new_region, user_id):
            conn = sqlite3.connect('characters.db')
            c = conn.cursor()
            c.execute("UPDATE characters SET region=? WHERE user_id=?", (new_region, user_id))
            conn.commit()

        def getMode(user_id):
            conn = sqlite3.connect('characters.db')
            c = conn.cursor()
            c.execute("SELECT mode FROM characters WHERE user_id=?", (user_id,))
            mode = c.fetchone()
            if mode is not None:
                return mode[0]
            else:
                return None
        
        def getRegion(user_id):
            conn = sqlite3.connect('characters.db')
            c = conn.cursor()
            c.execute("SELECT region FROM characters WHERE user_id=?", (user_id,))
            region = c.fetchone()
            if region is not None:
                return region[0]
            else:
                return None
        
        def getLevel(user_id):
            conn = sqlite3.connect('characters.db')
            c = conn.cursor()
            c.execute("SELECT level FROM characters WHERE user_id=?", (user_id,))
            level = c.fetchone()
            if level is not None:
                return level[0]
            else:
                return None
            
        
        #def save_to_db(self):

    class CCreature(Animated): #common creature
        def __init__(self, name, HP, max_HP, XP, defense, damage, attack, gold, biome):
            super().__init__(name, HP, max_HP, XP, defense, attack, gold)
            self.damage = damage #base damage of every creature
            self.biome = biome #what biome is this creature from
            #self.rarity = rarity #range from N/A, greater, advanced

        def spawnCreature(pbiome, level):
            conn = sqlite3.connect('creatures.db')
            c = conn.cursor()
            if level < 3:
                c.execute("SELECT * FROM Creatures WHERE diff<3 AND biome=?", (pbiome,))
            elif level < 5:
                c.execute("SELECT * FROM Creatures WHERE diff<4 AND biome=?", (pbiome,))
            elif level < 8:
                c.execute("SELECT * FROM Creatures WHERE diff<5 AND biome=?", (pbiome,))
            else:
                c.execute("SELECT * FROM Creatures WHERE diff<=5 AND biome=?", (pbiome,))
            results = c.fetchall()
            if not results:
                return None
            return random.choice(results)

def setup(bot):
    bot.add_cog(game())