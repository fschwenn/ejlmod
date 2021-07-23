# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest J-STAGE journal
# FS 2018-08-14

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

publisher = 'Japan Science and Technology Agency'
typecode = 'P'
jnl = sys.argv[1]
vol = sys.argv[2]
jnlfilename = '%s%s' % (jnl, vol)
cnum = False
if len(sys.argv) > 3: 
    iss = sys.argv[3]
    jnlfilename = jnl + vol + '.' + iss
if len(sys.argv) > 4:
    cnum = sys.argv[4]
    jnlfilename = jnl + vol + '.' + iss + '_' + cnum
    typecode = 'C'
if   (jnl == 'soken'): 
    jnlname = 'Soryushiron Kenkyu Electron.'


tocurl = 'https://www.jstage.jst.go.jp/browse/%s/%s/%s/_contents/-char/en' % (jnl, vol, iss)  

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))


recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'searchlist-title'}):
    rec = {'jnl' : jnlname, 'vol' : vol, 'tc' : typecode, 'autaff' : []}
    if len(sys.argv) > 3: 
        rec['issue'] = iss
    if len(sys.argv) > 4:
        rec['cnum'] = cnum
    for a in div.find_all('a'):
        rec['articlelink'] = a['href']
        rec['tit'] = a.text.strip()
    if rec['tit'] != '[title in Japanese]':
        recs.append(rec)

for rec in recs:
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['articlelink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['articlelink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['articlelink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #pages
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf'] = meta['content']
            #authors and affiliations
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'ja':
                    rec['language'] = 'Japanese'
                
    #abstract
    for div in artpage.body.find_all('div', attrs = {'id' : 'article-overiew-abstract-wrap'}):
        for p in div.find_all('p'):
            rec['abs'] = p.text.strip()
    #free text
    for span in artpage.body.find_all('span', attrs = {'title' : 'FREE ACCESS'}):
        if rec.has_key('pdf'):
            rec['FFT'] = rec['pdf']
            del(rec['pdf'])




                                       
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
 
