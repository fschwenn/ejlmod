# -*- coding: utf-8 -*-
#harvest theses from University of Edinburgh
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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Edinburgh U.'
rpp = 50
pages = 1

jnlfilename = 'THESES-EDINBURGH-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}
recs = []
hdls = []
for page in range(pages):
    tocurl = 'https://www.era.lib.ed.ac.uk/handle/1842/3420/discover?sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&page=' + str(page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://www.era.lib.ed.ac.uk' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            if not rec['hdl'] in hdls:
                recs.append(rec)
                hdls.append(rec['hdl'])
    time.sleep(5)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('Edinburgh U.')
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org\/', meta['content']):
                    rec['doi'] = re.sub('.*org\/', '', meta['content'])
            #supervisor
            #elif meta['name'] == 'DC.contributor':
            #    supervisor = re.sub(' *\[.*', '', meta['content'])
            #    rec['supervisor'] = [[ supervisor ]]
            #    rec['supervisor'][-1].append('Edinburgh U.')



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
