# -*- coding: utf-8 -*-
#harvest theses from Okayama U.
#FS: 2020-08-31

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Okayama U.'

jnlfilename = 'THESES-OKAYAMA_U-%s' % (stampoftoday)

pages = 1
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
#first get links of year pages
for degree in ['%E5%8D%9A%E5%A3%AB%EF%BC%88%E5%AD%A6%E8%A1%93%EF%BC%89', '%E5%8D%9A%E5%A3%AB%EF%BC%88%E7%90%86%E5%AD%A6%EF%BC%89']:
    for page in range(pages):
        tocurl = 'http://ousar.lib.okayama-u.ac.jp/en/list/thesis_types/%s/p/%i' % (degree, page+1)
        print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for div in tocpage.body.find_all('div', attrs = {'class' : 'view-result-item'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK'}
            for div2 in div.find_all('div', attrs = {'class' : 'title'}):
                for a in div2.find_all('a'):
                    rec['link'] = 'http://ousar.lib.okayama-u.ac.jp' + a['href']
                    rec['tit'] = a.text.strip()
                    rec['doi'] = '20.2000/OKAYAMA/' + re.sub('\W', '', a['href'][21:])
            for tr in div.find_all('tr'):
                for th in tr.find_all('th'):
                    tht = th.text.strip()
                for td in tr.find_all('td'):
                    if tht == 'Author':
                        for span in td.find_all('span', attrs = {'class' : 'delim'}):
                            span.decompose()
                        rec['autaff'] = [[ td.text.strip(), publisher ]]
                    elif tht == 'Published Date':
                        rec['date'] = td.text.strip()
            recs.append(rec)
        time.sleep(5)

    
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
    
