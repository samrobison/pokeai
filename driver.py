import time
import re
from selenium import webdriver
from movedex import MoveDex

username = "botLife"
password = "aiiscool"

driver = webdriver.Chrome('./chromedriver')
driver.get('http://play.pokemonshowdown.com/teambuilder');
time.sleep(3)
driver.find_element_by_name("backup").click()
team = ""

with open('team1.txt', 'r') as myfile:
    team=myfile.read()

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
myPokemon = []

print len(chats)
for chat in chats:
    if "team" in chat.text:
        if username not in chat.text:
            print chat.text
            otherPokemon =  chat.text.splitlines()[1].split('/')

enemyPokemon = []
for p in otherPokemon:
    a = p.encode('ascii', 'ignore')
    a = p.lower()
    a = p.replace(" ", "")
    enemyPokemon.append(a)

print enemyPokemon

time.sleep(5)

#clean up
driver.find_element_by_name("closeRoom").click()
time.sleep(1)
driver.find_elements_by_tag_name("button")[0].click()
driver.close()
