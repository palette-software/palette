#! /usr/bin/python

import argparse
from time import sleep

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait 
from selenium.webdriver.support import expected_conditions

DEFAULT_WAIT = 3.0
DEFAULT_USERNAME = 'palette'
DEFAULT_PASSWORD = 'Tableau2014!'
parser = argparse.ArgumentParser()
parser.add_argument('baseurl', action='store',
  help='base URL, for example: http://localhost:8080')
parser.add_argument('-p', '--password', default=DEFAULT_PASSWORD,
  help='password')
parser.add_argument('-u', '--username', default=DEFAULT_USERNAME,
  help='user account name')
parser.add_argument('-w', '--wait', default=DEFAULT_WAIT,
  help='seconds to wait between page tests')
args = parser.parse_args()
BASEURL = args.baseurl
PASSWORD = args.password
USERNAME = args.username
WAIT = args.wait

LOGIN = BASEURL + '/login'
EVENT = BASEURL
ARCHIVE = BASEURL + '/workbook/archive'
MANAGE = BASEURL + '/manage'
PROFILE = BASEURL + '/profile'
LOGOUT = BASEURL + '/logout'

browser = webdriver.Chrome()

# log in (takes us to home page)
browser.get(LOGIN)
assert 'Welcome' in browser.title
elem = browser.find_element_by_name('username')
elem.send_keys(USERNAME)
elem = browser.find_element_by_name('password')
elem.send_keys(PASSWORD)
elem = browser.find_element_by_name('login')
elem.click()
def homepage(id):
    if 'Home' in browser.title:
        return True
    else:
        return False
WebDriverWait(browser, 3).until(homepage)
sleep(WAIT)

# event page (home page)
browser.get(EVENT)
assert 'Home' in browser.title
sleep(WAIT)

# workbook archive page
browser.get(ARCHIVE)
assert 'Workbook Archive' in browser.title
sleep(WAIT)

# manage page
browser.get(MANAGE)
assert 'Manage' in browser.title
sleep(WAIT)

# profile page
browser.get(PROFILE)
assert 'Profile' in browser.title
sleep(WAIT)

# log out (takes us to login page)
browser.get(LOGOUT)
assert 'Welcome' in browser.title
sleep(WAIT)

browser.quit()
