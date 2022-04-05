# -*- coding: utf-8 -*-
#harvest theses from Virginia U.
#FS: 2021-11-15

import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options
import requests

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Virginia U.'
deps = [('Physics+-+Graduate+School+of+Arts+and+Sciences', ''),
        ('Department+of+Physics', ''),
        ('Mathematics+-+Graduate+School+of+Arts+and+Sciences', 'm'),
        ('Astronomy', 'a'),
        ('Department+of+Astronomy', '')]
startday = '%4d-01-01' % (now.year-2)
endday = '%4d-12-31' % (now.year)
rpp = 20
boringdegrees = ['BA (Bachelor of Arts)', 'MA (Master of Arts)',
                 'MS (Master of Science)', 'BS (Bachelor of Science)']
        
#driver
opts = Options()
opts.add_argument("--headless")
caps = webdriver.DesiredCapabilities().FIREFOX
caps["marionette"] = True
driver = webdriver.Firefox(options=opts, capabilities=caps)
driver.implicitly_wait(30)
driver.set_window_position(0, 0)
driver.set_window_size(1920, 10800)

prerecs = []
jnlfilename = 'THESES-VIRGINIA-%s' % (stampoftoday)
for (dep, fc) in deps:
    numofreloads = 0
    tocurl = 'https://search.lib.virginia.edu/?mode=advanced&q=date:+{' + startday + '+TO+' + endday + '}&pool=uva_library&sort=SortDatePublished_desc&filter={%22FilterResourceType%22:[%22Theses%22],%22FilterCollection%22:[%22Libra+Repository%22],%22FilterDepartment%22:[%22' + dep + '%22]}'
    print '==={ %s }==={ %s }===' % (dep, tocurl)
    try:
        driver.get(tocurl)
        time.sleep(10)
        tocpage = BeautifulSoup(driver.page_source, features="lxml")
    except:
        time.sleep(180)
        driver.get(tocurl)
        time.sleep(10)
        tocpage = BeautifulSoup(driver.page_source, features="lxml")
    for span in tocpage.find_all('span', attrs = {'class' : 'total'}):
        numoftheses = int(re.sub('\D', '', span.text.strip()))
        numofreloads = (numoftheses-1) / rpp
        print '   %i theses waiting' % (numoftheses)
    for i in range(numofreloads):
        time.sleep(10)
        print '       click for more result %i/%i' % (i+1, numofreloads)
        if len(driver.find_elements_by_css_selector('.v4-button.pure-button.pure-button-primary')) == 4:
            print '         click!'
            driver.find_elements_by_css_selector('.v4-button.pure-button.pure-button-primary')[-1].click()    
    tocpage = BeautifulSoup(driver.page_source, features="lxml")
    time.sleep(10)
    for div in tocpage.find_all('div', attrs = {'class' : 'access-urls'}):
        for a in div.find_all('a'):
            rec = {'jnl' : 'BOOK', 'tc' : 'T', 'note' : []}
            if fc:
                rec['fc'] = fc
            rec['artlink'] = a['href']
            rec['doi'] = re.sub('.*org\/', '', a['href'])
            prerecs.append(rec)
    print '   %i theses so far' % (len(prerecs))
    time.sleep(10)
       
i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        driver.get(rec['artlink'])
        artpage = BeautifulSoup(driver.page_source, features="lxml")
    except:
        print '   wait 5 minutes'
        time.sleep(300)
        driver.get(rec['artlink'])
        artpage = BeautifulSoup(driver.page_source, features="lxml")
    time.sleep(10)
    for div in artpage.find_all('div', attrs = {'id' : 'document'}):
        #title
        for h1 in div.find_all('h1'):
            rec['tit'] = h1.text.strip()
            h1.decompose()
        for d2 in div.find_all('div'):
            orcid = False
            for a in d2.find_all('a'):
                if a.has_attr('href') and re.search('orcid.org', a['href']):
                    orcid = re.sub('.*org\/', 'ORCID:', a['href'])
                a.decompose()
            for span in d2.find_all('span', attrs = {'class' : 'document-label'}):
                label = span.text.strip()
            for span in d2.find_all('span', attrs = {'class' : 'document-value'}):
                #author and affiliation
                if label == 'Author:':
                    parts = re.split(', ', span.text.strip())
                    if orcid:
                        rec['autaff'] = [[ '%s, %s' % (parts[0], parts[1]), orcid, ', '.join(parts[2:]) ]]
                    else:
                        rec['autaff'] = [[ '%s, %s' % (parts[0], parts[1]), ', '.join(parts[2:]) ]]
                #Supervisor
                elif label == 'Advisor:':
                    parts = re.split(', ', span.text.strip())
                    if len(parts) > 2:
                        rec['supervisor'] = [[ '%s, %s' % (parts[0], parts[1]), ', '.join(parts[2:]) ]]
                    else:
                        rec['supervisor'] = [[ span.text.strip() ]]
                elif label == 'Advisors:':
                    rec['supervisor'] = []
                    for br in span.find_all('br'):
                        br.replace_with('XXX')
                    for sv in re.split('XXX', span.text.strip()):
                        if sv:
                            parts = re.split(', ', sv.strip())
                            if len(parts) > 2:
                                rec['supervisor'].append([ '%s, %s' % (parts[0], parts[1]), ', '.join(parts[2:]) ])
                            else:
                                rec['supervisor'].append([ sv ])
                #abstract
                elif label == 'Abstract:':
                    rec['abs'] = span.text.strip()
                #degree
                elif label == 'Degree:':
                    degree = span.text.strip()
                    if not degree  == 'PHD (Doctor of Philosophy)':
                        if degree in boringdegrees:
                            print '   skip %s' % (degree)
                            keepit = False
                        else:
                            rec['note'].append(degree)
                #keywords
                elif label == 'Keywords:':
                    rec['keyw'] = re.split(', ', span.text.strip())
                #rights
                elif label == 'Rights:':
                    for a in span.find_all('a'):
                        if a.has_attr('href') and re.search('creativecommons', a['href']):
                            rec['license'] = {'url' : a['href']}
                    rec['note'].append(span.text.strip())
                #date
                elif label == 'Issued Date:':
                    rec['date'] = span.text.strip()
    #fulltext
    for div in artpage.find_all('div', attrs = {'id' : 'uploads'}):
        for a in div.find_all('a'):
            if a.has_attr('href') and re.search('pdf$', a['href']):
                if 'license' in rec.keys():
                    rec['FFT'] = 'https://libraetd.lib.virginia.edu' + a['href']
                else:
                    rec['hidden'] = 'https://libraetd.lib.virginia.edu' + a['href']
    if keepit:
        print '    ', rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
