# -*- coding: utf-8 -*-
#harvest Old Dominion U.
#FS: 2021-12-13

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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Old Dominion U. (main)'

jnlfilename = 'THESES-OLDDOMINION-%s' % (stampoftoday)
boringdegrees = []
basetocurl = 'https://digitalcommons.odu.edu/'
prerecs = []
for (url, aff, fc) in [('physics_etds/', 'Old Dominion U.', ''),
                       ('mathstat_etds/', 'Old Dominion U. (main)', 'm')]:
    tocurl = basetocurl + url
    print tocurl
    try:
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'id' : 'series-home'}):
        for child in div.children:
            try:
                name = child.name
            except:
                continue
            if name == 'h4':
                for span in child.find_all('span'):
                    date = span.text.strip()
            elif name == 'p':
                if child.has_attr('class') and 'article-listing' in child['class']:
                    #year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
                    if int(date) >= now.year - 1:
                        rec = {'jnl' : 'BOOK', 'tc' : 'T', 'date' : date, 'note' : []}
                        if fc:
                            rec['fc'] = fc
                        for a in child.find_all('a'):
                            rec['tit'] = a.text.strip()
                            rec['artlink'] = a['href']
                            a.replace_with('')
                            prerecs.append(rec)
    print '  ', len(prerecs)


recs = []
i = 0
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #abstract
            if meta['name'] == 'description':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #author
            elif meta['name'] == 'bepress_citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #fulltext
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['pdf_url'] = meta['content']
            #DOI
            elif meta['name'] == 'bepress_citation_doi':
                rec['doi'] = re.sub('^ht.*?\/10', '10', meta['content'])
            #date
            elif meta['name'] == 'bepress_citation_date':
                rec['date'] = meta['content']
    #ORCID
    for div in artpage.body.find_all('div', attrs = {'id' : 'orcid'}):
        for p in div.find_all('p'):
            rec['autaff'][-1].append('ORCID:'+re.sub('.*org\/', '', p.text.strip()))
    rec['autaff'][-1].append(publisher)
    #degree
    for div in artpage.body.find_all('div', attrs = {'id' : 'degree_name'}):
        for p in div.find_all('p'):
            degree = p.text.strip()
            rec['note'].append(degree)
            if degree in boringdegrees:
                print '    skip "%s"' % (degree)
                keepit = False
    #peusoDOI
    if not rec.has_key('doi'):
        rec['doi'] = '20.2000/OldDominion/' + re.sub('\W', '', re.sub('.*edu', '', rec['artlink']))
        rec['link'] = rec['artlink']
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    #ISBN
    for div in artpage.body.find_all('div', attrs = {'id' : 'identifier'}):
        for h4 in div.find_all('h4'):
            if h4.text.strip() == 'ISBN':
                for p in div.find_all('p'):
                    ISBN = p.text.strip()
                    rec['isbn'] = ISBN
    if keepit:
        print ' ' , rec.keys()
        recs.append(rec)


#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
