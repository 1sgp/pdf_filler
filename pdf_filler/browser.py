# browser

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoAlertPresentException
from bs4 import BeautifulSoup as bs
from time import sleep

def init():
    options=Options()
    #options.add_argument('-headless')
    browser=webdriver.Firefox(options=options)
    return browser

if __name__ == "__main__":
    init()