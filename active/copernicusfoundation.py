#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest Copernicus Foundation for Polish Astronomy
# FS 2019-07-22

import os
import ejlmod2
import codecs
import re
import sys
import urllib2
import urlparse
from bs4 import BeautifulSoup
import time



tmpdir = '/tmp'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

publisher = 'Copernicus Foundation for Polish Astronomy'
tc = 'P'
jnl = 'Acta Astron.'

vol = sys.argv[1]
isu = sys.argv[2]

tocurl = 'http://acta.astrouw.edu.pl/Vol%s/n%s/' %  (vol, isu)
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
    
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for table in tocpage.body.find_all('table', attrs = {'class' : 'text'}):
    for tr in table.find_all('tr'):
        for a in tr.find_all('a'):
            if re.search('Abstract', a.text):
                rec = {'jnl' : jnl, 'vol' : vol, 'issue' : isu, 'auts' : [],
                       'tc' : 'P', 'artlink' : '%s/%s' % (tocurl, a['href'])}
        for td in tr.find_all('td', attrs = {'class' : 'sz'}):
            tdtext = re.sub(':.*', '', re.sub('[\n\t]', '', td.text.strip()))
            for author in re.split(' *, *', re.sub(' and ', ', ', tdtext)):
                rec['auts'].append(author)
        recs.append(rec)

for rec in recs:
    print rec['artlink']
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for center in artpage.find_all('center'):
        for table in center.find_all('table'):
            for i in table.find_all('i'):
                rec['doi'] = re.sub('.*?(10.*) *$', r'\1', i.text.strip())
            ttext = re.sub('[\n\t]', '', table.text.strip())
            pages = re.sub('.*pp. ([0-9\-]*).*', r'\1', ttext)
            rec['p1'] = re.sub('\-.*', '', pages)
            rec['p2'] = re.sub('.*\-', '', pages)
            rec['year'] = re.sub('.*\((20..)\).*', r'\1', ttext)
            table.replace_with('')
        for b in center.find_all('b'):
            rec['tit'] = b.text.strip()
            b.replace_with('')
        for sup in table.find_all('sup'):
            supt = sup.text.strip()
            sup.replace_with('[AFF%s]' % (supt))
    alltext = re.sub('[\n\t]', ' ', artpage.body.text.strip())
    alltext = re.sub('.*ABSTRACT *', '', alltext)
    alltext = re.sub(' *Full article text.*', '', alltext)
    if re.search('Key words:', alltext):
        kewywords = re.sub('.*Key words: *', '', alltext)
        alltext = re.sub('Key words.*', '', alltext)
        rec['keyw'] = re.split(' \- ', kewywords)
    rec['abs'] = alltext

    print rec
    
jnlfilename = 'actaastron%s.%s' % (rec['vol'], rec['issue'])


                                       
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
 
