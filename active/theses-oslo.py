# -*- coding: utf-8 -*-
#harvest theses from Oslo
#FS: 2020-08-21

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

publisher = 'Oslo U.'
rpp = 20
numofpages = 1
jnlfilename = 'THESES-OSLO-%s' % (stampoftoday)


hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for (depnr, dep) in [(14, 'Phys'), (11, 'Astro'), (6, 'Math')]:
    for i in range(numofpages):
        tocurl = 'https://www.duo.uio.no/handle/10852/' + str(depnr) + '/discover?order=DESC&rpp=' + str(rpp) + '&sort_by=dc.date.issued_dt&page=' + str(i+1) + '&group_by=none&etal=0&filtertype_0=type&filter_0=Doktoravhandling&filter_relational_operator_0=equals'
        print '---{ %i %s }---{ %i/%i }---{ %s }------' % (depnr, dep, i+1, numofpages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(2)
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
            for a in div.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'oa' : False, 'note' : []}
                rec['link'] = 'https://www.duo.uio.no' + a['href']
                rec['hdl'] = re.sub('\/handle\/', '', a['href'])
                rec['tit'] = a.text.strip()
                recs.append(rec)
            
j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['link'])
    req = urllib2.Request(rec['link'])
    artpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    #author
    for meta in artpage.find_all('meta', attrs = {'name' : 'DC.reator'}):
        rec['autaff'] = [[ meta['content'], publisher ]]
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #author
            elif meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] in ['nob', 'nor']:
                    rec['language'] = 'norwegish'
                elif meta['content'] != 'eng':
                    rec['note'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta.has_attr('xml:lang'):
                    if meta['xml:lang'] in ['eng', 'en_US']:
                        rec['abs'] = meta['content']
                    else:
                        print meta['xml:lang']
            #rights
            elif meta['name'] == 'DC.rights':
                if meta.has_attr('xml:lang') and meta['xml:lang'] == 'eng':
                    print '  ', meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #URN
            elif meta['name'] == 'DC.identifier':
                if re.search('^URN', meta['content']):
                    rec['urn'] = meta['content']
    print '  ', rec.keys()
            
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
