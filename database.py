import sqlite3
import os.path

class PokeDatabase:
    def __init__(self):
        self.databasePath = './pokeAiDb.db'
        if not os.path.isfile(self.databasePath):
            self.dbSetup()
        self.conn = sqlite3.connect(self.databasePath)
        self.c = self.conn.cursor()

    def dbSetup(self):
        conn = sqlite3.connect(self.databasePath)
        conn.execute('''CREATE TABLE seenMoves
            ( pokemonName CHAR(50) NOT NULL ,
            moveName CHAR(50) NOT NULL,
            timesSeen INT NOT NULL DEFAULT 0,
            pokemonSeen INT NOT NULL DEFAULT 0
            );
            ''')
        conn.commit()
        conn.close()

    def findMovesForPokemon(self, pokemonName):
        self.c.execute("SELECT * FROM seenMoves WHERE pokemonName = '" + pokemonName + "';")
        results = self.c.fetchall()
        return results

    def updateMovesSeen(self, moves, pokemonName):
        #increment pokemon seen
        self.c.execute("UPDATE seenMoves SET pokemonSeen = pokemonSeen + 1 WHERE pokemonName = '" + pokemonName + "';")
        self.conn.commit()

        for move in moves:
            self.c.execute("UPDATE seenMoves SET timesSeen = timesSeen + 1 WHERE pokemonName = '" + pokemonName + "' and moveName = '" + move +"';")
            self.conn.commit()

    def addNewMove(self, moveName, pokemonName):
        self.c.execute("SELECT timesSeen FROM seenMoves WHERE pokemonName = '" + pokemonName + "' LIMIT 1;")
        result = self.c.fetchall()
        timesSeen = 0
        if len(result) != 0:
            timesSeen = result [0]
        if not self.moveExists(moveName, pokemonName):
            self.c.execute("INSERT INTO seenMoves (pokemonName, moveName, timesSeen, pokemonSeen) VALUES ('"+ pokemonName+"','"+ moveName+"', "+ str(timesSeen)+", 0 )")
            self.conn.commit()


    def moveExists(self, moveName, pokemonName):
        self.c.execute("SELECT timesSeen FROM seenMoves WHERE moveName = '" + moveName + "' and pokemonName = '" + pokemonName + "'LIMIT 1;")
        if len(self.c.fetchall()) == 0:
            return False
        return True


