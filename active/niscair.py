# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Niscair online Periodicals Repository
# FS 2018-09-14

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

publisher = 'Niscair'
typecode = 'P'
vol = sys.argv[1]
issue = sys.argv[2]
tocurl = sys.argv[3]

jnl = 'ijpap'
jnlname = 'Indian J.Pure Appl.Phys.'
jnlfilename = jnl+vol+'.'+issue


try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))


recs = []
for tr in tocpage.body.find_all('tr'):
    for td in tr.find_all('td', attrs = {'headers' : 't1'}):
        for a in td.find_all('a'):
            rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue,
                   'auts' : [],
                   'licence' : {'statement' : 'CC-BY-NC-ND-2.5'},
                   'tc' : typecode, 'tit' : a.text.strip()}
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            rec['artlink'] = 'http://nopr.niscair.res.in' + a['href']
            for td in tr.find_all('td', attrs = {'headers' : 't4'}):
                pages = re.split(' *\- *', td.text.strip())
                rec['p1'] = pages[0]
                if len(pages) > 1:
                    rec['p2'] = pages[1]    
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
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_author'}):
        rec['auts'].append(meta['content'])
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_date'}):
        rec['date'] = meta['content']
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
        rec['FFT'] = meta['content']
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_keywords'}):
        cont = re.sub('[\n\t]', ' ', meta['content'])
        cont = re.sub('&lt;.*?&gt;', '', re.sub('<.*?>', '', cont))
        rec['keyw'] = re.split(' *; ', cont)
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'DCTERMS.abstract'}):
        cont = re.sub('[\n\t]', ' ', meta['content'])
        cont = re.sub('&lt;.*?&gt;', '', re.sub('<.*?>', '', cont))
        rec['abs'] = cont
    print rec









                                       
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
 
