# -*- coding: utf-8 -*-
#harvest theses from Jyvaskyla U.
#FS: 2020-09-07


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

publisher = 'Jyvaskyla U.'
jnlfilename = 'THESES-JYVASKYLA-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
tocurl = 'https://jyx.jyu.fi/handle/123456789/56990/discover?sort_by=dc.date.issued_dt&order=desc&rpp=50'
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'note' : []}
    for a in div.find_all('a'):
        rec['link'] = 'https://jyx.jyu.fi' + a['href'] #+ '?show=full'
        #rec['doi'] = '20.2000/Jyvaskyla/' + re.sub('.*handle\/', '', a['href'])
        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i}---{ %s }------' % (i, len(recs), rec['link'])
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
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]            
                rec['autaff'][-1].append(publisher)
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_isbn':
                rec['isbn'] = re.sub('\-', '', meta['content'])
            #ISBN
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['xml:lang'] == 'en':
                    rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            #URN
            elif meta['name'] == 'DC.identifier':
                if re.search('^URN', meta['content']):
                    rec['urn'] = meta['content']




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
