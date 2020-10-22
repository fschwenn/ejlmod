# -*- coding: utf-8 -*-
#harvest theses from Iowa State U. (main)
#FS: 2020-04-08

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

publisher = 'Iowa State U. (main)'
hdr = {'User-Agent' : 'Magic Browser'}

prerecs = []
jnlfilename = 'THESES-IOWASTATE-%s' % (stampoftoday)

tocurl = 'https://lib.dr.iastate.edu/physastro_etd/'
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
time.sleep(2)
for div in tocpage.body.find_all('div', attrs = {'id' : 'series-home'}):
    year = False
    for child in div.children:
        try:
            child.name
        except:
            continue
        if child.name == 'h4':
            for span in child.find_all('span'):
                year = int(span.text.strip())
                print '==={ %i }===' % (year)
        elif child.name == 'p' and year:
            if year > now.year - 2:
                for a in child.find_all('a'):
                    if a.has_attr('href') and re.search('\d$', a['href']):
                        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'link' : a['href'], 'note' : [],
                               'year' : str(year), 'supervisor' : []}
                        rec['tit'] = a.text.strip()
                        rec['doi'] = '20.2000/IowaStateU/' + re.sub('.*\/', '', a['href'])
                        prerecs.append(rec)
            else:
                break

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
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
            if meta['name'] == 'author':
                rec['autaff'] = [[ meta['content'] ]]
            #keywords
            elif meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #abstract
            elif meta['name'] == 'description':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'bepress_citation_date':
                rec['date'] = meta['content']
            #PDF
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['hidden'] = meta['content']
            #degree
            elif meta['name'] == 'bepress_citation_dissertation_name':
                if meta['content'] in ['Master of Science']:
                    keepit = False
                else:
                    rec['note'].append(meta['content'])
    rec['autaff'][-1].append(publisher)
    #subject
    for div in artpage.body.find_all('id', attrs = {'id' : 'major'}):
        for p in div.find_all('p'):
            rec['note'].append(p.text.strip())
    #supervisor
    for div in artpage.body.find_all('id', attrs = {'id' : 'advisor1'}):
        for p in div.find_all('p'):
            rec['supervisor'].append([p.text.strip()])
    for div in artpage.body.find_all('id', attrs = {'id' : 'advisor2'}):
        for p in div.find_all('p'):
            rec['supervisor'].append([p.text.strip()])
    #pages
    for div in artpage.body.find_all('id', attrs = {'id' : 'file_size'}):
        for p in div.find_all('p'):
            rec['pages'] = re.sub('\D', '', p.text.strip())
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)

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


