# -*- coding: utf-8 -*-
#harvest theses from Alabama U.
#FS: 2021-09-15

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
rpp = 10
pages = 1

publisher = 'Alabama U.'

jnlfilename = 'THESES-ALABAMA-%s' % (stampoftoday)

recs = []
for page in range(pages):
    for dep in ['120', '126']:
        tocurl = 'https://ir.ua.edu/handle/123456789/' + dep + '/discover?rpp=' + str(rpp) + '&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
        print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
        try:
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
            time.sleep(3)
        except:
            print "retry %s in 180 seconds" % (tocurl)
            time.sleep(180)
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            for a in div.find_all('a'):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : []}
                    rec['tit'] = a.text.strip()
                    rec['link'] = 'https://ir.ua.edu' + a['href']
                    rec['doi'] = '30.3000/Alabama/' + re.sub('\W', '', a['href'])
                    if dep == '120':
                            rec['fc'] = 'm'
                    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.subject':
                rec['keyw'] += re.split('; ', meta['content'])
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
            elif meta['name'] == 'citation_date':
                if re.search('^\d\d\d\d\-\d\d\-\d\d', meta['content']): 
                    rec['date'] = meta['content']
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d p\.', meta['content']):
                    rec['pages'] = re.sub('\D', '', meta['content'])
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    print '  ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
