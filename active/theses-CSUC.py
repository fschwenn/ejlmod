# -*- coding: utf-8 -*-
#harvest theses from Catalonian server www.tdx.cat
#FS: 2018-02-01


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
startyear = now.year - 1

publisher = 'www.tdx.cat'

typecode = 'T'

jnlfilename = 'THESES-CSUC-%s' % (stampoftoday)

tocurls = ['http://www.tdx.cat/handle/10803/65',
           'http://www.tdx.cat/handle/10803/33551',
           'http://www.tdx.cat/handle/10803/125',
           'http://www.tdx.cat/handle/10803/442']

recs = []
for tu in tocurls:
    filterlang = 'filtertype_1=language&filter_relational_operator_1=equals&filter_1=eng'
    filterdate = 'filtertype_0=dateDefense&filter_relational_operator_0=contains&filter_0=[%i+TO+2030]' % (startyear)
    tocurl = '%s/discover?%s&%s&rpp=200' % (tu, filterlang, filterdate)
    print '==={ %s }======' % (tocurl)
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : []}
            rec['tit'] = a.text.strip()
            rec['link'] = 'http://www.tdx.cat' + a['href']
            recs.append(rec)
    print '------{ %i }------' % (len(recs))


i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DC.creator':
                rec['auts'] = [ meta['content'] ]
            elif meta['name'] == 'DCTERMS.available':
                rec['date'] = meta['content']
            elif meta['name'] == 'DC.identifier':
                if re.search('hdl.handle.net', meta['content']):
                    rec['hdl'] = re.sub('.*hdl.handle.net\/', '', meta['content'])
            elif meta['name'] == 'DCTERMS.abstract':
                if not meta.has_attr('xml:lang') or meta['xml:lang'] == 'eng':
                    rec['abs'] = meta['content']
            elif meta['name'] == 'DCTERMS.extent':
                rec['pages'] = re.sub('.*?(\d+).*', r'\1', meta['content'])
            elif meta['name'] == 'DC.publisher':
                rec['aff'] = [ meta['content'] ]
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    
    
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
