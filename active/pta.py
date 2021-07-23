# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest  Polskie Towarzystwo Astronomiczne
# FS 2018-10-15

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
publisher = 'Polskie Towarzystwo Astronomiczne'

typecode = 'C'
vol = sys.argv[1]
jnlfilename = 'pta'+vol
cnum = False
if len(sys.argv) > 2:
    cnum = sys.argv[2]
    jnlfilename += '_' + cnum

    
urltrunk = 'https://www.pta.edu.pl/proc/v%sp1' % (vol)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))

for meta in tocpage.head.find_all('meta', attrs = {'property' : 'dc:title'}):
    booktitle = meta['content']

sectitle = False
recs = []
for p in tocpage.body.find_all('p'):
    for strong in p.find_all('strong'):
        sectitle = p.text.strip()
    for b in p.find_all('b'):
        sectitle = False
    for a in p.find_all('a'):
        if a.has_attr('href'):
            if re.search('^\/proc\/v%s' % (vol), a['href']) and not a['href'] == 'urltrunk':
                rec = {'jnl' : 'BOOK', 'note' : [booktitle], 'tc' : typecode,
                       'artlink' : 'https://www.pta.edu.pl' + a['href'],
                       'bookseries' : [('a', 'Proceedings of the Polish Astronomical Society'), ('v', vol)]}
                if sectitle:
                    rec['note'].append(sectitle)
                if len(sys.argv) > 2:
                    rec['cnum'] = sys.argv[2]
                recs.append(rec)

i = 0                
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for div in artpage.body.find_all('div', attrs = {'class' : 'content'}):
        for p in div.find_all('p', attrs = {'class' : 'rtejustify'}):
            rec['abs'] = p.text.strip()
        for p in div.find_all('p'):
            pt = p.text.strip()
            if 'tit' in rec.keys() and not 'auts' in rec.keys():
                pt = re.sub(' and ', ', ', pt)
                rec['auts'] = re.split(' *, ', pt)
            if not 'tit' in rec.keys():
                for strong in p.find_all('strong'):
                    rec['tit'] = pt
            for em in p.find_all('em'):
                rec['p1'] = re.sub('.*?(\d+)\-\d+.*', r'\1', pt)
                rec['p2'] = re.sub('.*?\d+\-(\d+).*', r'\1', pt)
                rec['year'] = re.sub('.*\((\d\d\d\d)\).*', r'\1', pt)
        for a in div.find_all('a'):
            if a.has_attr('href'):
                if re.search('pdf$', a['href']):
                    rec['FFT'] = a['href']



                                       
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
 
