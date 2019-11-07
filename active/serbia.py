# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest from doiSerbia
# FS 2019-10-25

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import json

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

jnl = sys.argv[1]
issueid = sys.argv[2]

if jnl == 'facta':
    jnlname = 'Facta Univ.Ser.Phys.Chem.Tech.'
    typecode = 'P'
    issn = '0354-4656'
    publisher = 'Nis U.'
else:
    print 'journal unknown'
    sys.exit(0)

    
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}

toclink = 'http://www.doiserbia.nb.rs/issue.aspx?issueid=%s' % (issueid)
tocfile = '/tmp/%s%s' % (jnl, issueid)

print toclink
if not os.path.isfile(tocfile):
    os.system('lynx -source "%s" > %s' % (toclink, tocfile))

inf = open(tocfile, 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()))
inf.close()
              
recs = []
#for div in tocpage.body.find_all('div', attrs = {'id' : 'ContentRight'}):
#    for a in div.find_all('a'):
for a in tocpage.body.find_all('a'):
        if re.search('Details', a.text.strip()):
            rec = {'jnl' : jnlname, 'tc' : typecode, 'auts' : []}
            rec['artlink'] = 'http://www.doiserbia.nb.rs/' + a['href']
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(4)
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #title
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #authors
            elif meta['name'] == 'citation_author':
                rec['auts'].append(meta['content'])
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #pubnote
            elif meta['name'] == 'citation_year':
                rec['year'] = meta['content']
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content']
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #abstract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = re.sub('  +', ' ', re.sub('\n', ' ', meta['content']))
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('doi.org.10', a['href']):
            rec['doi'] = re.sub('.*doi.org.(10\..*)', r'\1', a['href'])
    print rec.keys()

jnlfilename = '%s%s.%s' % (jnl, rec['vol'], rec['issue'])

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

