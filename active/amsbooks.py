# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest http://www.ams.org/books
# FS 2019-04-13

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
from bs4 import BeautifulSoup
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'




series = sys.argv[1]
volume = sys.argv[2]
jnlfilename = 'amsbooks_%s%s' % (series, volume)
if len(sys.argv) > 3:
    cnum = sys.argv[3]
    jnlfilename += '_%s' % (cnum)

if series == 'pspum':
    jnl = 'Proc.Symp.Pure Math.'
    tc = 'C'
    
publisher = 'AMS'

tocurl = 'http://www.ams.org/books/%s/%s' % (series, volume)
print tocurl
tocpage = BeautifulSoup(urllib2.urlopen(tocurl))

#Hauptaufnahme
rec = {'jnl' : jnl, 'vol' : str(int(vol)), 'autaff' = [], 'isbns' : []}
if tc == 'C':
    rec['tc'] = 'K'
else:
    rec['tc'] = 'B'
if len(sys.argv) > 3:
    rec['cnum'] = cnum
for meta in tocpage.head.find_all('meta'):
    if meta.has_attr('name'):
        if meta['name'] == 'citation_isbn':
            rec['isbns'].append(('a', meta['content']))
        elif meta['name'] == 'citation_author':
            rec['autaff'].append([meta['content']])
        elif meta['name'] == 'citation_author_institution':
            rec['autaff'][-1].append(meta['content'])
        elif meta['name'] == 'citation_publication_date':
            rec['date'] = meta['content']
        elif meta['name'] == 'citation_doi':
            rec['doi'] = meta['content']
        elif meta['name'] == 'citation_title':
            rec['tit'] = meta['content']
for div in tocpage.body.find_all('div', attrs = {'id' : 'toggleText'}):
    divt = div.text.strip()
    divt = re.sub('[\n\t\r]', ' ', divt)
    divt = re.sub('Readership.*', '', divt)
    divt = re.sub('  +', ' ', divt)
    rec['abs'] = divt

recs = [rec]
for ul in tocpage.body.find_all('ul', attrs = {'class' : 'pdfIcon'}):
    for li in ul.find_all('li'):
        rec = {'jnl' : jnl, 'vol' : str(int(vol)), 'auts' : [], 'tc' : tc}
        rec['date'] = recs[0]['date']
        for a in li.find_all('a'):
            rec['tit'] = a.text.strip()
            rec['link'] = '%s/%s' % (tocurl, a['href'])
            rec['doi'] = '20.2000/%s/%s/%s' % (series, volume, a['href'])
            a.replace_with('')
        authors = re.sub(' and ', ', ', li.text.strip())
        rec['auts'] = re.split(' *, *', authors)
        recs.append(rec)
print len(recs)


#write xml
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
