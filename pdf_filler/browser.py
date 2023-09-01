# browser

from selenium import webdriver
from selenium.webdriver.firefox.options import Options

def init():
    options=Options()
    options.add_argument('-headless')
    browser=webdriver.Firefox(options=options)
    return browser

if __name__ == "__main__":
    init()
