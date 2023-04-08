import sqlite3

class connections:
    conn = sqlite3.connect('characters.db')
    conn1 = sqlite3.connect('creatures.db')

