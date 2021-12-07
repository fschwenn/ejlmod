# -*- coding: utf-8 -*-
#harvest theses from PANDA
#FS: 2018-02-16


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
import ssl
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'PANDA'

typecode = 'T'

jnlfilename = 'THESES-PANDA-%s' % (stampoftoday)

tocurl = 'https://panda.gsi.de/panda-publications/thesis-th'

#bad cerificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

try:
    tocpage = BeautifulSoup(urllib2.urlopen(tocurl, context=ctx))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.urlopen(tocurl, context=ctx))

recs = []
for div in tocpage.body.find_all('div', attrs = {'role' : 'article'}):
    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'exp' : 'GSI-FAIR-PANDA', 'keyw' : []}
    for d2 in div.find_all('div', attrs = {'property' : 'dc:title'}):
        rec['rn'] = [ d2.text.strip() ]
        rec['doi'] = '20.2000/PANDA/' + d2.text.strip()
    for section in div.find_all('section', attrs = {'class' : 'field field-name-field-publication-title field-type-text field-label-above view-mode-teaser'}):
        for d2 in section.find_all('div', attrs = {'class' : 'field-items'}):
            rec['tit'] = d2.text.strip()
    for section in div.find_all('section', attrs = {'class' : 'field field-name-field-publication-author field-type-text field-label-above view-mode-teaser'}):
        for d2 in section.find_all('div', attrs = {'class' : 'field-items'}):
            rec['auts'] = [ d2.text.strip() ]
    for section in div.find_all('section', attrs = {'class' : 'field field-name-field-file-upload field-type-file field-label-above view-mode-teaser'}):
        for a in section.find_all('a'):
            rec['link'] = a['href']
            if re.search('pdf$',  a['href']):
                rec['FFT'] = a['href']
    for section in div.find_all('section', attrs = {'class' : 'field field-name-field-publication-classification field-type-taxonomy-term-reference field-label-above view-mode-teaser'}):
        for li in section.find_all('li'):
            rec['keyw'].append(li.text.strip())
    for section in div.find_all('section', attrs = {'class' : 'field field-name-field-publication-date field-type-datetime field-label-above view-mode-teaser'}):
        for span in section.find_all('span'):
            rec['date'] = span['content'][:10] 
    for section in div.find_all('section', attrs = {'class' : 'field field-name-field-publication-abstract field-type-text-long field-label-above view-mode-teaser'}):
        for d2 in section.find_all('div', attrs = {'class' : 'field-items'}):
            rec['abs'] = re.sub('[\r\n\t]', ' ', d2.text.strip())
    recs.append(rec)
            


    
    
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
