# -*- coding: utf-8 -*-
#harvest theses from TU Munich
#FS: 2019-09-24


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Munich, Tech. U.'

typecode = 'T'

jnlfilename = 'THESES-TUM-%s' % (stampoftoday)


tocurl = 'https://mediatum.ub.tum.de/680895?nodes_per_page=50&sortfield0=-year-accepted'
print tocurl
hdr = {'User-Agent' : 'Magic Browser'}
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
divs = tocpage.body.find_all('div', attrs = {'class' : 'preview_text'})
i = 0 
for div in divs:
    i += 1
    for a in div.find_all('a'):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        rec['artlink'] = 'https://mediatum.ub.tum.de' + a['href']
        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    time.sleep(3)
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))
    #title
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-title'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['tit'] = div2.text.strip()
    #author
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-email_link'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['autaff'] = [[div2.text.strip(), 'Munich, Tech. U.']]
    #date
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-year-accepted'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['date'] = div2.text.strip()
    #supervisor
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-advisor'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['supervisor'] = [[re.sub(' *\(.*', '', div2.text.strip()), 'Munich, Tech. U.']]
    #language
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-lang'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            if div2.text.strip() == 'de':
                rec['language'] = 'german'
            elif div2.text.strip() != 'en':
                rec['note'].append('LANGUAGE: %s' % (div2.text.strip()))
    #keywords
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-keywords'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['keyw'] = re.split(', ', div2.text.strip())
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-description'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['abs'] = div2.text.strip()
    #link
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-www-address'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['link'] = div2.text.strip()
            if not 'urn' in rec.keys():
                rec['doi'] = '20.2001/TUM/' + re.sub('\W', '', rec['link'][26:])
    #pages
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-pdf_pages'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['pages'] = re.sub('\D', '', div2.text.strip())
    #urn
    for div in artpage.body.find_all('div', attrs = {'class' : 'field-urn_link'}):
        for div2 in div.find_all('div', attrs = {'class' : 'mask_value'}):
            rec['urn'] = re.sub('.*resolver.pl.', '', div2.text.strip())
    #PDF
    for a in artpage.body.find_all('a', attrs = {'target' : 'documentdownload'}):
        rec['FFT'] = 'https://mediatum.ub.tum.de' + a['href']






	


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
