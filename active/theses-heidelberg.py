# -*- coding: utf-8 -*-
#harvest theses from Heidelberg
#FS: 2019-09-15


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

publisher = 'U. Heidelberg (main)'

typecode = 'T'

jnlfilename = 'THESES-HEIDELBERG-%s' % (stampoftoday)
if now.month <= 8:
    years = [str(now.year - 1), str(now.year)]
else:
    years = [str(now.year)]

tocurl = 'http://archiv.ub.uni-heidelberg.de/volltextserver/view/type/doctoralThesis.html'
print tocurl
hdr = {'User-Agent' : 'Magic Browser'}
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
prerecs = []
ps = tocpage.body.find_all('p')
i = 0 
for p in ps:
    i += 1
    for span in p.find_all('span', attrs = {'class' : 'person_name'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'pacs' : []}
        for a in p.find_all('a'):
            rec['artlink'] = a['href']
            rec['tit'] = a.text.strip()
            a.replace_with('')
        pt = re.sub('[\n\t\r]', ' ', p.text.strip())
        if re.search('\(\d\d\d\d\)', pt):
            rec['date'] = re.sub('.*\((\d\d\d\d)\).*', r'\1', pt)
            if rec['date'] in years:
                prerecs.append(rec)
    print '%i/%i %s %i' % (i, len(ps), rec['date'], len(prerecs))

i = 0
recs = []
repacs = re.compile('(\d\d\.\d\d.\d[a-z]).*')
for rec in prerecs:
    i += 1
    time.sleep(3)
    print '---{ %i/%i %i }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))

    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'eprints.creators_name':
                rec['autaff'] = [[ meta['content'] ]]
                rec['autaff'][-1].append('U. Heidelberg (main)')
            #keywords
            elif meta['name'] == 'eprints.keywords':
                for keyw in re.split(' *, *', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'ger':
                    rec['language'] = 'german'
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['FFT'] = meta['content']
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('^DOI', meta['content']):
                    rec['doi'] = re.sub('DOI:', '', meta['content'])
            #abstract
            elif meta['name'] == 'DC.description':
                rec['abs'] = meta['content']
            #license            
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
            #PACS
            elif meta['name'] == 'eprints.class_labels':
                if repacs.search(meta['content']):
                    rec['pacs'].append(repacs.sub(r'\1', meta['content']))
            #DDC
            elif meta['name'] == 'eprints.subjects':
                if not 'ddc' in rec.keys():
                    rec['ddc'] = meta['content']
                elif meta['content'] < rec['ddc']:
                    rec['ddc'] = meta['content']

    if 'ddc' in rec.keys():
        if rec['ddc'][0] == '5':
            rec['note'] = [' DDC: %s ' % (rec['ddc'])]
            recs.append(rec)

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
