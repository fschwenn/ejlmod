# -*- coding: utf-8 -*-
#harvest theses from Bangalore, Indian Inst. Sci.
#FS: 2021-02-10

import getopt
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
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Bangalore, Indian Inst. Sci.'
rpp = 50
numofpages = 1

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for i in range(numofpages):
    tocurl = 'http://etd.iisc.ac.in/handle/2005/44/browse?rpp=' + str(rpp) + '&sort_by=3&type=title&offset=' + str(rpp*i) + '&etal=-1&order=DESC'
    print '---{ %i/%i }---{ %s }------' % (i+1, numofpages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(10)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : []}
            rec['link'] = 'http://etd.iisc.ac.in' + a['href']
            rec['doi'] = '20.2000/IISC/' + re.sub('\/handle\/', '', a['href'])
            rec['tit'] = a.text.strip()
            recs.append(rec)

driver = webdriver.PhantomJS()
driver.implicitly_wait(30)

jnlfilename = 'THESES-IISC-%s' % (stampoftoday)
j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['link'])
    try:
        driver.get(rec['link'])
        artpage = BeautifulSoup(driver.page_source)
    except:
        print 'wait a minute'
        time.sleep(60)
        driver.get(rec['link'])
        artpage = BeautifulSoup(driver.page_source)
    time.sleep(5)
    #author
    for meta in artpage.find_all('meta', attrs = {'name' : 'citation_author'}):
        rec['autaff'] = [[ meta['content'], publisher ]]
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'] += re.split('[,;] ', meta['content'])
    print '  ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()


