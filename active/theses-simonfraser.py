# -*- coding: utf-8 -*-
#harvest Simon Fraser U., Burnaby (main)
#FS: 2020-02-05

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Simon Fraser U., Burnaby (main)'
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
prerecs = []
jnlfilename = 'THESES-SIMONFRASER-%s' % (stampoftoday)
pages = 1

for page in range(pages):
    tocurl = 'https://summit.sfu.ca/collection/164?page=%i' % (page)
    tocpage = BeautifulSoup(urllib2.urlopen(tocurl))
    print '---{ %i/%i }---{ %s }------' % (page+1, pages, tocurl)
    for h2 in tocpage.body.find_all('h2', attrs = {'class' : 'title'}):
        for a in h2.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : []}
            rec['tit'] = h2.text.strip()
            rec['link'] = 'https://summit.sfu.ca' + a['href']
            rec['doi'] = '20.2000/SimonFraser' + a['href']
            prerecs.append(rec)

i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(prerecs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        try:
            print 'retry %s in 180 seconds' % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print 'no access to %s' % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #date
            elif meta['name'] == 'DC.date':
                rec['date'] = meta['content']
            #PDF
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    rec['autaff'][-1].append(publisher)
    #keywords
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-field-keywords'}):
        for kw in div.find_all('div', attrs = {'class' : 'field-item'}):
            rec['keyw'].append(kw.text.strip())
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-field-abstract'}):
        for abs in div.find_all('div', attrs = {'class' : 'field-item'}):
            rec['abs'] = abs.text.strip()
    #supervisor
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-field-senior-supervisor'}):
        for sv in div.find_all('div', attrs = {'class' : 'field-item'}):
            rec['supervisor'] = [[ sv.text.strip(), publisher ]]
    #thesis type
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-field-thesis-type'}):
        for tt in div.find_all('div', attrs = {'class' : 'field-item'}):
            if not re.search('M.Sc.', tt.text):
                rec['note'] = [ tt.text.strip() ]
                recs.append(rec)        
                print '  ', rec.keys()
                    
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


