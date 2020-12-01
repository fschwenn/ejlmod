# -*- coding: utf-8 -*-
#harvest theses from Warsaw U.
#FS: 2020-11-29

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

rpp = 20

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Warsaw U. (main)'

recs = []
hdr = {'User-Agent' : 'Magic Browser'}

deps = [('29', 'Warsaw U., Inst. Math. Mech.', 'math'), ('5', 'Warsaw U.', 'phys')]

for (depnr, aff, subject) in deps:
    jnlfilename = 'THESES-WARSAW-%s_%s' % (stampoftoday, subject)
    tocurl = 'https://depotuw.ceon.pl/handle/item/' + depnr + '/discover?sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp)
    print tocurl
    recs = []
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'note' : [], 'supervisor' : []}
            rec['link'] = 'https://depotuw.ceon.pl' + a['href'] + '?show=full'
            rec['doi'] = '20.2000/Warsaw/' + re.sub('\/handle\/', '', a['href'])
            rec['tit'] = a.text.strip()
            recs.append(rec)

    i = 0
    for rec in recs:
        i += 1
        print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            time.sleep(4)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            except:
                print "no access to %s" % (rec['link'])
                continue
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                #author
                if meta['name'] == 'DC.creator':
                    rec['autaff'] = [[ meta['content'], aff ]]
                #supervisor
                elif meta['name'] == 'DC.contributor':
                    rec['supervisor'] = [[ meta['content'] ]]
                #title
                elif meta['name'] == 'DC.title':
                    rec['tit'] = meta['content']
                elif meta['name'] == 'DCTERMS.alternative':
                    rec['transtit'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    if meta.has_attr('scheme'):
                        rec['ddc'] = meta['content']
                    else:
                        rec['keyw'].append(meta['content'])
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    if re.search(' the ', meta['content']):
                        rec['abs'] = meta['content']
                    else:
                        rec['abspl'] = meta['content']
                #date
                elif meta['name'] == 'DC.date':
                    rec['date'] = meta['content'][:8]
                #fulltext
                elif meta['name'] == 'citation_pdf_url':
                    rec['fulltextlink'] = meta['content']
                #pages
                elif meta['name'] == 'DCTERMS.extent':
                    rec['pages'] = meta['content']
                #language
                elif meta['name'] == 'DC.language':
                    if meta['content'] == 'pl':
                        rec['language'] = 'polish'
                #rights
                elif meta['name'] == 'DC.rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['license'] = {'url' : meta['content']}
        if 'abspl' in rec.keys() and not 'abs' in rec.keys():
            rec['abs'] = rec['abspl']
        if 'fulltextlink' in rec.keys():
            if 'license' in rec.keys():
                rec['FFT'] = rec['fulltextlink']
            else:
                rec['hidden'] = rec['fulltextlink']
        print '   ', rec.keys()

    #closing of files and printing
    xmlf  = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writeXML(recs, xmlfile, publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
