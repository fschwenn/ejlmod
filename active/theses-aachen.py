# -*- coding: utf-8 -*-
#harvest theses from RWTH Aachen U. 
#FS: 2019-12-13


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

publisher = 'RWTH Aachen U.'

rg = '100'
hdr = {'User-Agent' : 'Magic Browser'}
years = 2

recs = {}
for fachgruppe in ['130000', '110000']:
    tocurl = 'http://publications.rwth-aachen.de/search?ln=de&p=980__a%3Aphd+9201_k%3A' + fachgruppe + '&f=&action_search=Suchen&c=RWTH+Publications&sf=&so=d&rm=&rg=' + rg + '&sc=1&of=xd'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    for oai in tocpage.find_all('oai_dc:dc'):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [ fachgruppe ]}
        #title
        for dc in oai.find_all('dc:title'):
            rec['tit'] = dc.text
        #language
        for dc in oai.find_all('dc:language'):
            if dc.text != 'eng':
                if dc.text == 'ger':
                    rec['language'] = 'german'
                else:
                    rec['language'] = dc.text
        #keywords
        for dc in oai.find_all('dc:subject'):
            if re.search('\/ddc\/', dc.text):
                rec['note'].append(dc.text)
            else:
                rec['keyw'].append(dc.text)
        #author
        for dc in oai.find_all('dc:creator'):
            rec['autaff'] = [[ dc.text, publisher ]]
        #supervisor
        for dc in oai.find_all('dc:contributor'):
            rec['supervisor'].append([dc.text])
        #abstract
        for dc in oai.find_all('dc:description'):
            rec['abs'] = dc.text
        #date
        for dc in oai.find_all('dc:date'):
            rec['date'] = dc.text
            rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])
        #FFT
        for dc in oai.find_all('dc:rights'):
            if re.search('[oO]pen', dc.text):
                for dc2 in oai.find_all('dc:identifier'):
                    dc2t = dc2.text.strip()
                    if re.search('\.pdf$', dc2t):
                        rec['FFT'] = dc2t
        #DOI
        for dc in oai.find_all('dc:relation'):
            if re.search('10\.18154', dc.text):
                rec['doi'] = re.sub('.*(10\.18154.*)', r'\1', dc.text)
        #article link
        for dc in oai.find_all('dc:identifier'):
            dct = dc.text
            if re.search('http...publications.rwth.aachen.de.record.\d+', dct):
                rec['artlink'] = dct
            if not 'doi' in rec.keys():
                rec['doi'] = re.sub('.*\/', '20.2000/AACHEN/', dct)
                rec['link'] = dct
        if int(rec['year']) > now.year - years:
            recs[rec['doi']] = rec

jnlfilename = 'THESES-AACHEN_%s' % (stampoftoday)

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs.values(),xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
