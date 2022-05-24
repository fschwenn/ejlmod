# -*- coding: utf-8 -*-
#look for interesting IEEE-conferences

import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import codecs
import time
import datetime
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import unicodedata

ejldir = '/afs/desy.de/user/l/library/dok/ejl/backup'

rpp = 50
pages = 7
verbose = False

driver = webdriver.PhantomJS()
driver.implicitly_wait(60)
driver.set_page_load_timeout(30)

checkpagination = True

area = sys.argv[1]
    
if area in ['qis', 'QIS']:
    keywords = ["quantum computing", "quantum computer", "qubit", "quantum information", "quantum algorithm", "qudit", "variational quantum", "quantum circuit", "quantum device", "quantum sensing", "quantum sensor"]
    uninteresting = ['9601162', '9612423', '9621302', '9622894', '9623060', '9625862', '9626197',
                     '9628186', '9632864', '9633337', '9637048', '9637707', '9639075', '9639893',
                     '9639894', '9641073', '9642487', '9642488', '9643846', '9647036', '9650343',
                     '9651729', '9652585', '9653181', '9653182', '9654277', '9654796', '9662653',
                     '9666195', '9667777', '9673138', '9675837', '9678504', '9681385', '9684003',
                     '9686355', '9687823', '9691480', '9698820', '9701656', '9702520', '9703111',
                     '9703325', '9708596', '9711508', '9715739', '9717338', '9718604', '9719593',
                     '9720298', '9725360', '9726700', '9727189', '9727224', '9729251', '9730107',
                     '9731800', '9732060', '9734284', '9737724', '9740078', '9750413', '9750672',
                     '9751242', '9752770', '9754526', '9755448', '9757254', '9758393', '9615386',
                     '9619795', '9648909', '9660210', '9763565', '9730105', '9766439', '9768306']
elif area in ['hep', 'HEP']:
    keywords = ["LHC", "RHIC", "BELLE", "CERN", "DESY", "SLAC", "Fermilab", "KEK", "JINR", "NICA", "MU2E", "CALICE", "IceCube", "VIRGO"] # ILC -> iterative learning control
    uninteresting = ['9729251', '9715739', '9730107', '9745891', '9757254', '9337937', '9362508',
                     '9259608', '9263486', '9264268', '9265638', '9274797', '9276407', '9279433', 
                     '9281379', '9282733', '9285973', '9287816', '9288361', '9294155', '9295648', 
                     '9300349', '9306858', '9309528', '9312211', '9312958', '9314696', '9315292', 
                     '9326315', '9332308', '9342745', '9344050', '9365069', '9393999', '9401028', 
                     '9406783', '9407592', '9417241', '9425788', '9430855', '9431760', '9441490', 
                     '9453462', '9459012', '9465371', '9469409', '9473476', '9477294', '9480799', 
                     '9480801', '9484327', '9494148', '9495828', '9500243', '9506008', '9517313', 
                     '9518357', '9521186', '9530730', '9531994', '9549237', '9550759', '9560720', 
                     '9565594', '9566764', '9568388', '9569243', '9574041', '9577054', '9577055', 
                     '9588928', '9593288', '9598345', '9599146', '9600687', '9601161', '9605357', 
                     '9605697', '9607028', '9607382', '9612423', '9622894', '9632864', '9637048', 
                     '9637506', '9642487', '9649653', '9651729', '9652563', '9652585', '9652791', 
                     '9653181', '9704881', '9708596', '9709627', '9731800', '9732060', '9748173', 
                     '9754526', '9756129', '9385579', '9251288', '9306855', '9350666', '9477443',
                     '9546842', '9703325', '9251288', '9651276', '9768880', '9770952']

    
now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
startyear = str(now.year-2)
stopyear = str(now.year)

done = []
redoki = re.compile('.*IEEENuclSciSympConfRec.*_C(\d\d\d+).*')
for ordner in [ejldir, os.path.join(ejldir, str(now.year-1)), os.path.join(ejldir, str(now.year-2))]:
    for datei in os.listdir(ordner):
        if redoki.search(datei):
            done.append(redoki.sub(r'\1', datei))
print '%i done, %i uninteresting' % (len(done), len(uninteresting))

searchterm = '%22)%20OR%20(%22All%20Metadata%22:%22'.join(keywords)
conferences = {}
for page in range(pages):
    print '==={ %i/%i }===' % (page+1, pages)
    toclink = 'https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&matchBoolean=true&queryText=(%22All%20Metadata%22:%22' + searchterm + '%22)&highlight=true&returnType=SEARCH&matchPubs=true&sortType=newest&rowsPerPage=' + str(rpp) + '&ranges=' + startyear + '_' + stopyear + '_Year&returnFacets=ALL&pageNumber=' + str(page+1) + '&refinements=ContentType:Conferences&refinements=ContentType:Books'
    try:
        driver.get(toclink)
        #WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'icon-pdf')))
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'result-item-title')))
    except:
        print ' wait a minute'
        time.sleep(60)
        driver.get(urltrunc + toclink + pagecommand)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'global-content-wrapper')))
    #click to accept cookies
    if page == 0:
        try:
            time.sleep(1)
            driver.find_element_by_css_selector('.cc-btn.cc-dismiss').click()
        except:
            print "\033[0;91mCould not click .cc-btn.cc-dismiss\033[0m"
    time.sleep(3)
    page = BeautifulSoup(driver.page_source, features="lxml")

    for div in page.body.find_all('div', attrs = {'class' : 'List-results-items'}):
        for h2 in div.find_all('h2'):
            arttit = h2.text.strip()
            for a in h2.find_all('a'):
                artlink = 'https://ieeexplore.ieee.org' + a['href']
        for a in div.find_all('a'):
            if a.has_attr('href') and re.search('\/proceeding', a['href']):
                conftit = a.text.strip()
                confnumber = re.sub('\D', '', a['href'])
        for div2 in div.find_all('div', attrs = {'class' : 'stats-SearchResults_DocResult_ViewMore'}):
            artabs = div2.text.strip()
            for span in div2.find_all('span', attrs = {'class' : 'highlight'}):
                span.name = 'b'

            artabs = str(div2.contents[0])
        if confnumber in conferences.keys():
            conferences[confnumber]['articles'].append((arttit, artlink, artabs))
        elif confnumber in done:
            if verbose:
                print '  %s already done' % (confnumber)
        elif confnumber in uninteresting:
            if verbose:
                print '  %s not interesting' % (confnumber)
        else:
            if verbose:
                print ' ', confnumber, conftit
            conferences[confnumber] = {'title' : conftit, 'articles' : [(arttit, artlink, artabs)]}
            



ouf = codecs.EncodedFile(codecs.open('/afs/desy.de/group/library/www/html/akw/ieee_confsearch_%s.html' % (area.lower()), mode='wb'), 'utf8')
ouf.write('<html>\n <head><title>IEEE conference search (%s)</title></head>\n' % (area.upper()))
ouf.write(' <body>\n  <h2>%s: %s [%s]</h2>\n' % (area.upper(), ', '.join(keywords), stampoftoday))
ouf.write('Please add uninteresting conferences in /afs/desy.de/user/l/library/proc/ieee_confsearch.py<br>')
ouf.write('  <ol>\n')
confnumbers = conferences.keys()
confnumbers.sort()
i = 0
pagestotal = 0
for confnumber in confnumbers:
    i += 1
    if verbose:
        print '\n---{ %i/%i }---{ %s | %s }---' % (i, len(confnumbers), confnumber, conferences[confnumber]['title'])
    else:
        print '---{ %i/%i }---' % (i, len(confnumbers))
    ouf.write('   <li>\n')
    conflink = 'https://ieeexplore.ieee.org/xpl/conhome/%s/proceeding' % (confnumber)
    try:
        ouf.write('    <h3><a href="%s">%s</a></h3>\n' % (conflink, conferences[confnumber]['title']))
    except:
        ouf.write('    <h3><a href="%s">%s</a></h3>\n' % (conflink, '...'))
    numberofarticles = 0
    pagenumbers = []
    pagination = '?'
    if checkpagination:
        try:
            time.sleep(15)
            try:
                driver.get(conflink)
                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'result-item-title')))
                time.sleep(1)
                page = BeautifulSoup(driver.page_source, features="lxml")
            except:
                print "retry in 300 seconds"
                time.sleep(300)
                driver.get(conflink)
                WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'result-item-title')))
                time.sleep(1)
                page = BeautifulSoup(driver.page_source, features="lxml")
            for div in page.body.find_all('div', attrs = {'class' : 'Dashboard-header'}):
                divt = re.sub('[\n\t\r]', ' ', div.text.strip())
                divt = re.sub(',', '', divt)
                numberofarticles = int(re.sub('.* of +(\d+).*', r'\1', divt))
                pagestotal += numberofarticles
            pt = re.sub('[n\t\r]', '', page.text.strip())
            for part in re.split('Page\(s\). *',  pt)[1:]:
                pagenumbers.append(re.sub(' .*', '', part))
            if len(pagenumbers) > 20:
                spnumber = 17
            elif len(pagenumbers) > 10:
                spnumber = 10
            if pagenumbers[spnumber+1] == '1' and pagenumbers[spnumber-1] == '1' and pagenumbers[spnumber] == '1':
                pagination = 'nopag'
            elif re.search('\.', pagenumbers[spnumber]) and re.search('\.', pagenumbers[spnumber-1]):            
                pagination = 'special'
            elif int(pagenumbers[spnumber+1]) != int(pagenumbers[spnumber]) and int(pagenumbers[spnumber-1]) != int(pagenumbers[spnumber]):
                pagination = 'pag'
            
        except:
            pass
        if verbose:
            print ' ', numberofarticles, pagination
    ouf.write('    <ol>\n')
    for (arttit, artlink, artabs) in conferences[confnumber]['articles']:
        #print '-', arttit, artlink
        try:
            ouf.write('     <li><a href="%s">%s</a><br>' % (artlink, arttit))
        except:
            ouf.write('     <li><a href="%s">%s</a><br>' % (artlink, '...'))
        try:
            ouf.write(artabs)
        except:
            pass
        ouf.write('</li>\n')
    ouf.write('    </ol><br>\n')
    if checkpagination:
        ouf.write('    /home/library/.virtualenvs/inspire/bin/python $afl/proc/ieee_crawler.xml.py C%s # %i %s' % (confnumber, numberofarticles, pagination))
    else:
        ouf.write('    /home/library/.virtualenvs/inspire/bin/python $afl/proc/ieee_crawler.xml.py C%s' % (confnumber))
    try:
        ouf.write(' ## %s\n' % (conferences[confnumber]['title']))
    except:
        pass
    ouf.write('   </li>\n')
ouf.write('  </ol>\n')
if checkpagination:
    ouf.write('%i conference papers in total' % (pagestotal))

ouf.write(' </body>\n</html>')

print '\nhttp://www-library.desy.de/akw/ieee_confsearch_%s.html\n' % (area.lower())
