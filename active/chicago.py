# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Philosophy of Science
# FS 2019-10-28

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

publisher = 'The University of Chicago Press Books'
typecode = 'P'
jnl = sys.argv[1]
year = sys.argv[2]
vol = sys.argv[3]
issue = sys.argv[4]
hdr = {'User-Agent' : 'Magic Browser'}


jnlfilename = 'chicago.%s%s.%s' % (jnl, vol, issue)

if jnl == 'phos':
    jnlname = 'Phil.Sci.'
else:
    print 'journal not known'
    
tocurl = 'https://www.journals.uchicago.edu/toc/%s/%s/%s/%s' % (jnl, year, vol, issue)
print tocurl

driver = webdriver.PhantomJS()
driver.implicitly_wait(30)
driver.get(tocurl)
tocpage = BeautifulSoup(driver.page_source)
#print tocpage.text
recs = []
#for div in tocpage.body.find_all('div', attrs = {'class' : 'tocContent'}):
for div in tocpage.body.find_all('ul', attrs = {'class' : 'table-of-content__section-body'}):
    section = ''
    for child in div.children:
        try:
            child.name
            print child.name
        except:
            continue
        if child.name == 'h2':
            section = child.text.strip()
            print section
        elif child.name == 'h4':
            section = child.text.strip()
            print section
#        elif child.name == 'table' and not section in ['Book Reviews', 'Discussions', '', 'Essay Reviews']:
        elif child.name == 'li' and not section in ['Book Reviews', 'Discussions', 'Essay Reviews']:
            #print child
            rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'year' : year, 'tc' : 'P', 'auts' : []}
            if section:
                rec['note'] = [section]
            #title
            for span in child.find_all('span', attrs = {'class' : 'hlFld-Title'}):
                rec['tit'] = span.text.strip()
            for h5 in child.find_all('h5', attrs = {'class' : 'issue-item__title'}):
                rec['tit'] = h5.text.strip()
            #authors
            for span in child.find_all('span', attrs = {'class' : 'hlFld-ContribAuthor'}):
                rec['auts'].append(span.text.strip())                
            #pages
            divs = child.find_all('div', attrs = {'class' : 'art_meta citation'})
            if not divs:
                divs = child.find_all('div', attrs = {'class' : 'issue-item__pages'})
            for div in divs:
                divt = re.sub('[\n\t\r]', '', div.text.strip())
                pages = re.sub('.*pp. (\d.*\d).*', r'\1', divt)
                rec['p1'] = re.sub('\D.*', '', pages)
                rec['p2'] = re.sub('.*\D', '', pages)
            #DOI
            links = child.find_all('a', attrs = {'class' : 'ref'})
            if not links:
                links = child.find_all('a', attrs = {'class' : 'issue-item__btn', 'title' : 'Full Text'})                
            for a in links:
                if re.search('10.1086', a['href']):
                    rec['doi'] = re.sub('.*(10.1086)', r'\1', a['href'])
                    if re.search('\/(abs|full)\/', a['href']):
                        rec['artlink'] = 'https://www.journals.uchicago.edu' + a['href']
            #abstract
            for div in child.find_all('div', attrs = {'class' : 'issue-item__abstract'}):
                for div2 in div.find_all('div', attrs = {'class' : 'accordion__content'}):
                    rec['abs'] = div2.text.strip()
            if 'artlink' in rec.keys():
                recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    time.sleep(10)
    driver.get(rec['artlink'])
    artpage = BeautifulSoup(driver.page_source)
    #abstract
    if not 'abs' in rec.keys():
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'dc.Description'}):
            rec['abs'] = meta['content']
    #references
    #would need selenium or so
            



                                       
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
