# -*- coding: utf-8 -*-
#harvest theses Regina U.
#FS: 2021-12-21

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
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Regina U.'
jnlfilename = 'THESES-REGINA-%s' % (stampoftoday)

rpp = 50
pages = 2

boringdeps = ['Biochemistry', 'Biology', 'Clinical Psychology', 'Education',
              'Engineering - Electronic Systems', 'Engineering - Environmental Systems',
              'Engineering - Petroleum Systems', 'Experimental and Applied Psychology',
              'Geology', 'History', 'Interdisciplinary Studies', 'Public Policy',
              'Chemistry', 'Engineering - Industrial Systems', 'Engineering - Process Systems',
              'Geography', 'Kinesiology and Health Studies', 'Canadian Plains Studies',
              'Engineering - Software Systems', 'Psychology', 'Kinesiology', 'Media Studies',
              'Police Studies', 'olitical Science', 'Social Work']

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'https://ourspace.uregina.ca/handle/10294/2900/discover?sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&page=' + str(page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    try:
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    except:
        print ' try again in 20s...'
        time.sleep(20)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
        for a in div.find_all('a'):
            rec['link'] = 'https://ourspace.uregina.ca' + a['href']
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)
    time.sleep(5)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'] + '?show=full', headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(4)
    except:
        try:
            print "   retry %s in 15 seconds" % (rec['link'])
            time.sleep(15)
            req = urllib2.Request(rec['link'] + '?show=full', headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        except:
            print "   no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        (label, word) = ('', '')
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}): 
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            word = td.text.strip()
        #supervisor
        if re.search('dc.contributor.advisor', label):
                rec['supervisor'].append([ word ])
        #department
        elif re.search('thesis.degree.discipline', label):
            if word in boringdeps:
                keepit = False
            else:
                rec['note'].append(word)

    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    if keepit:
        recs.append(rec)
        print '   ', rec.keys()

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
