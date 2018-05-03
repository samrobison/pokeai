import sqlite3
import os.path

databasePath = './pokeAiDb.db'


def initDb():
    if not os.path.isfile(databasePath):
        dbSetup()

def dbSetup():
    conn = sqlite3.connect(databasePath)
    conn.execute('''CREATE TABLE seenMoves
            ( pokemonName CHAR(50) NOT NULL ,
            move_name CHAR(50) NOT NULL,
            timesSeen INT NOT NULL DEFAULT 0,
            pokemonSeen INT NOT NULL DEFAULT 0
            );
            ''')
    conn.commit()
    conn.close()

def findMovesForPokemon( pokemonName):
    conn = sqlite3.connect(databasePath)
    c = conn.cursor()
    c.execute("SELECT * FROM seenMoves WHERE pokemonName = '" + pokemonName + "';")
    results = c.fetchall()
    conn.close()
    return results

def updateMovesSeen( moves, pokemonName):
    conn = sqlite3.connect(databasePath)
    c = conn.cursor()
    #increment pokemon seen
    c.execute("UPDATE seenMoves SET pokemonSeen = pokemonSeen + 1 WHERE pokemonName = '" + pokemonName + "';")
    conn.commit()
    conn.close()

    for move in moves:
        c.execute("UPDATE seenMoves SET timesSeen = timesSeen + 1 WHERE pokemonName = '" + pokemonName + "' and move_name = '" + move +"';")
        conn.commit()
    conn.close()

def addNewMove( move_name, pokemonName):
    conn = sqlite3.connect(databasePath)
    c = conn.cursor()
    c.execute("SELECT timesSeen FROM seenMoves WHERE pokemonName = '" + pokemonName + "' LIMIT 1;")
    result = c.fetchall()
    timesSeen = 0
    if len(result) != 0:
        timesSeen = int(str(result[0][0]))
    if not moveExists(move_name, pokemonName, conn, c):
        c.execute("INSERT INTO seenMoves (pokemonName, move_name, timesSeen, pokemonSeen) VALUES ('"+ pokemonName+"','"+ move_name+"',"+str(timesSeen)+", 0 )")
        conn.commit()
    conn.close()


def moveExists( move_name, pokemonName, conn, c):
    c.execute("SELECT timesSeen FROM seenMoves WHERE move_name = '" + move_name + "' and pokemonName = '" + pokemonName + "'LIMIT 1;")
    if len(c.fetchall()) == 0:
        return False
    return True


