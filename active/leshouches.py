# -*- coding: UTF-8 -*-
#program to harvest Les Houches Lect.Notes   
# FS 2019-08-05


import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'Oxford Scholarship Online'
toclink = sys.argv[1]
cnum = sys.argv[2]

driver = webdriver.PhantomJS()
driver.implicitly_wait(30)
driver.get(toclink)
tocpage = BeautifulSoup(driver.page_source)


recs = []
for title in tocpage.head.find_all('title'):
    tt = title.text.strip()
    if re.search('Volume', tt):
        for div in tocpage.find_all('div', attrs = {'class' : 'contentItem'}):
            for a in div.find_all('a'):
                rec = {'jnl' : 'Les Houches Lect.Notes', 'tc' : 'C', 'cnum' : cnum,
                       'auts' : []}
                rec['vol'] = re.sub('.* Volume (\d+).*', r'\1', tt)
                rec['artlink'] = 'https://www.oxfordscholarship.com' + a['href']
                recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    driver.get(rec['artlink'])
    artpage = BeautifulSoup(driver.page_source)
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #keywords
            if meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split(' *; *', meta['content'])
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #abstract
            elif meta['name'] == 'description':
                rec['abs'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['auts'].append(meta['content'])
    for div in artpage.body.find_all('div', attrs = {'class' : 'bibliography'}):
        for p in div.find_all('p'):
            pt = p.text.strip()
            #DOI
            if re.search('DOI:', pt):
                rec['doi'] = re.sub('.*?(10\..*)', r'\1', pt)
            #year
            elif re.search('Print publication date', pt):
                rec['year'] = re.sub('.*?(20\d\d).*', r'\1', pt)


jnlfilename = 'leshouches%s' % (rec['vol'])
  
#write xml
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
