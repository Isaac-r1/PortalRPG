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
    with sqlite3.connect('armor.db') as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='armor'")

        if c.fetchone() is None:
            c.execute('''CREATE TABLE armor
                    (name text, 
                    rarity text, 
                    attack integer, 
                    defense integer, 
                    ctype text, 
                    description text,
                    AID INTEGER PRIMARY KEY AUTOINCREMENT)''')

        with open('CSV & TXT Files/Armor.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader) # skip header row
            for row in reader:
                c.execute("SELECT * FROM armor WHERE name = ? AND rarity = ?", (row[0], row[1]))
                existing_row = c.fetchone()
                if not existing_row:
                    c.execute("INSERT INTO armor (name, rarity, attack, defense, ctype, description) VALUES (?, ?, ?, ?, ?, ?)", (*row,))

    with sqlite3.connect('accessories.db') as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='accessories'")

        if c.fetchone() is None:
            c.execute('''CREATE TABLE accessories
                    (name text, 
                    rarity text, 
                    attack integer, 
                    defense integer, 
                    description text,
                    ACID INTEGER PRIMARY KEY AUTOINCREMENT)''')

        with open('CSV & TXT Files/Accessories.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader) # skip header row
            for row in reader:
                name, rarity, attack, defense, description = row
                c.execute("SELECT * FROM accessories WHERE name = ? AND rarity = ?", (name, rarity))
                existing_row = c.fetchone()
                if existing_row is None:
                    c.execute("INSERT INTO accessories (name, rarity, attack, defense, description) VALUES (?, ?, ?, ?, ?)", (name, rarity, attack, defense, description))
        conn.commit()

    with sqlite3.connect('weapons.db') as conn:
        c = conn.cursor()

        # check if table exists and create if not
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

        # read CSV file and insert rows if they don't already exist
        with open('CSV & TXT Files/Book1.csv', newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            next(reader) # skip header row
            for row in reader:
                name, rarity, damage, attack, defense, ctype, description = row
                c.execute("SELECT * FROM weapons WHERE name = ? AND rarity = ?", (name, rarity))
                existing_row = c.fetchone()
                if existing_row is None:
                    c.execute("INSERT INTO weapons (name, rarity, damage, attack, defense, ctype, description) VALUES (?, ?, ?, ?, ?, ?, ?)", (name, rarity, damage, attack, defense, ctype, description))
        conn.commit()

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

    with sqlite3.connect('activecreatures.db') as conn:
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activecreatures'")
        if c.fetchone() is None:
            c.execute('''CREATE TABLE activecreatures(
                name text,
                HP integer,
                max_HP integer,
                XP integer,
                defense integer,
                damage integer,
                attack integer,
                gold integer,
                Biome text,
                diff integer,
                CID integer PRIMARY KEY AUTOINCREMENT
            )''')



# create a new database to hold the merged data
    with sqlite3.connect('items.db') as conn:
        c = conn.cursor()

        c.execute("SELECT name from sqlite_master WHERE type='table' AND name = 'items'")
        if c.fetchone() is None:
            # create the items table with an auto-incrementing primary key
            c.execute('''CREATE TABLE items(
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                type TEXT,
                rarity TEXT,
                damage INTEGER,
                attack INTEGER,
                defense INTEGER,
                description TEXT,
                ctype TEXT
            )''')

        # attach the original databases
        c.execute("ATTACH 'weapons.db' AS weapons")
        c.execute("ATTACH 'armor.db' AS armor")
        c.execute("ATTACH 'accessories.db' AS accessories")

        # insert data from the original databases into the items table,
        # using unique auto-incrementing item_id values
        c.execute('''SELECT COUNT(*) FROM items WHERE type = 'weapon' AND name IN (SELECT name FROM weapons.weapons)''')
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO items (name, type, rarity, damage, attack, defense, description, ctype)
                SELECT name, 'weapon', rarity, damage, attack, defense, description, ctype
                FROM weapons.weapons''')

        c.execute('''SELECT COUNT(*) FROM items WHERE type = 'armor' AND name IN (SELECT name FROM armor.armor)''')
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO items (name, type, rarity, damage, attack, defense, description, ctype)
                SELECT name, 'armor', rarity, 0, attack, defense, description, ctype
                FROM armor.armor''')

        c.execute('''SELECT COUNT(*) FROM items WHERE type = 'accessory' AND name IN (SELECT name FROM accessories.accessories)''')
        if c.fetchone()[0] == 0:
            c.execute('''INSERT INTO items (name, type, rarity, damage, attack, defense, description, ctype)
                SELECT name, 'accessory', rarity, 0, attack, defense, description, ''
                FROM accessories.accessories''')

        conn.commit()

async def setup(bot):
    await bot.add_cog(databasecode())
