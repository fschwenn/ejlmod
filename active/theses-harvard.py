# -*- coding: utf-8 -*-
#harvest theses from Harvard
#FS: 2020-01-14


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Harvard U. (main)'
rpp = 50
numofpages = 1
departments = ['Mathematics', 'Physics']

driver = webdriver.PhantomJS()
driver.implicitly_wait(30)
hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for dep in departments:
    for i in range(numofpages):
        tocurl = 'https://dash.harvard.edu/handle/1/4927603/browse?type=department&value=%s&rpp=%i&sort_by=2&type=dateissued&offset=%i&etal=-1&order=DESC' % (dep, rpp, i*rpp)
        print '---{ %s }---{ %i/%i }---{ %s }------' % (dep, i+1, numofpages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(10)
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            for a in div.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'oa' : False, 'note' : [ dep ]}
                rec['link'] = 'https://dash.harvard.edu' + a['href']
                #rec['doi'] = '20.2000/HARVARD/' + re.sub('\/handle\/', '', a['href'])
                rec['tit'] = a.text.strip()
                if dep == 'Mathematics':
                    rec['fc'] = 'm'
                recs.append(rec)
            
jnlfilename = 'THESES-HARVARD-%s' % (stampoftoday)
j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['link'])
    try:
        driver.get(rec['link'])
        artpage = BeautifulSoup(driver.page_source)
    except:
        time.sleep(60)
        print 'wait a minute'
        driver.get(rec['link'])
        artpage = BeautifulSoup(driver.page_source)
    time.sleep(5)
    #author
    for meta in artpage.find_all('meta', attrs = {'name' : 'citation_author'}):
        rec['autaff'] = [[ meta['content'], publisher ]]
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name'):
                #date
                if meta['name'] == 'DC.date':
                    rec['date'] = meta['content']
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    if meta.has_attr('xml:lang') and meta['xml:lang'] == 'en':
                        rec['abs'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['FFT'] = meta['content']
                #URN
                elif meta['name'] == 'DC.identifier':                    
                    if meta.has_attr('scheme') and re.search('URI', meta['scheme']):
                        rec['urn'] = re.sub('.*harvard.edu\/', '', meta['content'])
                        rec['link'] = meta['content']
                    else:
                        rec['note'].append(meta['content'])
                #keywords
                elif meta['name'] == 'citation_keywords':
                    rec['keyw'] = re.split('[,;] ', meta['content'])
    if not 'urn' in rec.keys():
        rec['doi'] = '20.2000/Harvard' + re.sub('.*\/', '', rec['link'])
    print '  ', rec.keys()
            
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()


