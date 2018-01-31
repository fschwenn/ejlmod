# -*- coding: utf-8 -*-
#harvest theses from SISSA
#FS: 2018-01-30


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

publisher = 'SISSA'

typecode = 'T'

jnlfilename = 'THESES-SISSA-%s' % (stampoftoday)

tocurl = 'http://preprints.sissa.it/xmlui/handle/1963/3/recent-submissions?offset='


prerecs = []
for offset in [0]:
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('%s%i' % (tocurl, offset)))
        time.sleep(3)
    except:
        print "retry %s%i in 180 seconds" % (tocurl, offset)
        time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('%s%i' % (tocurl, offset)))
    for ul in tocpage.body.find_all('ul', attrs = {'class' : 'ds-artifact-list'}):
        for li in ul.find_all('li'):
            rec = {'jnl' : 'BOOK', 'tc' : typecode, 'keyw' : [], 'supervisor' : []}
            for div in li.find_all('div', attrs = {'class' : 'artifact-title'}):
                for a in div.find_all('a'):
                    rec['link'] = 'http://preprints.sissa.it' + a['href']
                    rec['doi'] = '20.2000/SISSA/' + re.sub('\W', '', a['href'])
                    rec['tit'] = a.text.strip()
            for span in li.find_all('span', attrs = {'class' : 'publisher-date'}):
                rec['date'] = re.sub('.*?(\d.*\d).*', r'\1', span.text.strip())
            prerecs.append(rec)

recs = []
i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i}---{ %s}------' % (i, len(prerecs), rec['link'])
    year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
    if year < now.year - 1:
        continue
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DC.creator':
                rec['auts'] = [ meta['content'] ]
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.description':
                rec['note'] = [ meta['content'] ]
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'DC.contributor':
                if not meta['content'] in ['Physics', 'Neuroscience', 'Mathematics']:
                    rec['supervisor'].append([ meta['content'] ])
    for div in artpage.body.find_all('div', attrs = {'class' : 'file-link'}):
        for a in div.find_all('a'):
            rec['FFT'] = 'http://preprints.sissa.it' + a['href']
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
