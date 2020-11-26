# -*- coding: utf-8 -*-
#harvest theses from Melbourne U.
#FS: 2020-11-19

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Melbourne (main)'

rpp = 24
pages = 1
startyear = now.year-1
departments = [('295', 'U. Melbourne (main)'), ('310', 'Melbourne U.')]
hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-MELBOURNE-%s' % (stampoftoday)

recs = []
for (dep, aff) in departments:
    for page in range(pages):
        tocurl = 'https://minerva-access.unimelb.edu.au/handle/11343/' + dep + '/discover?sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&page=' + str(page+1)
        print '==={ %s: %i/%i }==={ %s }===' % (aff, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(3)
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            keepit = True
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'affiliation' : aff,
                   'supervisor' : []}
            for span in div.find_all('span', attrs = {'class' : 'date'}):
                if re.search('^\d\d\d\d$', span.text):
                    rec['date'] = span.text.strip()
                    if int(rec['date']) < startyear:
                        keepit = False
            for a in div.find_all('a'):                
                rec['artlink'] = 'https://minerva-access.unimelb.edu.au' + a['href'] + '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                if keepit:
                    recs.append(rec)
        print '   %i records so far' % (len(recs))

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['link'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], rec['affiliation'] ]]
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
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            if label == 'melbourne.thesis.supervisorname':
                rec['supervisor'].append([td.text.strip()])
    print '  ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
        
