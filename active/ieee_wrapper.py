# -*- coding: utf-8 -*-
#FS: Harvesting coordinating program that checks for new issues of IEEE journals

import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import codecs
import time
import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

ejdir = '/afs/desy.de/user/l/library/dok/ejl'
jlist = '/afs/desy.de/user/l/library/lists/journals_to_check_regularly_by_hand'
host = os.uname()[1]
if host == 'inspire3.desy.de':
    pythonkommando = '/home/library/.virtualenvs/inspire/bin/python'
else:
    pythonkommando = 'python'

kommando = '/afs/desy.de/user/l/library/proc/ieee_crawler.xml.py'

driver = webdriver.PhantomJS()
driver.implicitly_wait(30)
today = datetime.datetime.now()
pryear = str(today.year - 1)
stampoftoday = '%4d-%02d-%02d' % (today.year, today.month, today.day)

#go through list of journals and pick IEEE ones
def gothroughjlist():
    tocheck = []
    os.system('cp %s %s.bak.%s' % (jlist, jlist, stampoftoday))
    inf = open(jlist, 'r')
    for line in inf.readlines():
        if re.search('ieee.*isnumber', line):
            tocheck.append(tuple(re.split(' *; *', line.strip())))
    inf.close()
    return tocheck

#check backup directories for specific journal
def readbackup(jnl):
    done = []
    rejnl = re.compile('.*'+jnl+'.*_(\d\d\d\d\d+).*')
    for subdir in ['backup', 'onhold', 'backup/' + pryear, 'zu_punkten', 'zu_punkten/enriched']:
        for datei in os.listdir(os.path.join(ejdir, subdir)):
            if rejnl.search(datei):
                done.append(rejnl.sub(r'\1', datei))
    return done

#compare the journal's web page with already processed files
def comparewebwithbackup(tocheck):
    todo = []
    for (jnl, link, command, date) in tocheck:
        print jnl, link
        done = readbackup(re.sub('[ \.]', '', jnl).lower())
        driver.get(link)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'accordion-chevron')))
        page = BeautifulSoup(driver.page_source)
        (newisns, oldisns) = ([], [])
        for a in page.body.find_all('a'):
            if a.has_attr('href') and re.search('isnumber', a['href']) and re.search('Issue \d', a.text):
                isn = re.sub('.*isnumber=(\d+).*', r'\1', a['href'])
                if isn in done:
                    oldisns.append(isn)
                else:
                    newisns.append((isn, jnl))
        if oldisns:
            print ' done:', oldisns, 'todo:', newisns
            #new ones found and sure there is no gap
            if newisns and len(newisns) >= 2:
                minisn = min([int(isn[0]) for isn in newisns])
                for isn in newisns:
                    if int(isn[0]) != minisn:
                        todo.append(isn)
                        print ' added ', isn
            #nothing new found
            else:
                todo.append((0, jnl))                
        else:
            #no old ones found -> not sure whether there is a gap
            print ' check manually:', newisns
            todo.append((-1, jnl))
        time.sleep(15)
    return todo

#start harvesting and update journal list
def harvest(todo):
    for (isn, jnl) in todo:
        print jnl, isn
        if isn > 0:
            print '  %s %s %s' % (pythonkommando, kommando, isn)
            os.system('%s %s %s' % (pythonkommando, kommando, isn))
        inf = open(jlist, 'r')
        lines = inf.readlines()
        inf.close()
        ouf = open(jlist, 'w')
        for line in lines:
            if re.search(jnl, line):
                if isn >= 0:
                    ouf.write(re.sub('(.*);.*', r'\1;', line.strip()))
                    ouf.write(stampoftoday+'\n')
                else:
                    ouf.write(line.strip() + ' CHECK MANUALLY\n')
            else:
                ouf.write(line)
        ouf.close()
    return


if __name__ == '__main__':
    tocheck = gothroughjlist()
    todo = comparewebwithbackup(tocheck)
    harvest(todo)
    print 'FINISHED'


    
