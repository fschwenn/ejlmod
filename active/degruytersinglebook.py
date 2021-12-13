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
if not os.path.isfile('/tmp/dg%s' % (jnlfilename)):
    os.system("wget -T 300 -t 3 -q -O /tmp/dg%s %s" % (jnlfilename, toclink))
    time.sleep(5)
inf = open('/tmp/dg%s' % (jnlfilename), 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()))
inf.close()

#Hauptaufnahme
rec = {'jnl' : jnl, 'auts' : [], 'tc' : 'B'}
date = False
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
divs = tocpage.find_all('div', attrs = {'class' : 'article-meta'})
if not divs:
    divs = tocpage.find_all('tr', attrs = {'class' : 'bookTocEntryRow'})
i = 0 
for div in divs:
    i += 1
    print '---'
    rec = {'jnl' : jnl, 'auts' : [], 'tc' : 'S', 'auts' : []}
    if date:
        rec['date'] = date
    for a in div.find_all('a'):
        if a.has_attr('href') and not re.search('pdf$', a['href']):
            rec['artlink'] = 'https://www.degruyter.com' + a['href']
            print rec['artlink']
    artfilename = '/tmp/dg%s___%05i' % (jnlfilename, i)
    if not os.path.isfile(artfilename):
        os.system("wget -T 300 -t 3 -q -O %s %s" % (artfilename, rec['artlink']))
        time.sleep(5)
    inf = open(artfilename, 'r')
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
    ###look for meta tags
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #pages
            if meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #ISBN
            elif meta['name'] == 'citation_isbn':
                rec['motherisbn'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['auts'].append(meta['content'])
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
        elif meta.has_attr('property'):
            #DOI
            if meta['property'] == 'og:url':
                if re.search('10.1515', meta['content']):
                    rec['doi'] = re.sub('.*(10\/1515\/.*)', r'\1', meta['content'])
                    rec['doi'] = re.sub('\/hml', '', rec['doi'])
            
    if rec['auts']:
        recs.append(rec)
    print '  ', rec
    
    







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

