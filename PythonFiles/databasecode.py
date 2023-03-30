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



class databasecode(commands.Cog):
    with sqlite3.connect('weapons.db') as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weapons'")

        table_exists = c.fetchone() is not None

        if not table_exists:
            c.execute('''CREATE TABLE weapons
                    (name text, 
                    rarity text, 
                    damage integer, 
                    attack integer, 
                    defense integer, 
                    ctype text, 
                    description text,
                    WID INTEGER PRIMARY KEY AUTOINCREMENT)''')

        with open('CSV & TXT Files/Book1.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader) # skip header row
            for row in reader:
                c.execute("INSERT INTO weapons (name, rarity, damage, attack, defense, ctype, description) VALUES (?, ?, ?, ?, ?, ?, ?)", (*row,))

    def create_player_weapons_table():
        with sqlite3.connect('player_weapons.db') as conn:
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='player_weapons'")

            table_exists = c.fetchone() is not None

            if not table_exists:
                c.execute('''CREATE TABLE player_weapons
                    (user_id integer, 
                    WID integer,
                    slot integer,
                    PRIMARY KEY (user_id, WID, slot))''')
    
    def insert_player_weapon(user_id, WID, slot):
        with sqlite3.connect('player_weapons.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO player_weapons (user_id, WID, slot) VALUES (?, ?, ?)", (user_id, WID, slot))

    with sqlite3.connect('creatures.db') as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='creatures'")
        if c.fetchone() is None:
            c.execute('''CREATE TABLE creatures(
                name text,
                HP integer,
                max_HP integer,
                XP integer,
                defense integer,
                damage integer,
                attack integer,
                gold integer,
                Biome text,
                diff integer
            )''')

        with open('CSV & TXT Files/Creatures.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader) # skip header row
            for row in reader:
                c.execute("INSERT INTO Creatures (name, HP, max_HP, XP, defense, damage, attack, gold, Biome, diff) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (*row,))
def setup(bot):
    bot.add_cog(databasecode())
