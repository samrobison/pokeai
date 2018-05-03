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

def open_browser():
    #sign in and make team
    driver = webdriver.Chrome('chromedriver.exe')
    driver.get('http://play.pokemonshowdown.com/teambuilder');
    time.sleep(3)
    driver.find_element_by_name("backup").click()
    return driver

def mute_game(driver):
    driver.find_element_by_name('openSounds').click()
    time.sleep(2)
    driver.find_element_by_name('muted').click()
    time.sleep(1)

def import_team(fileName):
    team = ""
    with open(fileName, 'r') as myFile:
        team=myFile.read()
    return team



def login(driver):
    driver.find_element_by_name("login").click()
    driver.find_element_by_name("username").send_keys(username)
    driver.find_element_by_class_name("buttonbar").find_elements_by_tag_name("button")[0].click()
    time.sleep(1)
    driver.find_element_by_name("password").send_keys(password)
    driver.find_element_by_class_name("buttonbar").find_elements_by_tag_name("button")[0].click()
    time.sleep(1)

def queue_match(driver):
    driver.get('http://play.pokemonshowdown.com')
    time.sleep(5)

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
        print('waiting')
        time.sleep(1)
    time.sleep(4)
    return 0

def select_pokemon(driver, pokemon):
    buttons = driver.find_element_by_class_name("switchmenu").find_elements_by_tag_name("button")
    for button in buttons:
        buttonName = nameFormat(button.text)
        if buttonName in pokemon or pokemon in buttonName:
            button.click()
            print((pokemon + " successfully sent out"))
            return

    raise Exception("Failed to find button for " + pokemon)

def turn_on_timer(driver):
    raiseNotDefined()

def parse_their_choice(driver):
    theirPick = ""
    for element in driver.find_elements_by_class_name('battle-history'):
        battleHistory.append(element.text)
        if "sent out" in element.text:
            theirPick = nameFormat(element.text.split('sent out')[1].replace("!", ""))
            if "(" in theirPick:
                theirPick = theirPick.split("(")[1].replace(")", "")
            print(theirPick)
            return theirPick

def lock_in_move(driver, myMove):
    over = wait(driver, 0, (lambda d, v: len(driver.find_elements_by_class_name("movecontrols")) == 0))
    if over < 0:
        return over
    buttons = driver.find_element_by_class_name("movecontrols").find_elements_by_tag_name("button")
    for move in buttons:
        if myMove in move.text or move.text in myMove or 'recharge' in move.text:
            move.click()
            return

    for move in buttons:
        print((move.text))
    raise Exception("Failed to find button for " + myMove)

def wait_for_next_turn(driver, currentTurn):
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
        print('waiting for enemy to select move')
        time.sleep(0.5)

def get_turn_info(driver, turn, enemyName):
    global theyMissed
    global iMissed
    # def correctTree(self, enemyMove, damageToMe, damageToThem, myMoveSuccessful, theirMoveSuccessful):

    turnInfo = ['enemyMove', 0, 0, True, True]
    for chat in driver.find_elements_by_css_selector('div.battle-history'):
        text = chat.text
        if 'opposing' in text:
            info = parse_history(text, iMissed)
            turnInfo[0] = info[0] or turnInfo[0]
            turnInfo[2] = info[1] or turnInfo[2]
            turnInfo[3] = info[2] or turnInfo[3]
            if not (info[2] is not None or info[2]):
                iMissed += 1
        else:
            info = parse_history(text, theyMissed)
            turnInfo[1] = info[1] or turnInfo[1]
            turnInfo[4] = info[2] or turnInfo[4]
            if not (info[2] is not None or info[2]):
                theyMissed += 1
    print(turnInfo)
    return turnInfo

def parse_history(text, missedCount):
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
            print(damage)
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
        print("Message failed")

def parse_my_team(driver):
    battle_search = re.search('https://play.pokemonshowdown.com/(battle-gen7randombattle-\d+)', driver.current_url)
    battle_query = battle_search.group(1)
    pokemon = []
    for i in range(6):
        driver.execute_script("let button = $('.disabled')[0]; BattleTooltips.showTooltipFor('%s',%s ,'sidepokemon', button, false)"% (battle_query, str(i)))
        # pokemon_info will have a string in the form of Manaphy L76HP: 100.0% (277/277)Ability: Hydration / Item: Choice Scarf157 Atk / 196 Def / 196 SpA / 196 SpD / 196 Spe• Energy Ball• Psychic• Surf• Ice Beam
        pokemon_info = driver.find_element_by_id('tooltipwrapper').text
        print(pokemon_info)
        pokemon.append(Pokemon(my_init_string=pokemon_info))
    return pokemon

def parse_enemy_pokemon(driver):
    battle_search = re.search('https://play.pokemonshowdown.com/(battle-gen7randombattle-\d+)', driver.current_url)
    battle_query = battle_search.group(1)
    driver.execute_script("let button = $('.disabled')[0]; BattleTooltips.showTooltipFor('%s', 'your0','pokemon', button, false)"% (battle_query))
    pokemon_info = driver.find_element_by_id('tooltipwrapper').text
    print(pokemon_info)
    return []

def create_enemy_pokemon(names):
    return names

def battle(driver):
    my_pokemon = parse_my_team(driver)
    #get opponent's pokemon
    enemy_names = parse_enemy_pokemon(driver)
    enemy_pokemon = create_enemy_pokemon(enemy_names)

    tree = Tree(my_pokemon, enemy_pokemon)
    my_choice =  tree.choosePokemon()

    select_pokemon(driver, my_choice)
    # wait(driver, 0, (lambda d, v: len(d.find_elements_by_class_name('battle-history')) == v))
    turn = 0
    turn = wait_for_next_turn(driver, turn)
    print(turn)
    if turn > 0:
        their_choice = parse_their_choice(driver)
        tree.findRootForPicked(my_choice, their_choice)
        message(driver, 'Hello! I am PokeAi Version 0.1.8, Thanks for training me! \nNew this version: MDP rewards for protect modified\n')

    while turn > 0:
        print(("------------------TURN "+ str(turn) + "------------------"))
        move = tree.getNextMove()
        if  move[1] <= 0:
            message(driver, "This is awkward looks like i can't win\n")
        lock = lock_in_move(driver, move[0])
        turn = wait_for_next_turn(driver, turn)

        try:
            info = get_turn_info(driver, turn - 1, their_choice)
            tree.correctTree(info[0], info[1], info[2], info[3], info[4])
        except:
            tb = traceback.format_exc()
            print(tb)
            message(driver, 'Congratulations! You made me crash somehow. Take a look:')
            message(driver, tb)
            tree.correctTree(None, None, None, None, None)

        if turn < 0:
            return turn


def after_battle(driver):
    time.sleep(20)
    driver.close()


def main():
    initDb()
    treeTest = False
    if treeTest:
        raiseNotDefined()
    else:
        driver = open_browser()
        mute_game(driver)
        try:
            login(driver)
            for i in range(3):
                battle_history = []
                url = queue_match(driver)
                wait(driver, url, (lambda d, u: u == d.current_url))
                battle(driver)
            after_battle(driver)
        except:
            tb = traceback.format_exc()
            print(tb)
            message(driver, 'Congratulations! You made me crash somehow. Take a look:')
            message(driver, tb.replace('sam', 'someCoder'))
            after_battle(driver)


if __name__ == "__main__": main()





