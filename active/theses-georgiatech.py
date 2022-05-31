# -*- coding: utf-8 -*-
#harvest theses from Georgia Tech
#FS: 2022-04-18

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
import unicodedata
import ssl


xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Georgia Tech'
jnlfilename = 'THESES-GEORGIATECH-%s' % (stampoftoday)

rpp = 50
pages = 5

boring = ['Electrical and Computer Engineering', 'Civil and Environmental Engineering',
          'Aerospace Engineering', 'Biology', 'Chemical and Biomolecular Engineering',
          'City and Regional Planning', 'Computational Science and Engineering',
          'Industrial and Systems Engineering', 'Interactive Computing', 'Music',
          'Mechanical Engineering', 'Psychology', 'Public Policy', 'Architecture', 
          'Biomedical Engineering (Joint GT/Emory Department)', 'Chemistry and Biochemistry',
          'Economics', 'History, Technology and Society', 'International Affairs',
          'Building Construction', 'Business', 'Earth and Atmospheric Sciences',
          'Literature, Media, and Communication', 'Materials Science and Engineering',
          'Applied Physiology', 'Industrial Design', 'Biomedical Engineering',
          'Polymer, Textile and Fiber Engineering']

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
redoc = re.compile('rft.degree=Doctoral')
for page in range(pages):
    tocurl = 'https://smartech.gatech.edu/handle/1853/3739/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(rpp*(page+120)) + '&etal=-1&order=DESC'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    for td in tocpage.body.find_all('h4', attrs = {'class' : 'artifact-title'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'note' : [], 'keyw' : [], 'supervisor' : []}
        for span in td.find_all('span', attrs = {'class' : 'Z3988'}):
            if redoc.search(span['title']):
                for a in td.find_all('a'):
                    rec['artlink'] = 'https://smartech.gatech.edu' + a['href'] + '?show=full'
                    rec['link'] = 'https://smartech.gatech.edu' + a['href']
                    rec['hdl'] = re.sub('.*handle\/', '',  a['href'])
                    if not rec['hdl'] in uninterestingDOIS:
                        prerecs.append(rec)
    time.sleep(7)

i = 0
recs = []
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue


    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'].append([ meta['content'], publisher ])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            word = td.text.strip()
        #Department
        if label == 'dc.contributor.department':
            if word in boring:
                keepit = False
            else:
                rec['note'].append(word)
        #supervisor
        elif label == 'dc.contributor.advisor':
            rec['supervisor'].append([word])

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

