# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest CCSENET
# FS 2018-10-30

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'Canadian Center of Science and Education'
jnl = sys.argv[1]
vol = sys.argv[2]
isu = sys.argv[3]

if   (jnl == 'apr'): 
    jnlname = 'Appl.Phys.Res.'
    issn = '1916-9639'
elif (jnl == 'jmr'):
    jnlname = 'J.Math.Res.'
    issn = '1916-9795'

jnlfilename = jnl+vol+'.'+isu
tc = 'P'

archiveslink = 'http://www.ccsenet.org/journal/index.php/%s/issue/archives' % (jnl)


print '[archive] %s' % (archiveslink)
arcpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(archiveslink))
for li in arcpage.body.find_all('li'):
    for a in li.find_all('a'):
        at = a.text.strip()
        if re.search('Vol. %s, No. %s$' % (vol, isu), at):
            toclink = a['href']


print '[TOC] %s' % (toclink)
tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
recs = []
for li in tocpage.body.find_all('li', attrs = {'class' : 'h5'}):
    for a in li.find_all('a'):
        artlink = a['href']
        print '[ART] %s' % (artlink)
        rec = {'vol' : vol, 'issue' : isu, 'jnl' : jnlname, 'tc' : tc,
               'auts' : []}
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(artlink))
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                if meta['name'] == 'DC.Date.issued':
                    rec['date'] = meta['content'] 
                elif meta['name'] == 'DC.Description':
                    rec['abs'] = meta['content'] 
                elif meta['name'] == 'DC.Identifier.pageNumber':
                    rec['p1'] = meta['content'] 
                elif meta['name'] == 'DC.Identifier.DOI':
                    rec['doi'] = meta['content'] 
                elif meta['name'] == 'DC.Rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['licence'] = {'url' : meta['content']}
                elif meta['name'] == 'DC.Title':
                    rec['tit'] = meta['content'] 
                elif meta['name'] == 'citation_author':
                    rec['auts'].append(meta['content'])
                elif meta['name'] == 'citation_firstpage':
                    rec['p1'] = meta['content'] 
                elif meta['name'] == 'citation_lastpage':
                    rec['p2'] = meta['content'] 
                elif meta['name'] == 'citation_pdf_url':
                    rec['FFT'] = meta['content'] 
        recs.append(rec)

xmlf = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile = open(xmlf, 'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs ,xmlfile, publisher, jnlfilename)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename + ".xml\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
