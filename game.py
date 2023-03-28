#from replit import db
import enum, random, sys
import csv
import sqlite3
from copy import deepcopy
import random
import itertools
from random import randint, random
from discord.ext import commands
from discord.ext.commands import bot
from discord.ext.commands.core import command

class game(commands.Cog):

    class GameMode(enum.IntEnum):
        ADVENTURE = 1
        BATTLE = 2
        ATHOME = 3
    
    class Region(enum.IntEnum):
        SWAMP = 1
        FOREST = 2
        TUNDRA = 3
        MOUNTAIN = 4
        OCEAN = 5
    
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

        def __init__(self, name, HP, max_HP, XP, defense, attack, gold, inventory, w, armor, accessory, ctype, battling, user_id):
            super().__init__(name, HP, max_HP, XP, defense, attack, gold)
            self.inventory = inventory #player inventory, storage (on the character)
            self.w = w #weapon slot 1
            self.armor = armor
            self.accessory = accessory
            self.ctype = ctype #character type
            self.battling = battling #character battling
            self.user_id = user_id #user id
        
        #def save_to_db(self):

    class CCreature(Animated): #common creature
        def __init__(self, name, HP, max_HP, XP, defense, damage, attack, gold, biome):
            super().__init__(name, HP, max_HP, XP, defense, attack, gold)
            self.damage = damage #base damage of every creature
            self.biome = biome #what biome is this creature from
            #self.rarity = rarity #range from N/A, greater, advanced
           

def setup(bot):
    bot.add_cog(game())