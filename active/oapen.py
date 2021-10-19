# -*- coding: utf-8 -*-
#harvest books from oapen.org
#FS: 2021-10-19

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

rpp = 50
pages = 1
publishers = {}
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for page in range(pages):
    tocurl = 'https://library.oapen.org/browse?rpp=' + str(rpp) + '&offset=' + str(rpp*page) + '&etal=-1&sort_by=3&type=collection&value=SCOAP3+for+Books&order=DSC'
    print '---{ %i/%i }---{ %s }---' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for li in tocpage.body.find_all('li', attrs = {'class' : 'ds-artifact-item'}):
        rec = {'tc' : 'B', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'autaff' : []}
        for div in li.find_all('div', attrs = {'class' : 'artifact-title'}):
            for a in div.find_all('a'):
                rec['artlink'] = 'https://library.oapen.org' + a['href']
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            recs.append(rec)
    time.sleep(3)

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
            if meta['name'] == 'citation_author':
                rec['autaff'].append([ meta['content'] ])
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
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
            #ISBN
            elif meta['name'] == 'citation_isbn':
                if 'isbns' in rec.keys():
                    rec['isbns'].append([('a', re.sub('\-', '', meta['content']))])
                else:
                    rec['isbns'] = [[('a', re.sub('\-', '', meta['content']))]]
            #pages
            elif meta['name'] == 'citation_pages':
                rec['pages'] = meta['content']
            #publisher
            elif meta['name'] == 'citation_publisher':
                rec['publisher'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if rec['publisher'] in publishers.keys():
        publishers[rec['publisher']].append(rec)
    else:
        publishers[rec['publisher']] = [rec]
    print '   ', rec.keys()
    print '    ', [(s, len(publishers[s])) for s in publishers.keys()]

for publisher in publishers.keys():
    jnlfilename = 'oapen_%s.%s' % (stampoftoday, re.sub('\W', '', publisher))
    #closing of files and printing
    xmlf = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(publishers[publisher], xmlfile, publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
