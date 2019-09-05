# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Ingenta journals 
# FS 2019-08-26

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
def tfstrip(x): return x.strip()

publisher = 'Ingenta'
jnl = sys.argv[1]
year = sys.argv[2]
vol = sys.argv[3]
iss = sys.argv[4]
jnlfilename = 'ingenta_%s%s.%s' % (jnl, vol, iss)
    
if jnl == 'pe':
    jnlname = 'Phys.Essays'
    typcode = 'P'
else:
    sys.exit(0)
    
tocurl = 'https://www.ingentaconnect.com/content/%s/%s/%s/%08i/%08i' % (jnl, jnl, year, int(vol), int(iss))
print tocurl
hdr = {'User-Agent' : 'Mozilla/5.0'}
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
articlelinks = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'greybg'}):
    for div2 in div.find_all('div', attrs = {'class' : 'data'}):
        for a in div2.find_all('a'):
            if a.has_attr('href'):
                if re.search('contentone', a['href']):
                    rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : iss, 'year' : year,
                           'tc' : typcode, 'auts' : [], 'keyw' : []}
                    rec['articlelink'] = 'https://www.ingentaconnect.com' + a['href']
                    rec['tit'] = a.text.strip()
                    if not rec['articlelink'] in articlelinks:
                        recs.append(rec)
                        articlelinks.append(rec['articlelink'])
i=0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['articlelink'])
    time.sleep(20)
    req = urllib2.Request(rec['articlelink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DC.creator':
                rec['auts'].append(meta['content'])
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(re.sub('; *$', '', meta['content']))
            elif meta['name'] == 'DC.identifier':
                rec['doi'] = re.sub('.*?(10.*)', r'\1', meta['content'])
            elif meta['name'] == 'DCTERMS.bibliographicCitation':
                pages = re.sub('.*, *', '', meta['content'])
                pages = re.sub('\(.*', '', pages)
                rec['p1'] = re.sub('\-.*', '', pages)
                rec['p2'] = re.sub('.*\-', '', pages)
    for div in artpage.body.find_all('div', attrs = {'id' : 'Abst'}):
        abstract = div.text.strip()
        if not abstract == 'No Abstract.':
            rec['abs'] = abstract

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

