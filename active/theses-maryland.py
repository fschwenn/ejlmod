# -*- coding: utf-8 -*-
#harvest Maryland University theses
#FS: 2018-01-31


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

publisher = 'Maryland University'

typecode = 'T'

jnlfilename = 'THESES-MARYLAND-%s' % (stampoftoday)

numberoftheses = 400
tocurl = 'https://drum.lib.umd.edu/handle/1903/2800/discover?filtertype=dateIssued&filter_relational_operator=equals&filter=[' + str(now.year-1) + '+TO+' + str(now.year+1) + ']&rpp=200'
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(4)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
    for a in div.find_all('a'):
        rec = {'jnl' : 'BOOK', 'tc' : 'T', 'tit' : a.text.strip(), 
               'keyw' : [], 'supervisor' : []}
        rec['artlink'] = 'https://drum.lib.umd.edu' + a['href']
        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
        if not  rec['hdl'] in ['1903/22153']:
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(4)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], 'Maryland U.' ]]
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['FFT'] = meta['content']
            elif meta['name'] == 'DC.identifier':
                if re.search('doi:', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #elif meta['name'] == 'DC.contributor':
            #    rec['supervisor'].append([meta['content']])
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'DCTERMS.available'}):
        rec['date'] = re.sub('T.*', '', meta['content'])
    for div in artpage.body.find_all('div', attrs = {'class' : 'simple-item-view-advisor'}):
        for p in div.find_all('div'):
            rec['supervisor'].append([ re.sub('^Dr. ', '', p.text.strip()) ])
    
    
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
