# -*- coding: utf-8 -*-
#harvest theses from Goettingen U.
#FS: 2019-11-13


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

publisher = 'Gottingen U.'

typecode = 'T'

jnlfilename = 'THESES-GOETTINGEN-%s' % (stampoftoday)

tocurl = 'https://ediss.uni-goettingen.de/handle/11858/8/discover?fq=dateIssued.year=[' + str(now.year - 1) + '+TO+' + str(now.year + 1) + ']&rpp=2000'


print tocurl

hdr = {'User-Agent' : 'Magic Browser'}

prerecs = {}
os.system('wget -O /tmp/%s.toc "%s"' % (jnlfilename, tocurl))
inf = open('/tmp/%s.toc' % (jnlfilename), 'r')
lines = inf.readlines()
inf.close()
tocpage = BeautifulSoup(' '.join(lines))
i = 0
for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
    i += 1
    for a in div.find_all('a'):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        rec['artlink'] = 'https://ediss.uni-goettingen.de' + a['href'] + '?show=full'
        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
        if a['href'] in prerecs.keys():
            print '%3i) %s already on list' % (i, a['href'])
        else:
            prerecs[a['href']] = rec
            print '%3i) %s added to list (%i)' % (i, a['href'], len(prerecs))

    
recs = []
i = 0
for rec in prerecs.values():
    i += 1
    time.sleep(3)
    print '---{ %i/%i }---{ %s}------' % (i, len(prerecs), rec['artlink'])
    os.system('wget -O /tmp/%s.%05i "%s"' % (jnlfilename, i, rec['artlink']))
    inf = open('/tmp/%s.%05i' % (jnlfilename, i), 'r')
    lines = inf.readlines()
    inf.close()
    artpage = BeautifulSoup(' '.join(lines))
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'DC.rights'}):
        if re.search('creativecommons.org', meta['content']):
            rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('Gottingen U.')
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'ger':
                    rec['language'] = 'german'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                if 'licence' in rec.keys():
                    rec['FFT'] = meta['content']
                else:
                    rec['hiddden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']

    print rec.keys()
    recs.append(rec)


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
