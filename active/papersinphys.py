# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Papers in Physics
# FS 2017-12-13

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

publisher = 'Papers in Physics'
typecode = 'P'

vol = sys.argv[1]

jnlfilename = 'pip%s' % (vol)

    
urltrunk = 'http://www.papersinphysics.org/papersinphysics/issue/view/%s' % (vol)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))

recs = []
for table in tocpage.body.find_all('table', attrs = {'class' : 'tocArticle'}):
    rec = {'jnl' : 'Papers Phys.', 'tc' : typecode, 'vol' : vol, 'keyw' : [], 'autaff' : []}
    #PDF
    for a in table.find_all('a'):
        if a.text.strip() == 'PDF':
            rec['FFT'] = a['href']
    #article link
    for td in table.find_all('td', attrs = {'class' : 'tocTitle'}):
        rec['tit'] = td.text.strip()
        for a in td.find_all('a'):
            rec['artlink'] = a['href']
    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    autaff = False
    print '%i/%i %s' % (i, len(recs), rec['tit'])
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #article ID
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #authors and affiliations
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([ meta['content'] ])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
    #abstract
    for div in artpage.body.find_all('div', attrs = {'id' : 'articleAbstract'}):
        for p in div.find_all('p'):
            if not rec.has_key('abs'):
                rec['abs'] = p.text
                break
    #license
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['licence'] = {'url' : a['href']}


                                       
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
 
