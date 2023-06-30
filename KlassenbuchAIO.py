# Klassenbuchscraper AiO Package
# version 0.2.1 ALPHA for 'pdf_filler' by mxwmnn
# 06/30/2023

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from bs4 import BeautifulSoup
from bs4 import re
import getpass
import os
import sys
import time

options=Options()
options.add_argument('-headless')
browser = webdriver.Firefox(options=options)

def countdown():
    time.sleep(1)
    print('')
    print('10 seconds left before refreshing.')
    time.sleep(5)   
    print('5')
    time.sleep(1)
    print('4')
    time.sleep(1)
    print('3')
    time.sleep(1)
    print('2')
    time.sleep(1)
    print('1')
    time.sleep(1)

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def enterCreds():
    print("Please enter your credentials. You may correct them, when the login doesn't work.")
    User = input('Username: ')
    Pass = getpass.getpass(prompt='Password: ')
    if User == "":
        print('Please enter a username.')
        User = input('Username: ')
    elif Pass == "":
        Pass = getpass.getpass(prompt='Please enter a password: ')
    else:
        print('Credentials accepted.')
    time.sleep(1)
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
        time.sleep(3)
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
        time.sleep(1)
        if "Ungültige Anmeldedaten. Versuchen Sie es noch einmal!" in browser.page_source:
            print("Wrong credentials. Please check your input!")
            User, Pass = checkCreds(User, Pass)
            time.sleep(2)
            loginUser(User, Pass)
        else:
            logged_in = True
            print('Login successful!')
            return
    except NoSuchElementException:
        print('Already signed in.')
        logged_in = True
        return logged_in

def print_menu(regal):
    for key in regal.keys():
        print (key, '--', regal[key])

def Kursmenu():
    menu_options_kurse = {
    0: 'Exit'
}
    global Kurse
    Kurse = {}    
    browser.get('https://lernplattform.gfn.de/my/')
    soup = BeautifulSoup(browser.page_source, 'html.parser')
    kurssuppe = soup.find_all('a', class_='list-group-item')
    ikurse = 0
    for kurs in kurssuppe:
        ikurse = ikurse + 1
        href = kurs['href']
        text = kurs.find('span').text
        menu_options_kurse[ikurse] = text
        Kurse[ikurse] = href   
    print_menu(menu_options_kurse)
    choice = input('Choose which Klassenbuch of the listed Kurse above you want to scrape: ')
    return choice
    
def Kurswahl(choice):
    linkstr = Kurse[int(choice)] + '&section=5'
    browser.get(linkstr)
    klassenbuchelement = browser.find_element(By.CLASS_NAME, 'activitytitle')
    klassenbuchelement.click()
    table = browser.find_element(By.CLASS_NAME, 'boxaligncenter')
    daten = table.find_elements(By.CLASS_NAME, 'datecol')
    descr = table.find_elements(By.CLASS_NAME, 'desccol')
    d = 0
    classbook = {}
    for x in daten:        
        Tag = x.text
        Data = descr[d].text
        classbook[d] = {f'{Tag} : {Data}'}            
        d = d + 1
    time.sleep(1)
    return classbook

useri, passi = enterCreds()
loginUser(useri, passi)
time.sleep(1)
clear()

while True:
    clear()
    choice = Kursmenu()

    if choice == '0':
        time.sleep(0.5)
        clear()
        print('Goodbye! Feel free to submit your Feedback!')
        print('https://github.com/mxwmnn/pdf_filler')
        time.sleep(2)
        browser.quit()
        break

    else:
        output = Kurswahl(choice)
        for x in output:
            print(output[x])

    countdown()
