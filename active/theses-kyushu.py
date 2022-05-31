# -*- coding: utf-8 -*-
#harvest theses from Kyushu U.
#FS: 2022-02-17

import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import unicodedata 
import codecs
import datetime
import time
import json
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
startyear = now.year-1
stopyear = now.year
publisher = 'Kyushu U., Fukuoka (main)'
pages = 2
rpp = 200
boringdegrees = ['Master Thesis', 'DOCTOR OF PHILOSOPHY (Dental Science)', 'DOCTOR OF PHILOSOPHY (Medical Science)',
                 'DOCTOR OF PHILOSOPHY (Systems Life Sciences)', 'DOCTOR OF PHILOSOPHY IN HEALTH SCIENCES',
                 'DOCTOR OF DESIGN', 'DOCTOR OF LITERATURE', 'DOCTOR OF PHILOSOPHY IN KANSEI SCIENCE',
                 'DOCTOR OF PHILOSOPHY IN NURSING', 'DOCTOR OF PHILOSOPHY (Medicinal Sciences)',
                 'DOCTOR OF AUTOMOTIVE SCIENCE', 'DOCTOR OF LAWS', 'DOCTOR OF PHILOSOPHY (Clinical Pharmacy)',
                 'DOCTOR OF PHILOSOPHY (Education)', 'DOCTOR OF PHILOSOPHY (Pharmaceutical Sciences)',
                 'DOCTOR OF PHILOSOPHY (Psychology)',
                 'DOCTOR OF ECONOMICS', 'DOCTOR OF ENGINEERING', 'DOCTOR OF PHILOSOPHY (Agricultural Science)']
              
jnlfilename = 'THESES-KYUSHU-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
for page in range(pages):
    tocurl = 'https://catalog.lib.kyushu-u.ac.jp/opac_search/?lang=1&amode=2&appname=Netscape&version=5&cmode=0&kywd=&smode=1&year1_exp=' + str(startyear) + '&year2_exp=' + str(stopyear) + '&file_exp[]=4&dpmc_exp[]=all&txtl_exp=2&sort_exp=6&disp_exp=' + str(rpp) + '&start=' + str(page*rpp+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    for ul in tocpage.body.find_all('ul', attrs = {'class' : 'result-list'}):
        for div in ul.find_all('div', attrs = {'class' : 'row'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'note' : [], 'auts' : [], 'aff' : [publisher]}
            for div2 in div.find_all('div', attrs = {'class' : 'result-book-datatypenm'}):
                if not div2.text.strip() in boringdegrees:
                    for a in div.find_all('a'):
                        rec['artlink'] = 'https://catalog.lib.kyushu-u.ac.jp' + a['href']
                        rec['hdl'] = re.sub('.*bibid=(\d+).*', r'2324/\1', a['href'])
                    if not rec['hdl'] in uninterestingDOIS:
                        prerecs.append(rec)
    time.sleep(2)
        

i = 0
recs = []
for rec in prerecs:
    keepit = True
    oa = False
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for table in artpage.find_all('table', attrs = {'class' : 'book-detail-table'}):
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                #author
                if tht == 'Creator':
                    for a in td.find_all('a'):
                        if re.search('[A-Z]', a.text):
                            rec['auts'].append(a.text.strip())
                #supervisor
                elif tht == 'Thesis Advisor':
                    for div in td.find_all('div', attrs = {'class' : 'metadata_value'}):
                        rec['supervisor'].append([re.sub('[\n\t\r]', ' ', div.text).strip()])
                #degree
                elif tht == 'Degree':
                    degree = re.sub('[\n\t\r]', ' ', td.text).strip()
                    if degree in boringdegrees:
                        keepit = False
                    else:
                        rec['note'].append(degree)
                #OA
                elif tht == 'Access Rights':
                    if re.search('open access', td.text):
                        oa = True
    for meta in artpage.find_all('meta'):
        if meta.has_attr('property'):
            #author
            if meta['property'] == 'citation_author':
                rec['auts'][-1] += ', CHINESENAME: ' + meta['content']
            #title
            elif meta['property'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['property'] == 'citation_date':
                rec['date'] = meta['content']
            #abstract
            elif meta['property'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['property'] == 'citation_pdf_url':
                if oa:
                    rec['FFT'] = meta['content']
            #handle
            elif meta['property'] == 'og:url':
                rec['link'] = meta['content']
                rec['hdl'] = re.sub('.*handle.net\/', '', meta['content'])
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)
    else:
        newuninterestingDOIS.append(rec['hdl'])

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

ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()

        
