# -*- coding: utf-8 -*-
#harvest theses from Queen Mary, U. of London (main)
#FS: 2020-09-02

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
startyear = now.year - 1
stopyear = now.year + 1
rpp = 50
pages = 20
numberofrecords = rpp*pages

publisher = 'Queen Mary, U. of London (main)'

jnlfilename = 'THESES-QUEEN_MARY-%s' % (stampoftoday)
boring = ['Engineering and Materials Science', #'Electronic Engineering and Computer Science', 
          'Biological and Chemical Sciences', 'Law', 'Medicine', 'Electronic Engineering',
          #'School of Electronic Engineering and Computer Science',
          'Medicine and Dentistry', 'Engineering and Material Science',
          'School of Medicine and Dentistry', 'School of Law',
          'School of Biological and Chemical Sciences',
          'Cancer', #'Computer Science',
          'Electronic engineering and computer science',
          'Dentistry',
          'Barts and the London School of Medicine and Dentistry',
          'Geography', 'History', 'C4DM', 'Business and Management']
prerecs = []


inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

realpages = pages
for page in range(pages):
    if len(prerecs) < numberofrecords:
        tocurl = 'https://qmro.qmul.ac.uk/xmlui/handle/123456789/56376/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&filtertype_0=dateIssued&filtertype_1=type&filter_relational_operator_1=equals&filter_relational_operator_0=equals&filter_1=Thesis&filter_0=%5B' + str(startyear) + '+TO+' + str(stopyear) + '%5D'
        print '==={ %i/%i }==={ %s }===' % (page+1, realpages, tocurl)
        try:
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
            time.sleep(3)
        except:
            print "retry %s in 180 seconds" % (tocurl)
            time.sleep(180)
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
        if page == 0:
            for p in tocpage.body.find_all('p', attrs = {'class' : 'pagination-info'}):
                if re.search('\d of \d+', p.text):
                    numberofrecords = int(re.sub('.*of (\d+).*', r'\1', p.text.strip()))
                    print '  %i theses in query' % (numberofrecords)
                    realpages = (numberofrecords-1) / rpp + 1
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            for a in div.find_all('a'):
                for h4 in a.find_all('h4'):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'keyw' : []}
                    rec['tit'] = a.text.strip()
                    rec['link'] = 'https://qmro.qmul.ac.uk' + a['href']
                    rec['doi'] = '20.2000/QueenMary/' + re.sub('\W', '', a['href'])
                    if not rec['doi'] in uninterestingDOIS:
                        prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] in ['citation_author', 'DC.creator']:
                if not re.search('Queen Mary', meta['content']):
                    rec['autaff'] = [[ meta['content'], publisher ]]
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'DC.contributor':
                rec['supervisor'].append([meta['content']])
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            elif meta['name'] == 'DC.identifier':
                if re.search('^10\.\d+\/', meta['content']):
                    rec['doi'] = meta['content']
            elif meta['name'] == 'citation_date':
                if re.search('^\d\d\d\d\-\d\d\-\d\d', meta['content']): 
                    rec['date'] = meta['content']
    keepit = True
    for kw in rec['keyw']:
        if kw in boring:
            print '  skip', kw
            keepit = False
    if keepit:
        recs.append(rec)
    else:
        newuninterestingDOIS.append(rec['doi'])

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

ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()
