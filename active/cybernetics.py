# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest CYBERNETICS AND PHYSICS
# FS 2020-10-26

import os
import ejlmod2
import codecs
import re
import sys
import unicodedata
import string
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup



xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

publisher = 'International Physics and Control Society'
volume = sys.argv[1]
issue = sys.argv[2]

jnl = 'cybphy'
jnlname = 'Cybern.Phys.'
jnlfilename = '%s%s.%s' % (jnl, volume, issue)


starturl = 'http://lib.physcon.ru/doc?id=29e59dce4f11'
hdr = {'User-Agent' : 'Magic Browser'}
req = urllib2.Request(starturl, headers=hdr)
startpage = BeautifulSoup(urllib2.urlopen(req))

for li in startpage.body.find_all('li'):
    for a in li.find_all('a'):
        if re.search('Volume %s, .*, Number %s' % (volume, issue), a.text.strip()):
            year = re.sub('.*([12]\d\d\d).*', r'\1', a.text.strip())
            tocurl = 'http://lib.physcon.ru/' + a['href']
            
print "get table of content via %s" % (tocurl)
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'children'}):
    for li in div.find_all('li'):
        for a in li.find_all('a'):
            rec = {'jnl' : jnlname, 'vol' : volume, 'issue' : issue, 'year' : year,
                   'note' : [], 'tc' : 'P', 'auts' : []}
            rec['license'] = {'statement' : 'CC-BY-4.0'}
            if not a.text.strip() in ['CONTENTS']:
                rec['artlink'] = 'http://lib.physcon.ru/' + a['href']
                rec['tit'] = a.text.strip()
                recs.append(rec)

i = 0
for rec in recs:
    time.sleep(1)
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))
    #authors
    for div in artpage.body.find_all('div', attrs = {'class' : 'authors'}):
        rec['auts'] = re.split(', ', re.sub('[\n\t\r]', '', div.text.strip()))
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'abstract'}):
        abs = div.text.strip()
        #DOI
        if re.search('doi.org\/10.35470\/', abs):
            rec['doi'] = re.sub('.*doi.org\/(10.*)', r'\1', abs)
            abs = re.sub(',*\.* *https?...doi.org.*', '', abs).strip()
        else:
            abs = re.sub('\.*\,*$', '', abs)
        #pages
        pages = re.sub('.*CYBERNETICS AND PHYSICS.*?([\d\-]+)$', r'\1', abs)
        rec['p1'] = re.sub('\-.*', '', pages)
        rec['p2'] = re.sub('.*\-', '', pages)
        #abstract
        rec['abs'] = re.sub('CYBERNETICS AND PHYSICS, Vol.*', '', abs)
    #PDF
    for a in artpage.body.find_all('a'):
        if a.text.strip() == 'download':
            rec['FFT'] = 'http://lib.physcon.ru/' + a['href']
    #noDOI
    if not 'doi' in rec.keys():
        rec['doi'] = '20.2000/physcon.ru/' + re.sub('\W', '', rec['artlink'][22:])
        rec['link'] = rec['artlink']

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
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
 
