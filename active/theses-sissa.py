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

tocurl = 'https://iris.sissa.it/simple-search?query=&location=&sort_by=score&order=desc&rpp=100&filter_field_1=publtypeh&filter_type_1=equals&filter_value_1=8+Thesis&filter_field_2=dateIssued&filter_type_2=equals&filter_value_2=%5B' + str(now.year - 1) + '+TO+' + str(now.year + 1) + '%5D&etal=0&filtername=publtypeh&filterquery=8+Thesis%3A%3A8.1+PhD+thesis&filtertype=equals'


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
    for tr in tocpage.body.find_all('tr'):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for td in tr.find_all('td', attrs = {'headers' : 't1'}):
            for a in td.find_all('a'):
                rec['artlink'] = 'https://iris.sissa.it' + a['href']
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
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            elif meta['name'] == 'citation_author_orcid':
                rec['autaff'][-1].append( 'ORCID:' + meta['content'] )
            elif meta['name'] == 'citation_author_email':
                rec['autaff'][-1].append( 'EMAIL:' + meta['content'] )
            #title
            elif meta['name'] in ['DC.title', 'citation_title']:
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
                if meta['content'] == 'ita':
                    rec['language'] = 'italian'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    for p in artpage.body.find_all('p', attrs = {'class' : 'abstractEng'}):
        rec['abs'] = p.text.strip()
    recs.append(rec)
    print '  ', rec.keys()
    print rec


	


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
