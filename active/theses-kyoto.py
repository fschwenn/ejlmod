# -*- coding: utf-8 -*-
#harvest theses from University of Kyoto
#FS: 2019-09-27


import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time
import json
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Kyoto U.'

typecode = 'T'

jnlfilename = 'THESES-KYOTO-%s' % (stampoftoday)

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}
tocurl = 'https://www-he.scphys.kyoto-u.ac.jp/theses/index.html'
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
recs = []
table = tocpage.body.find_all('table')[0]
for thead in table.find_all('thead'):
    thead.replace_with('')
for tr in table.find_all('tr'):
    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
    tds = tr.find_all('td')
    i = len(tds)-3
    rec['autaff'] = [[tds[i].text.strip(), 'Kyoto U.']]
    rec['tit'] = re.sub('[\n\t]', ' ', tds[1+i].text.strip())
    for a in tds[1+i].find_all('a'):
        rec['link'] = 'https://www-he.scphys.kyoto-u.ac.jp/theses/' + a['href'][2:]
        rec['FFT'] = 'https://www-he.scphys.kyoto-u.ac.jp/theses/' + a['href'][2:]
        rec['doi'] = '20.2000/KYOTO/' + re.sub('\W', '', a['href'])
    rec['date'] = tds[2+i].text.strip()
    recs.append(rec)


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
