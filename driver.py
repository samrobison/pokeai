import time
import re
from selenium import webdriver
from movedex import MoveDex
from tree import Tree
from Pokemon import Pokemon
from Pokemon import Move

#sign in and make team
username = "botLife"
password = "aiiscool"

driver = webdriver.Chrome('./chromedriver')
driver.get('http://play.pokemonshowdown.com/teambuilder');
time.sleep(3)
driver.find_element_by_name("backup").click()
team = ""

with open('team1.txt', 'r') as myfile:
    team=myfile.read()

#get my pokemon
myPokemon = []
name = team.splitlines()[2].split('@')[0].replace(" ", "").replace("-", "").lower()
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
MoveDex[move1]['name'] = move1
MoveDex[move2]['name'] = move2
MoveDex[move3]['name'] = move3
MoveDex[move4]['name'] = move4

moves = [MoveDex[move1], MoveDex[move2], MoveDex[move3], MoveDex[move4]]
myPokemon.append(Pokemon(name, abil=ability, moves=moves, stat=stats))

name = team.splitlines()[11].split('@')[0].replace(" ", "").replace("-", "").lower()
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
MoveDex[move1]['name'] = move1
MoveDex[move2]['name'] = move2
MoveDex[move3]['name'] = move3
MoveDex[move4]['name'] = move4
moves = [MoveDex[move1], MoveDex[move2], MoveDex[move3], MoveDex[move4]]
myPokemon.append(Pokemon(name, abil=ability, moves=moves, stat=stats))

name = team.splitlines()[20].split('@')[0].replace(" ", "").replace("-", "").lower()
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
MoveDex[move1]['name'] = move1
MoveDex[move2]['name'] = move2
MoveDex[move3]['name'] = move3
MoveDex[move4]['name'] = move4
moves = [MoveDex[move1], MoveDex[move2], MoveDex[move3], MoveDex[move4]]
myPokemon.append(Pokemon(name, abil=ability, moves=moves, stat=stats))

#back to inputing team

driver.find_elements_by_class_name('textbox')[0].send_keys(team)
driver.find_element_by_name("saveBackup").click()

driver.find_element_by_name("login").click()
driver.find_element_by_name("username").send_keys(username)
driver.find_element_by_class_name("buttonbar").find_elements_by_tag_name("button")[0].click()
time.sleep(1)
driver.find_element_by_name("password").send_keys(password)
driver.find_element_by_class_name("buttonbar").find_elements_by_tag_name("button")[0].click()
time.sleep(1)
driver.get('http://play.pokemonshowdown.com')
time.sleep(1)
driver.find_element_by_name("format").click()
driver.find_elements_by_class_name("popupmenu")[1].find_elements_by_tag_name("li")[4].click()

url = driver.current_url

driver.find_element_by_name("search").click()

while driver.current_url == url:
    time.sleep(1)


#get oppenents pokemon

chats = driver.find_elements_by_class_name('chat')

otherPokemon = []

for chat in chats:
    if "team" in chat.text:
        if username not in chat.text:
            otherPokemon =  chat.text.splitlines()[1].split('/')

enemyPokemon = []
for p in otherPokemon:
    name = str(p)
    name = name.lower()
    name = name.replace(" ", "").replace("-", "")
    enemyPokemon.append(Pokemon(name))


tree = Tree(myPokemon, enemyPokemon)

choice =  tree.shortestPath(tree.rootNode)
print choice
#select pokemon
buttons = driver.find_element_by_class_name("switchmenu").find_elements_by_tag_name("button")
for button in buttons:
    if button.text.lower().replace(" ", "").replace("-", "") == choice[0]:
        button.click()

#loop

#end
time.sleep(5)

#clean up
driver.find_element_by_name("closeRoom").click()
time.sleep(1)
driver.find_elements_by_tag_name("button")[0].click()
driver.close()
