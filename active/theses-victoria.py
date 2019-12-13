# -*- coding: utf-8 -*-
#harvest theses from Victoria U., Wellington
#FS: 2019-11-25


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

publisher = 'Victoria U., Wellington'
rpp = 50
numofpages = 2


hdr = {'User-Agent' : 'Magic Browser'}
for i in range(numofpages):
    recs = []
    jnlfilename = 'THESES-VICTORIA-%s_%02i' % (stampoftoday, i)
    tocurl = 'https://researcharchive.vuw.ac.nz/handle/10063/32/browse?rpp=%i&sort_by=2&type=dateissued&offset=%i&etal=-1&order=DESC' % (rpp, i*rpp)
    print '---{ %i/%i }---{ %s }------' % (i+1, numofpages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : []}
            rec['artlink'] = 'https://researcharchive.vuw.ac.nz' + a['href']
            rec['hdl'] = re.sub('\/handle\/', '', a['href'])
            rec['tit'] = a.text.strip()
            recs.append(rec)
            
    j = 0
    for rec in recs:
        j += 1
        print '---{ %i/%i }---{ %i/%i }---{ %s }------' % (i+1, numofpages, j, len(recs), rec['artlink'])
        req = urllib2.Request(rec['artlink'])
        artpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(5)
        #author
        for meta in artpage.find_all('meta', attrs = {'name' : 'DC.creator'}):
            rec['autaff'] = [[ meta['content'], publisher ]]
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name'):
                #date
                if meta['name'] == 'DC.date':
                    rec['date'] = meta['content'][:10]
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    rec['abs'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    rec['keyw'].append( meta['content'] )
                #FFT
                #elif meta['name'] == 'citation_pdf_url':
                #    rec['FFT'] = meta['content']
                #URN
        print '  ', rec.keys()
                
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


