# -*- coding: utf-8 -*-
#harvest British Columbia U.
#FS: 2020-02-10


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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'British Columbia U.'

pages = 1+9
deps = ['Mathematics,%20Department%20of&campus=UBCV',
        'Physics%20and%20Astronomy,%20Department%20of&campus=UBCV']
#        'Mathematics,%20Department%20of&campus=UBCO',
#        'Computer%20Science,%20Mathematics,%20Physics%20and%20Statistics,%20Department%20of%20(Okanagan)&campus=UBCO']

recs = []
jnlfilename = 'THESES-BRITISHCOLUMBIA-%s' % (stampoftoday)
dois = []
for dep in deps:
    for page in range(pages):
        tocurl = 'https://open.library.ubc.ca/search?q=*&p=' + str(page) + '&sort=6&view=0&circle=y&dBegin=&dEnd=&c=1&affiliation=' + dep + '&degree=Doctor%20of%20Philosophy%20-%20PhD'
        print '---{ %i/%i }---{ %s }---' % (page+1, pages, tocurl)
        driver = webdriver.PhantomJS()
        driver.implicitly_wait(30)
        driver.get(tocurl)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'dl-r-title')))
        tocpage = BeautifulSoup(driver.page_source)
        time.sleep(2)
        for a in tocpage.find_all('a', attrs = {'class' : 'dl-r-title'}):
            if a.has_attr('href'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'artlink' : a['href'], 'note' : []}
                rec['tit'] = a.text.strip()
                rec['doi'] = '20.2000/BritishColumbia/' + re.sub('.*items\/', '', a['href'])
                if 'UBCO' in dep:
                    rec['note'].append('Okanagan Campus')
                if dep == 'Mathematics,%20Department%20of&campus=UBCV':
                    rec['fc'] = 'm'
                if not rec['doi'] in dois:
                    recs.append(rec)
                    dois.append(rec['doi'])
            

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(10)
    except:
        try:
            print 'retry %s in 180 seconds' % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print 'no access to %s' % (rec['artlink'])
            continue
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #abstract
            elif meta['name'] == 'og:description':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'DC.issued':
                rec['date'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #number of pages
            elif meta['name'] == 'eprints.pages':
                rec['pages'] = meta['content']
            #PDF
            elif meta['name'] == 'citation_pdf_url':
                if 'license' in rec.keys():
                    rec['FFT'] = meta['content']
                else:
                    rec['hidden'] = meta['content']
    rec['autaff'][-1].append(publisher)
                
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text: 
    retfiles = open(retfiles_path,'a')
    retfiles.write(line)
    retfiles.close()


