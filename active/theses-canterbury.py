# -*- coding: utf-8 -*-
#harvest theses from Canterbury U.
#FS: 2020-09-11


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Canterbury U.'

rpp = 20
pages = 1

hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-CANTERBURY-%s' % (stampoftoday)


prerecs = []
for page in range(pages):
    tocurl = 'https://ir.canterbury.ac.nz/handle/10092/841/discover?filtertype_1=discipline&filter_relational_operator_1=contains&filter_1=physics&submit_apply_filter=&rpp=' + str(rpp) + '&sort_by=dc.date.issued_dt&order=desc&page=' + str(page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for a in div.find_all('a'):
            for h4 in a.find_all('h4'):
                rec['artlink'] = 'https://ir.canterbury.ac.nz' + a['href']# + '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                prerecs.append(rec)

    recs = []

i = 0
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['link'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *[;,] +', meta['content']):
                    rec['keyw'].append(keyw)
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('dx.doi.org',  meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            #Rights
            elif meta['name'] == 'DC.rights':
                rec['note'].append(meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
    for div in artpage.body.find_all('div', attrs = {'class' : 'simple-item-view-other'}):
        for h5 in div.find_all('h5'):
            #Degree
            if re.search('Degree', h5.text):
                for span in div.find_all('span'):
                    rec['degree'] = span.text.strip()
                    if re.search('Master', rec['degree']):
                        keepit = False
                        print '   skip "%s"' % (rec['degree'])
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)


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
        
