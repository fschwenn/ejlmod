# -*- coding: utf-8 -*-
#harvest theses from Rostock U.
#FS: 2021-03-21

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Rostock U.'
jnlfilename = 'THESES-ROSTOCK-%s' % (stampoftoday)

rpp = 20
pages = 1

boring = []

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
artlinks = []
for ddc in ['530', '510', '500']:
    for j in range(pages):
        tocurl = 'http://rosdok.uni-rostock.de/browse/epub?_search=811f238e-c54c-48f3-8b0a-3f35a06f6650&_add-filter=%2Bir.sdnb_class.facet%3ASDNB%3A' + ddc + '&_start=' + str(rpp*j) + '&_add-filter=%2Bir.doctype_class.facet%3Adoctype%3Aepub.dissertation'
        print '==={ %s }==={ %i/%i }==={ %s }===' % (ddc, j+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for span in tocpage.body.find_all('span', attrs = {'class' : 'ir-pagination-btn-numfound'}):
            print span.text
        divs = tocpage.body.find_all('div', attrs = {'class' : 'col-sm-9'})
        for div in divs:
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : ['DDC:'+ddc]}
            for tr in div.find_all('tr'):
                if re.search('purl.uni-rostock.de', tr.text):
                    rec['artlink'] = tr.text.strip()
                    if not rec['artlink'] in artlinks:
                        recs.append(rec)
                        artlinks.append(rec['artlink'])
        time.sleep(15)

i = 0
for rec in recs:
    i += 1
    keepit = True
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
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DC.issued':
                rec['date'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #URN
            elif meta['name'] == 'DC.identifier':
                if re.search('^urn',  meta['content']):
                    rec['urn'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.description':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
            #rights
            elif meta['name'] == 'DC.rights':
                if re.search('^CC',  meta['content']):
                    rec['license'] = {'statement' : re.sub(' ', '-', meta['content'])}
    for tr in artpage.find_all('tr'):
        for th in tr.find_all('th'):
            label = th.text.strip()
        for td in tr.find_all('td'):
            try:
                word = td.text.strip()
            except:
                word = ''
            if word:
                #language
                if re.search('Sprach', label):
                    if word == 'Deutsch':
                        rec['language'] = 'German'
    #license
    if not 'license' in rec.keys():
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    print '  ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
