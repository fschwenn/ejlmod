#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest The African Review of Physics
# FS 2012-06-01

import os
import ejlmod2
import codecs
import re
import sys
import unicodedata
import string
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import datetime


tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)


publisher = 'The Abdus Salam International Centre for Theoretical Physics'
jnl = 'arp'
vol = sys.argv[1]
year = sys.argv[2]

jnlfilename = '%s%s_%s' % (jnl, vol, stampoftoday)
jnlname = 'Afr.Rev.Phys.'

urltrunk = 'http://aphysrev.ictp.it/index.php/aphysrev/issue/view/%i' % (int(vol)+22)


recs = []
recnr = 1
print "get table of content of %s%s ..." %(jnlname,vol)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))


i = 0
for table in tocpage.body.find_all('table', attrs = {'class' : 'tocArticle'}):
    i += 1
    print i
    rec = {'year' : year, 'jnl' : jnlname, 'vol' : vol, 'tc' : 'P',
           'auts' : []}
    for td in table.find_all('td'):
        if td.has_attr('class'):
            if  'tocTitle' in td['class']:
                rec['tit'] = td.text.strip()
            elif 'tocPages' in td['class']:
                rec['p1'] = td.text.strip()
            elif 'tocGalleys' in td['class']:
                for a in td.find_all('a'):
                    rec['FFT'] = a['href']
                    rec['pdf'] = a['href']
            elif 'tocAuthors' in td['class']:
                for aut in re.split(' *, *', td.text.strip()):
                    rec['auts'].append(re.sub('\t', '', aut))
    if not rec.has_key('p1') or not rec['p1']:
        rec['p1'] = 'dummy%03i' % (i)
    recs.append(rec)





xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile  = open(xmlf,'w')
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
