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

publisher = 'UNESP'

typecode = 'T'

jnlfilename = 'THESES-UNESP-%s' % (stampoftoday)

tocurl = 'https://repositorio.unesp.br/handle/11449/77166/discover?filtertype=dateIssued&filter_relational_operator=equals&filter=[' + str(now.year - 1) + '+TO+' + str(now.year + 1) + ']&rpp=100'


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
            rec['artlink'] = 'https://repositorio.unesp.br' + a['href'] + '?show=full'
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
                if re.search('\[UNESP\]', meta['content']):
                    rec['autaff'][-1].append('Universidade Estadual Paulista (UNESP), Instituto de Fisica Teorica (IFT), 01140-070, Sao Paulo, Brazil')
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
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['xml:lang'] == 'en':
                    rec['abs'] = meta['content']
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
