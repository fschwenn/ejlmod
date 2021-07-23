# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest AIP-journals
# FS 2015-02-11

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

publisher = 'Andromda'
typecode = 'P'

jnl = sys.argv[1]
issuenumber = sys.argv[2]

if jnl == 'lhep':
    jnlname = 'LHEP'
    tocurl = 'http://journals.andromedapublisher.com/index.php/LHEP/issue/view/' + issuenumber

print tocurl
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for div in tocpage.find_all('div', attrs = {'class' : 'title'}):
    for a in div.find_all('a'):
        rec = {'jnl': jnlname, 'tc' : typecode, 'autaff' : [], 'keyw' : []}
        rec['tit'] = a.text.strip()
        rec['artlink'] = a['href']
        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        print rec['artlink']
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'] )
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #PBN
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content'] 
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content'] 
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content'] 
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content'] 
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.Description':
                rec['abs'] = meta['content']
    #licence
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['license'] = {'url' : a['href']}
    #references
    for div in artpage.body.find_all('div', attrs = {'class' : 'item references'}):
        rec['refs'] = []
        for div2 in div.find_all('div'):
            for br in div2.find_all('br'):
                br.replace_with('_TRENNER_')
            for ref in re.split('_TRENNER_', div2.text):
                rec['refs'].append([('x', ref)])
    print rec

jnlfilename = '%s%s.%s' % (jnl, rec['vol'], rec['issue'])
                
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
 
