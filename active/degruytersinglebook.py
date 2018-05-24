# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest single De Gruyter Book
# FS 2018-05-24

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
urltrunc = 'https://www.degruyter.com'
publisher = 'De Gruyter'

toclink = sys.argv[1]

jnlfilename = 'dg' + re.sub('.*\/', '', toclink)

jnl = "BOOK"

#get list of volumes
os.system("wget -T 300 -t 3 -q -O /tmp/dg%s %s" % (jnlfilename, toclink))
inf = open('/tmp/dg%s' % (jnlfilename), 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()))
inf.close()

#Hauptaufnahme
rec = {'jnl' : jnl, 'auts' : [], 'tc' : 'B'}
for h1 in tocpage.find_all('h1', attrs = {'id' : 'mainTitle'}):
    rec['tit'] = h1.text
for div in tocpage.find_all('div', attrs = {'class' : 'HG'}):
    editors = re.sub('Ed. by ', '', div.text.strip())
    for editor in re.split(' *\/ *', editors):
        rec['auts'].append('%s (Ed.)' % (editor))
for dd in tocpage.find_all('dd', attrs = {'id' : 'pubDate'}):
    date = re.sub('.*(\d\d\d\d).*', r'\1', dd.text)
    rec['date'] = date
for dd in tocpage.find_all('dd', attrs = {'id' : 'isbn'}):
    rec['isbn'] = dd.text
    rec['doi'] = '10.1515/' + re.sub('\-', '', dd.text)

recs = [rec]

#Chapters
for div in tocpage.find_all('div', attrs = {'class' : 'article-meta'}):
    rec = {'jnl' : jnl, 'auts' : [], 'tc' : 'S', 'date' : date, 'auts' : []}
    for a in div.find_all('a'):
        rec['artlink'] = 'https://www.degruyter.com' + a['href']
    os.system("wget -T 300 -t 3 -q -O /tmp/dg%s%i %s" % (jnlfilename, len(recs), rec['artlink']))
    inf = open('/tmp/dg%s%i' % (jnlfilename, len(recs)), 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    #title
    for h2 in artpage.find_all('h2', attrs = {'class' : 'chapterTitle'}):
        rec['tit'] = h2.text
    #authors
    for h3 in artpage.find_all('h3', attrs = {'class' : 'chapterAuthor'}):
        for author in re.split(' *\/ *', h3.text):
            rec['auts'].append(author)
    #abstract
    for meta in artpage.find_all('meta', attrs = {'name' : 'description'}):
        rec['abs'] = meta['content']
    #pages 
    for p in artpage.find_all('p', attrs = {'class' : 'pages'}):
        pages = re.split('\D+', re.sub('^\D*(\d.*)', r'\1', p.text.strip()))
        if len(pages) > 0:
            rec['p1'] = pages[0]
            if len(pages) > 1:
                rec['p2'] = pages[1]
    #DOI
    for p in artpage.find_all('p', attrs = {'class' : 'doi'}):
        ptext = p.text.strip()
        if re.search('hapter', ptext):
            rec['doi'] = re.sub('.*?(10\..*)', r'\1', ptext)
    if rec['auts']:
        recs.append(rec)
    
    







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

