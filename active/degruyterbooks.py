# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest PDe Gruyter Book series
# FS 2016-01-03

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

serial = sys.argv[1]

jnlfilename = 'dg' + serial
if serial == '129734':
    jnl = "De Gruyter Stud.Math.Phys."

#get list of volumes
os.system("wget -T 300 -t 3 -q -O /tmp/dg%s %s%s%s" % (serial, urltrunc, '/view/serial/', serial))
inf = open('/tmp/dg%s' % (serial), 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()))
inf.close()
#get volumes
recs = []
i = 0
for a in tocpage.find_all('a', attrs = {'class' : 'tocLink'}):
    i += 1
    vollink = urltrunc + a['href']
    print vollink
    rec = {'tc' : 'B', 'jnl' : jnl}
    #authors
    for span in a.find_all('span', attrs = {'class' : 'authors'}):
        authors = re.sub(': *$', '', span.text)
        rec['auts'] = re.split(' *\/ *', authors)
    for span in a.find_all('span', attrs = {'class' : 'editors'}):
        authors = re.sub(': *$', '', span.text)
        rec['auts'] = []
        for editor in re.split(' *\/ *', authors):
            rec['auts'].append(editor + ' (Ed.)')
    #title
    for span in a.find_all('span', attrs = {'class' : 'title'}):
        rec['tit'] = span.text.strip()
    #year
    for span in a.find_all('span', attrs = {'class' : 'year'}):
        rec['year'] = re.sub('.*?(\d+).*', r'\1', span.text.strip())
    #volume
    for span in a.find_all('span', attrs = {'class' : 'volNo'}):
        rec['vol'] = re.sub('.*?(\d+).*', r'\1', span.text.strip())
    #get details
    os.system("wget -T 300 -t 3 -q -O /tmp/dg%s.%i %s" % (serial, i, vollink))
    inf = open('/tmp/dg%s.%i' % (serial, i), 'r')
    volpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    #abstract
    rec['abs'] = ''
    for div in volpage.find_all('div', attrs = {'class' : 'region-padding'}):
        for h3 in div.find_all('h3', attrs = {'id' : 'overviewTitle'}):
            for p in div.find_all('p'):
                rec['abs'] += p.text
    #isbn
    for dd in volpage.find_all('dd', attrs = {'id' : 'isbn'}):
        rec['isbn'] = dd.text
    #number of pages
    for dt in volpage.find_all('dt', attrs = {'id' : 'pages'}):
        rec['pages'] = re.sub('.*?(\d+).*', r'\1', dt.text.strip())
    #keywords
    for dd in volpage.find_all('dd', attrs = {'id' : 'keywords'}):
        rec['keyw'] = re.split(', ', dd.text)
    print rec
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

