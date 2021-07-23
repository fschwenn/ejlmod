# -*- coding: utf-8 -*-
#harvest theses Northern Illinois U.
#FS: 2020-12-23

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

publisher = 'NIU, DeKalb'
jnlfilename = 'THESES-NorthernIllinois-%s' % (stampoftoday)

rpp = 50
pages = 2

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for page in range(pages):
    tocurl = 'https://commons.lib.niu.edu/handle/10843/8763/browse?order=DESC&rpp=' + str(rpp) + '&sort_by=3&etal=-1&offset=' + str(page*rpp) + '&type=dateissued'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    divs = tocpage.body.find_all('h4', attrs = {'class' : 'artifact-title'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for a in div.find_all('a'):
            rec['link'] = 'https://commons.lib.niu.edu' + a['href'] #+ '?show=full'
            rec['doi'] = '20.2000/NorthernIllinois/' + re.sub('.*handle\/', '', a['href'])
            recs.append(rec)
    print '  %i records do far' % (len(recs))
    time.sleep(10)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(3)
    except:
        try:
            print "   retry %s in 15 seconds" % (rec['link'])
            time.sleep(15)
            req = urllib2.Request(rec['link'], headers=hdr)
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
            elif meta['name'] == 'DCTERMS.issued':
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
    if not 'date' in rec.keys():
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'DCTERMS.dateAccepted'}):
            rec['date'] = meta['content']
            rec['note'].append('date from DCTERMS.dateAccepted')
    rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'pdf_url' in rec.keys():
                rec['FFT'] = rec['pdf_url']
    #upload PDF at least hidden
    if not 'FFT' in rec.keys() and 'pdf_url' in rec.keys():
        rec['hidden'] = rec['pdf_url']

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
