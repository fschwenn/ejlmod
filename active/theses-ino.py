# -*- coding: utf-8 -*-
#harvest theses from INO
#FS: 2019-11-13


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'INO'


jnlfilename = 'THESES-INO-%s' % (stampoftoday)

tocurl = 'http://www.ino.tifr.res.in/ino/inoTheses.php'

print tocurl

hdr = {'User-Agent' : 'Magic Browser'}
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))

recs = []
for tr in tocpage.body.find_all('tr'):
    rec = {'tc' : 'T',  'jnl' : 'BOOK'}
    tds = tr.find_all('td')
    if len(tds) == 3:
        #date
        if re.search('\d\d\d\d', tds[0].text):
            rec['date'] = re.sub('.*(\d\d\d\d).*', r'\1', tds[0].text.strip())
        #author
        for strong in tds[1].find_all('strong'):
            rec['autaff'] = [[ strong.text.strip() ]]
            strong.replace_with('')
        #title, supervisor, aff
        tdt = re.split(' *Supervisor: *', tds[1].text.strip())
        rec['tit'] = tdt[0]
        supervisor = re.sub(' *\(.*', '', tdt[1])
        supervisor = re.sub('(Dr|Prof)\. ', '', supervisor)
        if re.search('\(', tdt[1]):
            aff = re.sub('.*\( *(.*?) *\).*', r'\1', tdt[1])
            rec['supervisor'] = [[ supervisor, aff ]]
            rec['autaff'][0].append(aff)
        else:
            rec['supervisor'] = [[ supervisor ]]
        #pdf
        for a in tds[2].find_all('a'):
            rec['FFT'] = 'http://www.ino.tifr.res.in/ino/' + a['href']
            rec['link'] = 'http://www.ino.tifr.res.in/ino/' + a['href']
            rec['doi'] = '20.2000/' + a['href'][:-4]
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
