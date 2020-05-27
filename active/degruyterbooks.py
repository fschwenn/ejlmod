# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest PDe Gruyter Book series
# FS 2016-01-03

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
import datetime
from bs4 import BeautifulSoup
import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
urltrunc = 'https://www.degruyter.com'
publisher = 'De Gruyter'

serial = sys.argv[1]

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

jnlfilename = 'dg' + serial + stampoftoday
if serial == 'GSTMP':
    jnl = "De Gruyter Stud.Math.Phys."
    tocurl = 'https://www.degruyter.com/view/serial/GSTMP-B?contents=toc-59654'

#get list of volumes
#os.system("wget -T 300 -t 3 -q -O /tmp/dg%s %s" % (serial, tocurl))
#inf = open('/tmp/dg%s' % (serial), 'r')
#tocpage = BeautifulSoup(''.join(inf.readlines()))
#inf.close()
driver = webdriver.PhantomJS()
driver.implicitly_wait(30)
driver.get(tocurl)
tocpage = BeautifulSoup(driver.page_source)

#get volumes
recs = []
i = 0
divs = tocpage.body.find_all('div', attrs = {'class' : 'cover-image'})
for div in divs:
    for a in div.find_all('a'):
        i += 1
        rec = {'tc' : 'B', 'jnl' : jnl, 'auts' : [], 'isbns' : []}
        rec['link'] = urltrunc + a['href']
        print i, rec['link']
        #get details
        time.sleep(10)
        os.system("wget -T 300 -t 3 -q -O /tmp/dg%s.%i %s" % (serial, i, rec['link']))
        inf = open('/tmp/dg%s.%i' % (serial, i), 'r')
        volpage = BeautifulSoup(''.join(inf.readlines()))
        inf.close()
        for meta in volpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #title
                if meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                #keywords
                elif meta['name'] == 'citation_keywords':
                    rec['keyw'] = re.split('; ', meta['content'])
                #ISBN
                #elif meta['name'] == 'citation_isbn':
                #    rec['isbn'] = meta['content']
                #date
                elif meta['name'] == 'citation_publication_date':
                    rec['date'] = meta['content']
                #date
                elif meta['name'] == 'dc.identifier':
                    rec['doi'] = meta['content']
                #authors
                elif meta['name'] == 'citation_author':
                    rec['auts'].append(meta['content'])
            elif meta.has_attr('property'):
                #abstract
                if meta['property'] == 'og:description':
                    rec['abs'] = meta['content']
        #volume
        for div in volpage.find_all('div', attrs = {'class' : 'font-content '}):
            for a in div.find_all('a', attrs = {'class' : 'c-Button--primary"'}):
                atext = a.text.strip()
                if re.search('\d$', atext):
                    rec['vol'] = re.sub('.*\D', '', atext)
        #DOI
        #pages
        for dd in volpage.find_all('dd', attrs = {'class' : 'pagesarabic'}):
            rec['pages'] = re.sub('[\n\t\r]', '', dd.text.strip())
        #ISBNS
        for dd in volpage.find_all('dd', attrs = {'class' : 'publisherisbn'}):
            rec['isbns'].append([('a', re.sub('[\n\t\r\-]', '', dd.text.strip()))])
        #authors
        if not rec['auts']:
            for div in volpage.find_all('div', attrs = {'class' : 'content-box'}):
                for h2 in div.find_all('h2'):
                    if re.search('Author', h2.text):
                        for strong in div.find_all('strong'):
                            rec['auts'].append(strong.text.strip())
        print rec.keys()
        recs.append(rec)
    
    







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

