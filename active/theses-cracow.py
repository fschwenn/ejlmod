# -*- coding: utf-8 -*-
#harvest theses from Cracow
#FS: 2019-12-05


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

publisher = 'Jagiellonian U. (main)'

typecode = 'T'

jnlfilename = 'THESES-CRACOW-%s' % (stampoftoday)
years = [str(now.year - 1), str(now.year)]

hdr = {'User-Agent' : 'Magic Browser'}

tocurl = 'https://fais.uj.edu.pl/dla-studentow/studia-doktoranckie/prace-doktorskie'
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'post-folded__nav'}):
    for h3 in div.find_all('h3'):
        for span in h3.find_all('span'):
            year = span.text.strip()
            print '---{ %s }---' % (year)
    if year in years:
        for tr in div.find_all('tr'):
            rec = {'tc' : 'T', 'year' : year, 'date' : year, 'jnl' : 'BOOK',
                   'note' : ['Vorsicht! Keine Abstracts vorhanden!']}
            tds = tr.find_all('td')
            if len(tds) == 3:
                for a in tds[1].find_all('a'):
                    if re.search('http', a['href']):
                        rec['FFT'] = re.sub('\.pdf\/.*', '.pdf', a['href'])
                    else:
                        rec['FFT'] = 'https://fais.uj.edu.pl' + re.sub('\.pdf\/.*', '.pdf', a['href'])
                    rec['doi'] = '20.2000/cracow/' + re.sub('\W', '', re.sub('.*documents', '', a['href']))
                    rec['link'] = rec['FFT']
                    rec['tit'] = a.text.strip()
                    rec['autaff'] = [[tds[0].text.strip(), publisher]]
                    if re.search('PL', tds[2].text):
                        rec['language'] = 'polish'
                    recs.append(rec)





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
