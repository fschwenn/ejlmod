# -*- coding: utf-8 -*-
#harvest theses from Sussex U.
#FS: 2020-03-23


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Sussex U.'
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
jnlfilename = 'THESES-SUSSEX-%s' % (stampoftoday)

for year in [now.year, now.year-1]:
    tocurl = 'http://sro.sussex.ac.uk/view/divisions/d234/%i.html' % (year)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for p in tocpage.find_all('p'):
        if re.search('PhD', p.text):
            for a in p.find_all('a'):
                if a.has_attr('href'):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'link' : a['href'], 'note' : []}
                    rec['tit'] = a.text.strip()
                    rec['doi'] = '20.2000/UCLodon/' + re.sub('\D', '', a['href'])
                    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(10)
    except:
        try:
            print 'retry %s in 180 seconds' % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print 'no access to %s' % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'eprints.creators_name':
                rec['autaff'] = [[ meta['content'] ]]
            #ORCID
            elif meta['name'] == 'eprints.creators_orcid':
                rec['autaff'][-1].append(re.sub('.*(\d{4}\-\d{4}\-\d{4}\-\d{4}).*', r'ORCID:\1', meta['content']))
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'eprints.date':
                rec['date'] = meta['content']
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', meta['content'])
            #DOI
            elif meta['name'] == 'eprints.doi':
                rec['doi'] = meta['content']
            #number of pages
            elif meta['name'] == 'eprints.pages':
                rec['pages'] = meta['content']
            #PDF
            elif meta['name'] == 'DC.identifier':
                if re.search('pdf$', meta['content']):
                    rec['hidden'] = meta['content']
            #PDF
            elif meta['name'] == 'eprints.thesis_award':
                rec['note'].append(meta['content'])
    rec['autaff'][-1].append(publisher)
    print '  ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, 'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text:
    retfiles = open(retfiles_path, 'a')
    retfiles.write(line)
    retfiles.close()


