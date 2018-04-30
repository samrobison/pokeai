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
from database import *

battleHistory = []
theyMissed = 0
iMissed = 0

def openBrowser():
    #sign in and make team
    driver = webdriver.Chrome('./chromedriver')
    driver.get('http://play.pokemonshowdown.com/teambuilder');
    time.sleep(3)
    driver.find_element_by_name("backup").click()
    return driver

def muteGame(driver):
    driver.find_element_by_name('openSounds').click()
    time.sleep(2)
    driver.find_element_by_name('muted').click()
    time.sleep(1)

def importTeam(fileName):
    team = ""
    with open(fileName, 'r') as myFile:
        team=myFile.read()
    return team

def parseTeam(team):
    #get my pokemon
    #pokemon 1
    myPokemon = []
    name = nameFormat(team.splitlines()[2].split('@')[0])
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
    move1 = nameFormat(team.splitlines()[6])
    move2 =  nameFormat(team.splitlines()[7])
    move3 =  nameFormat(team.splitlines()[8])
    move4 =  nameFormat(team.splitlines()[9])

    moves = [MoveDex[move1], MoveDex[move2], MoveDex[move3], MoveDex[move4]]
    myPokemon.append(Pokemon(name, abil=ability, moves=moves, stat=stats, itemHeld=item))

    #pokemon 2
    name = nameFormat(team.splitlines()[11].split('@')[0])
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
    move1 = nameFormat(team.splitlines()[15])
    move2 = nameFormat(team.splitlines()[16])
    move3 = nameFormat(team.splitlines()[17])
    move4 = nameFormat(team.splitlines()[18])

    moves = [MoveDex[move1], MoveDex[move2], MoveDex[move3], MoveDex[move4]]
    myPokemon.append(Pokemon(name, abil=ability, moves=moves, stat=stats, itemHeld=item))

    #pokemon 3
    name = nameFormat(team.splitlines()[20].split('@')[0])
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
    move1 = nameFormat(team.splitlines()[24])
    move2 = nameFormat(team.splitlines()[25])
    move3 = nameFormat(team.splitlines()[26])
    move4 = nameFormat(team.splitlines()[27])

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
        name = nameFormat(str(p))

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
        buttonName = nameFormat(button.text)
        if buttonName in pokemon or pokemon in buttonName:
            button.click()
            print pokemon + " successfully sent out"
            return

    raise Exception("Failed to find button for " + pokemon)

def turnOnTimer(driver):
    raiseNotDefined()

def parseTheirChoice(driver):
    theirPick = ""
    for element in driver.find_elements_by_class_name('battle-history'):
        battleHistory.append(element.text)
        if "sent out" in element.text:
            theirPick = nameFormat(element.text.split('sent out')[1].replace("!", ""))
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
        if myMove in move.text or move.text in myMove or 'recharge' in move.text:
            move.click()
            return

    for move in buttons:
        print move.text
    raise Exception("Failed to find button for " + myMove)

def waitForNextTurn(driver, currentTurn):
    turn = currentTurn
    while turn == currentTurn:
        for header in driver.find_elements_by_css_selector('h2.battle-history'):
            t = int(header.text.split("Turn ")[1])
            if t > turn:
                turn = t
                return t
        for chat in driver.find_elements_by_css_selector('div.battle-history'):
            if 'botLife won the battle!' in chat.text:
                message(driver, 'GG. Getting smarter every game! \n')
                return -1
            elif 'won the battle' in chat.text:
                message(driver, "Looks like humans are still better... for now  \n")
                return -2
        print 'waiting for enemy to select move'
        time.sleep(0.5)

def getTurnInfo(driver, turn, enemyName):
    global theyMissed
    global iMissed
    # def correctTree(self, enemyMove, damageToMe, damageToThem, myMoveSuccessful, theirMoveSuccessful):

    turnInfo = ['enemyMove', 0, 0, True, True]
    for chat in driver.find_elements_by_css_selector('div.battle-history'):
        text = chat.text
        if 'opposing' in text:
            info = parseHistory(text, iMissed)
            turnInfo[0] = info[0] or turnInfo[0]
            turnInfo[2] = info[1] or turnInfo[2]
            turnInfo[3] = info[2] or turnInfo[3]
            if not (info[2] is not None or info[2]):
                iMissed += 1
        else:
            info = parseHistory(text, theyMissed)
            turnInfo[1] = info[1] or turnInfo[1]
            turnInfo[4] = info[2] or turnInfo[4]
            if not (info[2] is not None or info[2]):
                theyMissed += 1
    print turnInfo
    return turnInfo

def parseHistory(text, missedCount):
    turnInfo = [None, None, None] #[move, damage, successful]
    if text not in battleHistory:
        avoided = 0
        if 'used' in text and 'opposing' in text:
            move = nameFormat(text.split("used ")[1].replace("!", ""))
            turnInfo[0] = move
            # print "Move to add: " + move
            # addNewMove(move, enemyName)
            # battleHistory.append(text)
            # add to database
        elif 'avoided' in text:
            avoided += 1
            if avoided > missedCount:
                turnInfo[2] = False
                turnInfo[1] = 0
                missedCount += 1
        if 'lost' in text and 'some of its HP' not in text:
            damage = text.split("lost ")[1].replace("% of its health!", "")
            print damage
            damage = float(damage)
            if turnInfo[1] is None:
                turnInfo[1] = 0
            turnInfo[1] += damage
            battleHistory.append(text)
        else:
            battleHistory.append(text)
    return turnInfo


def message(driver, message):
    messageArea = driver.find_element_by_class_name('chatbox').find_elements_by_tag_name('textarea')[1]
    try:
        if messageArea != None:
            messageArea.send_keys(message)
    except:
        print "Message failed"
def battle(driver, myPokemon):
    #get opponent's pokemon
    enemyNames = parseEnemyPokemon(driver)
    enemyPokemon = createEnemyPokemon(enemyNames)

    tree = Tree(myPokemon, enemyPokemon)
    myChoice =  tree.choosePokemon()

    selectPokemon(driver, myChoice)
    # wait(driver, 0, (lambda d, v: len(d.find_elements_by_class_name('battle-history')) == v))

    turn = 0
    turn = waitForNextTurn(driver, turn)
    print turn
    if turn > 0:
        theirChoice = parseTheirChoice(driver)
        tree.findRootForPicked(myChoice, theirChoice)
        message(driver, 'Hello! I am PokeAi Version 0.1.8, Thanks for training me! \nNew this version: MDP rewards for protect modified\n')

    while turn > 0:
        print "------------------TURN "+ str(turn) + "------------------"
        move = tree.getNextMove()
        if  move[1] <= 0:
            message(driver, "This is awkward looks like i can't win\n")
        lock = lockInMove(driver, move[0])
        turn = waitForNextTurn(driver, turn)

        try:
            info = getTurnInfo(driver, turn - 1, theirChoice)
            tree.correctTree(info[0], info[1], info[2], info[3], info[4])
        except:
            tb = traceback.format_exc()
            print tb
            message(driver, 'Congratulations! You made me crash somehow. Take a look:')
            message(driver, tb)
            tree.correctTree(None, None, None, None, None)

        if turn < 0:
            return turn


def afterBattle(driver):
    time.sleep(20)
    driver.close()


def main():
    initDb()
    treeTest = False
    if treeTest:
        pokeText = importTeam('team1.txt')
        myPokemon = parseTeam(pokeText)
        enemyNames = ["venusaur", "tapukoko", "greninja"]
        enemyPokemon = createEnemyPokemon(enemyNames)
        tree = Tree(myPokemon, enemyPokemon)
        choice =  tree.choosePokemon()
        from random import randint
        # randomChoice = enemyNames[randint(0,2)]
        randomChoice = enemyNames[2]
        print "Enemy chose: " + randomChoice
        tree.findRootForPicked(choice, randomChoice)
        tree.getNextMove()
        # def correctTree(self, enemyMove, damageToMe, damageToThem, myMoveSuccessful, theirMoveSuccessful):
        tree.correctTree('fusionbolt', 70.0, 0, False, True)
        tree.getNextMove()
    else:
        driver = openBrowser()
        muteGame(driver)
        try:
            pokeText = importTeam('team1.txt')
            myPokemon = parseTeam(pokeText)
            inputTeam(driver, pokeText)
            login(driver)
            for i in range(3):
                battleHistory = []
                url = queueMatch(driver)
                wait(driver, url, (lambda d, u: u == d.current_url))
                battle(driver, myPokemon)
            afterBattle(driver)
        except:
            tb = traceback.format_exc()
            print tb
            message(driver, 'Congratulations! You made me crash somehow. Take a look:')
            message(driver, tb.replace('sam', 'someCoder'))
            afterBattle(driver)


if __name__ == "__main__": main()





