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
tocurl = 'https://drum.lib.umd.edu/handle/1903/2800/browse?type=dateissued&submit_browse=Issue+Date&rpp=%i&order=DESC' % (numberoftheses)

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(4)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for ul in tocpage.body.find_all('ul', attrs = {'class' : 'ds-artifact-list'}):
    for li in ul.find_all('li'):
        for h4 in li.find_all('h4'):
            for a in h4.find_all('a'):
                rec = {'jnl' : 'BOOK', 'tc' : 'T', 'tit' : a.text.strip(), 
                       'keyw' : [], 'supervisor' : []}
                rec['link'] = 'https://drum.lib.umd.edu' + a['href']
                rec['doi'] = '20.2000/MARYLAND/' + re.sub('\W', '', a['href'])
            for span in li.find_all('span', attrs = {'class' : 'date'}):
                rec['date'] = span.text.strip()
                year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
                if year >= now.year - 1*100:
                    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(4)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'DC.type':
                if meta['content'] == "Dissertation":
                    rec['MARC'] = [('502', [('d', rec['date']), ('c', 'Maryland U.'), ('b', 'PhD')])]                    
            elif meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], 'Maryland U.' ]]
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['FFT'] = meta['content']
            elif meta['name'] == 'DC.identifier':
                if re.search('doi:', meta['content']):
                    rec['doi'] = meta['content'][4:]
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
