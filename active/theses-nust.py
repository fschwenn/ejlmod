# -*- coding: utf-8 -*-
#harvest theses from Norwegian U. Sci. Tech.
#FS: 2020-04-03

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

publisher = 'Norwegian U. Sci. Tech.'
rpp = 20


hdr = {'User-Agent' : 'Magic Browser'}
recs = []
jnlfilename = 'THESES-NUST-%s' % (stampoftoday)
tocurl = 'https://ntnuopen.ntnu.no/ntnu-xmlui/handle/11250/227485/browse?resetOffset=true&sort_by=2&order=DESC&rpp=%i&type=type&value=Doctoral+thesis' % (rpp)
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
time.sleep(2)
for div in tocpage.body.find_all('h4', attrs = {'class' : 'artifact-title'}):
    for a in div.find_all('a'):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
        rec['artlink'] = 'https://ntnuopen.ntnu.no' + a['href']
        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
        rec['tit'] = a.text.strip()
        recs.append(rec)

j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'])
    artpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    #author
    for meta in artpage.find_all('meta', attrs = {'name' : 'DC.creator'}):
        rec['autaff'] = [[ meta['content'], publisher ]]
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if not 'abs' in rec.keys():
                    rec['abs'] = meta['content']
            #subject
            elif meta['name'] == 'DC.subject':
                rec['note'].append( meta['content'] )
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #ISBN
            elif meta['name'] == 'citation_isbn':
                rec['isbn'] = meta['content']
    print '  ', rec.keys()

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
