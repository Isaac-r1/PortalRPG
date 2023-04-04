import csv
import sqlite3
from copy import deepcopy
import random
from random import randint
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

        def get_weapon_damage(WID):
            with sqlite3.connect('weapons.db') as conn:
                c = conn.cursor()
                c.execute('SELECT damage FROM weapons WHERE WID = ?', (WID,))
                result = c.fetchone()
                if result:
                    return result[0]
                else:
                    return "Unknown Weapon"
                
        def get_weapon_name(WID):
            with sqlite3.connect('weapons.db') as conn:
                c = conn.cursor()
                c.execute('SELECT name FROM weapons WHERE WID = ?', (WID,))
                result = c.fetchone()
                if result:
                    return result[0]
                else:
                    return "Unknown Weapon"
                
        def get_name(item_id):
            with sqlite3.connect('items.db') as conn:
                c = conn.cursor()
                c.execute('SELECT name FROM items WHERE item_id = ?', (item_id,))
                result = c.fetchone()
                if result:
                    return result[0]
                else:
                    return "Unknown item"
        
        def random_rarity():
            n = random.randint(1,100)
            if(n >= 95):
                return "L"
            elif(n >= 80):
                return "R"
            elif(n >= 50):
                return "UC"
            else:
                return "C"

    
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
        
        def getMaxHP(user_id):
            conn = sqlite3.connect('characters.db')
            c = conn.cursor()
            c.execute("SELECT max_HP FROM characters WHERE user_id=?", (user_id,))
            max_HP = c.fetchone()
            if max_HP is not None:
                return max_HP[0]
            else:
                return None

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
        
        def how_rare():
            randomN = randint(0,100)
            if(randomN >= 95):
                rarity = "A"
            elif(randomN >= 60 <= 95):
                    rarity = "G"
            else:
                    rarity = "N" 
            return rarity
        
        def rarity_scaling(value, r):
            if(r == "N"):
                return value 
            if(r == "G"):
                return value*(randint(10, 15)/10)
            if(r == "A"):
                return value*(randint(15, 20)/10)

        def spawnCreature(pbiome, level, rarity):
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
            creature = random.choice(results)
            max_hp = game.CCreature.rarity_scaling(creature[2], rarity)
            damage = game.CCreature.rarity_scaling(creature[5], rarity)
            defense = game.CCreature.rarity_scaling(creature[4], rarity)
            gold = game.CCreature.rarity_scaling(creature[7], rarity)
            new_creature = (creature[0], int(max_hp), int(max_hp), creature[3], int(defense), int(damage), creature[6], int(gold), creature[2], creature[9])

            item_rarity = game.weapon.random_rarity()
            conn1 = sqlite3.connect('items.db')
            c1 = conn1.cursor()
            c1.execute("SELECT * FROM items WHERE rarity=?", (item_rarity,))
            iresults = c1.fetchall()
            if not iresults:
                return None
            item = random.choice(iresults)

            return (new_creature, item)

        def creature_damage(name):
            with sqlite3.connect('creatures.db') as conn:
                c = conn.cursor()
                c.execute('SELECT damage FROM creatures WHERE name = ?', (name,))
                result = c.fetchone()
                if result:
                    return result[0]
                else:
                    return "Unknown animal"
        
        
        def getMaxHP(name):
            conn = sqlite3.connect('creatures.db')
            c = conn.cursor()
            c.execute("SELECT max_HP FROM characters WHERE user_id=?", (name,))
            max_HP = c.fetchone()
            if max_HP is not None:
                return max_HP[0]
            else:
                return None



def setup(bot):
    bot.add_cog(game())