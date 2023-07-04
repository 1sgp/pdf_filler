# Klassenbuchscraper AiO Package
# version 0.6 ALPHA for 'pdf_filler' by mxwmnn
# 07/04/2023

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from bs4 import re
from time import sleep
import getpass
import os
import sys

# add username and password for automation
# useri = 'name@domain.com'
# passi = 'Password'

options=Options()
options.add_argument('-headless')
browser = webdriver.Firefox(options=options)

def countdown(x):
    sleep(1)
    print('')
    sleep(1)
    print(f'{x}', "seconds left before refreshing.", end="\r")
    sleep(1)
    for count in range(x, 1, -1):   
        print(f'{count}', "seconds left before refreshing.", end='\r')
        sleep(1)
    print("1 second left before refreshing.", end='\r')
    sleep(1)
    sleep(0.2)
    print('')
    print("Refreshing..")
    sleep(0.8)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def enterCreds():
    print("Please enter your credentials. You may correct them, if the login doesn't work.")
    User = input('Username: ')
    Pass = getpass.getpass(prompt='Password: ')
    if User == "":
        print('Please enter a username.')
        User = input('Username: ')
    if Pass == "":
        Pass = getpass.getpass(prompt='Please enter a password: ')
    else:
        print('Credentials accepted.')
    sleep(1)
    clear()
    return User, Pass

def checkCreds(User, Pass):
    if User == "":
        User = input('Username: ')
    else:
        print('Username: ', User)
        changeit = input('Do you want to change the username? (N/Y):')
        if changeit.lower() == "y":
            User = input('Username: ')
            clear()
            print(User)
    if Pass == "":
        print('Please enter a valid password')
        Pass = getpass.getpass(prompt='Enter a password please: ')
    else:
        pwc = input('Do you want to VISIBLY check your password? (N/Y):')       
    if pwc.lower() == "y":
        print('Username: ', User)
        print('Password: ', Pass)
        sleep(3)
        clear()      
    pwr = input('Do you want to change your password? (N/Y):') 
    if pwr.lower() == "y":
        Pass = getpass.getpass(prompt='Enter a new password please: ')          
    return User, Pass

def loginUser(User, Pass):
    try:
        browser.get("https://lernplattform.gfn.de/login/index.php")
        username = browser.find_element(By.ID, 'username')
        password = browser.find_element(By.ID, 'password')
        loginbut = browser.find_element(By.CLASS_NAME, 'btn-primary')
        print("Logging in ..")
        username.clear()
        username.send_keys(User)
        password.clear()
        password.send_keys(Pass)
        loginbut.click()
        sleep(1)
        if "Ungültige Anmeldedaten. Versuchen Sie es noch einmal!" in browser.page_source:
            print("Wrong credentials. Please check your input!")
            User, Pass = checkCreds(User, Pass)
            sleep(1.5)
            loginUser(User, Pass)
        else:
            logged_in = True
            print('Login successful!')
            return
    except NoSuchElementException:
        print('Already signed in.')
        logged_in = True
        return logged_in

def Kursmenu():
    global Kurse
    Kurse = {}    
    browser.get('https://lernplattform.gfn.de/my/')
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    kurse_els = soup.find_all('a', class_='list-group-item')
    for kurs in kurse_els:
        kursname = kurs.find('span').text
        if kursname.startswith("LF", 0,2):
            href = kurs['href']
            Kurse[kursname] = href
        else:
            continue
    return Kurse
    
def klassenbucher(Kurse):
    classbooks = {}
    for key in Kurse.keys():
        linkstr = Kurse[key] + '&section=5'
        sleep(0.1)
        browser.get(linkstr)
        klassenbuchelement = browser.find_element(By.CLASS_NAME, 'activitytitle')
        klassenbuchelement.click()
        sleep(0.5)
        anzeigelink = browser.current_url + '&view=5'
        browser.get(anzeigelink)
        sleep(1)
        actualpage = BeautifulSoup(browser.page_source, 'html.parser')
        tables = actualpage.find_all('table')
        daten = tables[1].find_all('td', 'datecol cell c0')
        desc = tables[1].find_all('td', 'desccol cell c1')
        classbook = {}
        d=0
        for x in daten:
            Datum = x.text
            Data = desc[d].text
            classbook[Datum] = Data
            classbooks[key] = classbook
            d = d + 1
            sleep(1)
    return classbooks

useri, passi = enterCreds()
loginUser(useri, passi)
sleep(1)
clear()
Kurse = Kursmenu()
output = klassenbucher(Kurse)

while True:
    clear()
    print(output)
    countdown(10)