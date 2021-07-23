# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Annals of the University of Craiova Physics AUC
# FS 2021-05-20

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'University of Craiova'
year = sys.argv[1]
vol = sys.argv[2]
tocurl = 'http://cis01.central.ucv.ro/pauc/vol/%s_%s/pauc_%s.html' % (year, vol, year)
jnlfilename = 'auc%s' % (vol)
if len(sys.argv) > 3:
    part = sys.argv[3]
    tocurl = 'http://cis01.central.ucv.ro/pauc/vol/%s_%s_part%s/pauc_%s_part%s.html' % (year, vol, part, year, part)
    jnlfilename = 'auc%s.%s' % (vol, part)
    
try:
    print tocurl
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")

recs = []
rec = {}
for td in tocpage.body.find_all('td'):
    #authors
    for strong in td.find_all('strong'):
        rec = {'jnl' : 'Ann.U.Craiova Phys.', 'tc' : 'P', 'year' : year, 'auts' : [], 'vol' : vol}
        authors = strong.text.strip()
        for aut in re.split(', ', authors):
            if len(aut) > 2:
                rec['auts'].append(aut)
        strong.decompose()
        if len(sys.argv) > 3:
            rec['issue'] = part
        #title and PDF
        for a in td.find_all('a'):
            rec['link'] = re.sub('(.*\/).*', r'\1', tocurl) + a['href']
            rec['FFT'] = rec['link']
            rec['tit'] = re.sub('^, *', '', a.text.strip())
    #pages
    if rec.has_key('tit'):
        pages = td.find_all('span', attrs = {'style' : 'width:40px;'})
        if not pages:
            pages = td.find_all('div', attrs = {'align' : 'right'})        
        for span in pages:
            rec['p1'] = re.sub('\-.*', '', span.text.strip())
            rec['p2'] = re.sub('.*\-', '', span.text.strip())
            recs.append(rec)
            print rec.keys()
            rec = {}
            pags = []

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()

