# -*- coding: utf-8 -*-
#harvest theses from MIT
#FS: 2019-09-13


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

publisher = 'MIT'

typecode = 'T'

jnlfilename = 'THESES-MIT-%s' % (stampoftoday)

tocurl = 'https://dspace.mit.edu/handle/1721.1/7695/discover?sort_by=dc.date.issued_dt&order=desc&rpp=200'


print tocurl

hdr = {'User-Agent' : 'Magic Browser'}

prerecs = []
for offset in [0]:
#    try:
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
#    except:
#        print "retry in 180 seconds"
#        time.sleep(180)
#        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('%s%i' % (tocurl, offset)))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://dspace.mit.edu' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)


recs = []
i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i}---{ %s}------' % (i, len(prerecs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['link'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('MIT')
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'por':
                    rec['language'] = 'portuguese'
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d+ pages', meta['content']):
                    rec['pages'] = re.sub('\D*(\d+) pages.*', r'\1', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #license            
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
                    
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
