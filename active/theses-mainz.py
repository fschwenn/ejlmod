# -*- coding: utf-8 -*-
#harvest theses from Mainz U.
#FS: 2020-01-27

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

publisher = 'Mainz U.'

jnlfilename = 'THESES-MAINZ-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}

recs = []

rpp = 40
pages = 3

for page in range(pages):
    tocurl = 'https://openscience.ub.uni-mainz.de/simple-search?query=&filter_field_1=organisationalUnit&filter_type_1=equals&filter_value_1=FB+08+Physik%2C+Mathematik+u.+Informatik&filter_field_2=publicationType&filter_type_2=equals&filter_value_2=Dissertation&sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&etal=0&start=' + str(page*rpp)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    for tr in tocpage.body.find_all('tr'):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for td in tr.find_all('td', attrs = {'headers' : 't1'}):
            rec['year'] = td.text.strip()
            rec['date'] = td.text.strip()
        for td in tr.find_all('td', attrs = {'headers' : 't3'}):
            for a in td.find_all('a'):
                rec['tit'] = a.text.strip()
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                rec['artlink'] = 'https://openscience.ub.uni-mainz.de' + a['href']
                recs.append(rec)
    time.sleep(10)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(4)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for tr in artpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
            tdt = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue'}):
            #authors
            if tdt == 'Authors:':
                rec['autaff'] = [[ td.text.strip(), publisher ]]
            #language
            elif tdt == 'Language :':
                if td.text.strip() == 'german':
                    rec['language'] = 'German'
            #abstract
            elif tdt == 'Abstract:':
                rec['abs'] = td.text.strip()
            #license
            elif re.search('Information', tdt):
                for a in td.find_all('a'):
                    if re.search('creativecommons.org', a['href']):
                        rec['license'] = {'url' : a['href']}
            #pages
            elif tdt == 'Extent:':
                if re.search('\d\d', td.text):
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', td.text.strip())
            #DOI
            elif tdt == 'DOI:':
                for a in td.find_all('a'):
                    rec['doi'] = re.sub('.*org\/', '', a['href'])                    
        #FFT
        for td in tr.find_all('td', attrs = {'class' : 'standard'}):
            for a in td.find_all('a'):
                if re.search('pdf$', a['href']):
                    if 'license' in rec.keys():
                        rec['FFT'] = 'https://openscience.ub.uni-mainz.de' + a['href']
                    else:
                        rec['hidden'] = 'https://openscience.ub.uni-mainz.de' + a['href']
    print '  ', rec.keys()

#closing of files and printing
xmlf    = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
