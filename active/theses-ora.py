# -*- coding: utf-8 -*-
#harvest Oxford University Reseach Archive for theses
#FS: 2018-01-25


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

publisher = 'Oxford University'

typecode = 'T'

jnlfilename = 'THESES-ORA-%s' % (stampoftoday)

tocurl = 'https://ora.ox.ac.uk/search/detailed?q=%2A%3A%2A&truncate=450&filterf_subject=%22Physics%22&filterf_thesisLevel=%22Doctoral%22&rows=500&sort=timestamp%20desc'
tocurl = 'https://ora.ox.ac.uk/?f%5Bf_degree_level%5D%5B%5D=Doctoral&f%5Bf_type_of_work%5D%5B%5D=Thesis&f%5Bf_subjects%5D%5B%5D=Physics&per_page=100&q=&search_field=all_fields&sort=publication_date+desc'

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

prerecs = []
#for div in tocpage.find_all('div', attrs = {'class' : 'response_doc'}):
for div in tocpage.find_all('section', attrs = {'class' : 'document-metadata-header'}):
    rec = {'jnl' : 'BOOK', 'tc' : typecode, 'keyw' : [], 'note' : []}
    isnew = True
    for li in div.find_all('li'):
        lit = li.text.strip()
        if re.search('^2\d\d\d', lit):
            rec['date'] = li.text.strip()
            year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
            if year < now.year - 1:
                isnew = False
    for h3 in div.find_all('h3'):
        rec['tit'] = h3.text.strip()
        for a in h3.find_all('a'):
            rec['link'] = 'https://ora.ox.ac.uk' + a['href']
            rec['doi'] = re.sub('.*:', '20.2000/', a['href'])
    if isnew:
        prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    i += 1
    print '%i/%i' % (i, len(prerecs))
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))

    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #fulltext
            if meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'prism.keyword':
                rec['keyw'].append(meta['content'])
            #author
            elif meta['name'] == 'citation_author':
                rec['auts'] = [ meta['content'] ]
            #subject
            elif meta['name'] == 'DC.subject':
                rec['note'].append(meta['content'])
    #bad metadata
    if not rec.has_key('auts'):
        rec['auts'] = [ 'Mustermann, Martin' ]
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
