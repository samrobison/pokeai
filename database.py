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

def findMovesForPokemon(pokemonName):
    conn = sqlite3.connect(databasePath)
    c = conn.cursor()
    c.execute("SELECT * FROM seenMoves WHERE pokemonName = ?", (pokemonName,))
    results = c.fetchall()
    conn.close()
    return results

def updateMovesSeen(moves, pokemonName):
    conn = sqlite3.connect(databasePath)
    c = conn.cursor()
    c.execute("UPDATE seenMoves SET pokemonSeen = pokemonSeen + 1 WHERE pokemonName = ?", (pokemonName,))
    conn.commit()
    for move in moves:
        c.execute(
            "UPDATE seenMoves SET timesSeen = timesSeen + 1 WHERE pokemonName = ? AND move_name = ?",
            (pokemonName, move),
        )
        conn.commit()
    conn.close()

def addNewMove(move_name, pokemonName):
    conn = sqlite3.connect(databasePath)
    c = conn.cursor()
    c.execute("SELECT timesSeen FROM seenMoves WHERE pokemonName = ? LIMIT 1", (pokemonName,))
    result = c.fetchall()
    timesSeen = int(result[0][0]) if result else 0
    if not moveExists(move_name, pokemonName, conn, c):
        c.execute(
            "INSERT INTO seenMoves (pokemonName, move_name, timesSeen, pokemonSeen) VALUES (?, ?, ?, 0)",
            (pokemonName, move_name, timesSeen),
        )
        conn.commit()
    conn.close()

def moveExists(move_name, pokemonName, conn, c):
    c.execute(
        "SELECT timesSeen FROM seenMoves WHERE move_name = ? AND pokemonName = ? LIMIT 1",
        (move_name, pokemonName),
    )
    return len(c.fetchall()) != 0


