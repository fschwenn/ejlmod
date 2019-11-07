# -*- coding: utf-8 -*-
#harvest theses from SISSA
#FS: 2018-01-30


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

tocurl = 'https://ediss.uni-goettingen.de/handle/11858/8/discover?fq=dateIssued.year=[' + str(now.year - 1) + '+TO+' + str(now.year + 1) + ']&rpp=500'


print tocurl

hdr = {'User-Agent' : 'Magic Browser'}

prerecs = []
os.system('wget -O /tmp/%s.toc "%s"' % (jnlfilename, tocurl))
inf = open('/tmp/%s.toc' % (jnlfilename), 'r')
lines = inf.readlines()
inf.close()
tocpage = BeautifulSoup(' '.join(lines))
for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
    for a in div.find_all('a'):
        rec['artlink'] = 'https://ediss.uni-goettingen.de' + a['href'] + '?show=full'
        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
        prerecs.append(rec)


recs = []
i = 0
for rec in prerecs:
    i += 1
    time.sleep(3)
    print '---{ %i/%i}---{ %s}------' % (i, len(prerecs), rec['artlink'])
    os.system('wget -O /tmp/%s.%05i "%s"' % (jnlfilename, i, rec['artlink']))
    inf = open('/tmp/%s.%05i' % (jnlfilename, i), 'r')
    lines = inf.readlines()
    inf.close()
    artpage = BeautifulSoup(' '.join(lines))
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
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #license            
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}

    print rec
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
