import time
import re
import traceback

from selenium import webdriver
from movedex import MoveDex
from tree import Tree
from Pokemon import Pokemon
from libs import *
from userinfo import password
from userinfo import username
from database import PokeDatabase

treeTest = False
battleHistory = []
db = PokeDatabase()

def openBrowser():
    #sign in and make team
    driver = webdriver.Chrome('./chromedriver')
    driver.get('http://play.pokemonshowdown.com/teambuilder');
    time.sleep(3)
    driver.find_element_by_name("backup").click()
    return driver

def importTeam(fileName):
    team = ""
    with open(fileName, 'r') as myFile:
        team=myFile.read()
    return team

def parseTeam(team):
    #get my pokemon
    #pokemon 1
    myPokemon = []
    name = team.splitlines()[2].split('@')[0].replace(" ", "").replace("-", "").lower()
    item = team.splitlines()[2].split('@')[1].strip()
    ability = team.splitlines()[3].split(':')[1].replace(" ", "")
    evs = team.splitlines()[4].split(':')[1].split('/')
    stats = {}
    for ev in evs:
        m1 = re.search('(\d+)\s(\w+)', ev)
        key = m1.group(2).lower()
        if key == 'def':
            key = 'defe'
        stats[key] = int(m1.group(1))
    move1 = team.splitlines()[6].replace(" ", "").replace("-", "").lower()
    move2 = team.splitlines()[7].replace(" ", "").replace("-", "").lower()
    move3 = team.splitlines()[8].replace(" ", "").replace("-", "").lower()
    move4 = team.splitlines()[9].replace(" ", "").replace("-", "").lower()

    moves = [MoveDex[move1], MoveDex[move2], MoveDex[move3], MoveDex[move4]]
    myPokemon.append(Pokemon(name, abil=ability, moves=moves, stat=stats, itemHeld=item))

    #pokemon 2
    name = team.splitlines()[11].split('@')[0].replace(" ", "").replace("-", "").lower()
    item = team.splitlines()[11].split('@')[1].strip()
    ability = team.splitlines()[12].split(':')[1].replace(" ", "")
    evs = team.splitlines()[13].split(':')[1].split('/')
    stats = {}
    for ev in evs:
        m1 = re.search('(\d+)\s(\w+)', ev)
        key = m1.group(2).lower()
        if key == 'def':
            key = 'defe'
        stats[key] = int(m1.group(1))
    move1 = team.splitlines()[15].replace(" ", "").replace("-", "").lower()
    move2 = team.splitlines()[16].replace(" ", "").replace("-", "").lower()
    move3 = team.splitlines()[17].replace(" ", "").replace("-", "").lower()
    move4 = team.splitlines()[18].replace(" ", "").replace("-", "").lower()

    moves = [MoveDex[move1], MoveDex[move2], MoveDex[move3], MoveDex[move4]]
    myPokemon.append(Pokemon(name, abil=ability, moves=moves, stat=stats, itemHeld=item))

    #pokemon 3
    name = team.splitlines()[20].split('@')[0].replace(" ", "").replace("-", "").lower()
    item = team.splitlines()[20].split('@')[1].strip()
    ability = team.splitlines()[21].split(':')[1].replace(" ", "")
    evs = team.splitlines()[22].split(':')[1].split('/')
    stats = {}
    for ev in evs:
        m1 = re.search('(\d+)\s(\w+)', ev)
        key = m1.group(2).lower()
        if key == 'def':
            key = 'defe'
        stats[key] = int(m1.group(1))
    move1 = team.splitlines()[24].replace(" ", "").replace("-", "").lower()
    move2 = team.splitlines()[25].replace(" ", "").replace("-", "").lower()
    move3 = team.splitlines()[26].replace(" ", "").replace("-", "").lower()
    move4 = team.splitlines()[27].replace(" ", "").replace("-", "").lower()

    moves = [MoveDex[move1], MoveDex[move2], MoveDex[move3], MoveDex[move4]]
    myPokemon.append(Pokemon(name, abil=ability, moves=moves, stat=stats, itemHeld=item))
    return myPokemon

def inputTeam(driver, teamText):
    #back to inputing team

    driver.find_elements_by_class_name('textbox')[0].send_keys(teamText)
    driver.find_element_by_name("saveBackup").click()

def login(driver):
    driver.find_element_by_name("login").click()
    driver.find_element_by_name("username").send_keys(username)
    driver.find_element_by_class_name("buttonbar").find_elements_by_tag_name("button")[0].click()
    time.sleep(1)
    driver.find_element_by_name("password").send_keys(password)
    driver.find_element_by_class_name("buttonbar").find_elements_by_tag_name("button")[0].click()
    time.sleep(1)

def queueMatch(driver):
    driver.get('http://play.pokemonshowdown.com')
    time.sleep(5)

    for i in range(1):
        driver.find_element_by_name("format").click()
        time.sleep(1)
        driver.find_elements_by_xpath("//button[@value='gen71v1']")[0].click()
        time.sleep(1)

    url = driver.current_url
    driver.find_element_by_name("search").click()
    return url

def wait(driver, value, func):
    while func(driver, value):
        for chat in driver.find_elements_by_css_selector('div.battle-history'):
            if 'botLife won the battle!' in chat.text:
                return -1
            elif 'won the battle' in chat.text:
                return -2
        print 'waiting'
        time.sleep(1)
    time.sleep(4)
    return 0

def createEnemyPokemon(otherPokemon):
    enemyPokemon = []
    for p in otherPokemon:
        name = str(p)
        name = name.lower()
        name = name.replace(" ", "").replace("-", "")
        enemyPokemon.append(Pokemon(name))
    return enemyPokemon

def parseEnemyPokemon(driver):
    chats = driver.find_elements_by_class_name('chat')
    otherPokemon = []

    for chat in chats:
        if "team" in chat.text:
            if username not in chat.text:
                otherPokemon = chat.text.splitlines()[1].split('/')
    return otherPokemon

def selectPokemon(driver, pokemon):
    buttons = driver.find_element_by_class_name("switchmenu").find_elements_by_tag_name("button")
    for button in buttons:
        buttonName = button.text.lower().replace(" ", "").replace("-", "")
        if buttonName in pokemon or pokemon in buttonName:
            button.click()
            print pokemon + "successfully sent out"
            return

    raise Exception("Failed to find button for " + pokemon)

def turnOnTimer(driver):
    raiseNotDefined()

def parseTheirChoice(driver):
    theirPick = ""
    for element in driver.find_elements_by_class_name('battle-history'):
        battleHistory.append(element.text)
        if "sent out" in element.text:
            theirPick = element.text.split('sent out')[1].replace(" ", "").replace("-", "").replace("!", "").lower()
            if "(" in theirPick:
                theirPick = theirPick.split("(")[1].replace(")", "")
            print theirPick
            return theirPick

def lockInMove(driver, myMove):
    over = wait(driver, 0, (lambda d, v: len(driver.find_elements_by_class_name("movecontrols")) == 0))
    if over < 0:
        return over
    buttons = driver.find_element_by_class_name("movecontrols").find_elements_by_tag_name("button")
    for move in buttons:
        if myMove in move.text or move.text in myMove:
            move.click()
            return

    for move in buttons:
        print move.text
    raise Exception("Failed to find button for " + myMove)

def waitForNextTurn(driver, currentTurn):
    turn = currentTurn
    while turn == currentTurn:
        for header in driver.find_elements_by_css_selector('h2.battle-history'):
            turn = int(header.text.split("Turn")[1])
            return turn
        for chat in driver.find_elements_by_css_selector('div.battle-history'):
            if 'botLife won the battle!' in chat.text:
                return -1
            elif 'won the battle' in chat.text:
                return -2
        print 'waiting for enemy to select move'
        time.sleep(0.5)

def getTurnInfo(driver, turn, enemyName):
    turnInfo = ['enemyMove', 0, 'damageToThem', True, 'theirMoveSuccessful']
    for chat in driver.find_elements_by_css_selector('div.battle-history'):
        text = chat.text
        if text not in battleHistory:
            battleHistory.append(text)
            if 'opposing' in text:
                if 'used' in text:
                    move = text.split("used ")[1].replace("!", "").replace(" ", "").replace("-", "").lower()
                    turnInfo[0] = move
                    db.addNewMove(move, enemyName)
                    #add to database
                elif 'avoided' in text:
                    # mymove successful
                    turnInfo[3] = False
                    # damage to them
                    turnInfo[2] = 0
    return turnInfo


def battle(driver, myPokemon):
    #get opponent's pokemon
    enemyNames = parseEnemyPokemon(driver)
    enemyPokemon = createEnemyPokemon(enemyNames)

    tree = Tree(myPokemon, enemyPokemon, db)
    myChoice =  tree.choosePokemon()

    selectPokemon(driver, myChoice)
    # wait(driver, 0, (lambda d, v: len(d.find_elements_by_class_name('battle-history')) == v))

    turn = 0
    turn = waitForNextTurn(driver, turn)
    if turn > 0:
        theirChoice = parseTheirChoice(driver)
        tree.findRootForPicked(myChoice, theirChoice)
    while turn >= 0:
        move = tree.getNextMove()
        lock = lockInMove(driver, move)
        turn = waitForNextTurn(driver, turn)
        try:
            info = getTurnInfo(driver, turn - 1, theirChoice)
            print info
        except:
            print traceback.format_exc()

        tree.correctTree(None, None, None, None, None)

def afterBattle(driver):
    time.sleep(20)
    driver.close()

def main():
    if treeTest:
        pokeText = importTeam('team1.txt')
        myPokemon = parseTeam(pokeText)
        enemyNames = ["venusaur", "tapukoko", "greninja"]
        enemyPokemon = createEnemyPokemon(enemyNames)
        tree = Tree(myPokemon, enemyPokemon, db)
        choice =  tree.choosePokemon()
        from random import randint
        randomChoice = enemyNames[randint(0,2)]
        print "Enemy chose: " + randomChoice
        tree.findRootForPicked(choice, randomChoice)
        tree.getNextMove()
        tree.correctTree(None, None, None, None, None)
        tree.getNextMove()
    else:
        driver = openBrowser()
        try:
            pokeText = importTeam('team1.txt')
            myPokemon = parseTeam(pokeText)
            inputTeam(driver, pokeText)
            login(driver)
            url = queueMatch(driver)
            wait(driver, url, (lambda d, u: u == d.current_url))
            battle(driver, myPokemon)
            afterBattle(driver)
        except:
            print traceback.format_exc()
            afterBattle(driver)


if __name__ == "__main__": main()





