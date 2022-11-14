# -*- coding: utf-8 -*-
#harvest theses from Salamanca U.
#FS: 2022-04-20

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

rpp = 10
years = 2

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Salamanca U.'

jnlfilename = 'THESES-SALAMANCA-%s' % (stampoftoday)
recs = []
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for (fc, dep) in [('m', '4145'), ('m', '4154'), ('', '4091'), ('', '4109')]:
    tocurl = 'https://gredos.usal.es/handle/10366/' + dep + '/browse?order=DESC&rpp=' + str(rpp) + '&sort_by=3&etal=-1&offset=' + str(0 * rpp) + '&type=dateissued'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(3)
    for li in tocpage.body.find_all('li', attrs = {'class' : 'ds-artifact-item'}):
        year = 666
        for span in li.find_all('span', attrs = {'class' : 'date'}):
            if re.search('[12]\d\d\d', span.text):
                year = int(re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip()))
        if year >=  now.year - years:
            for h4 in li.find_all('h4', attrs = {'class' : 'artifact-title'}):
                for a in h4.find_all('a'):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'note' : [], 'supervisor' : []}
                    rec['artlink'] = 'https://gredos.usal.es' + a['href']
                    rec['hdl'] = re.sub('.*\/handle\/', '', a['href'])
                    rec['tit'] = a.text.strip()
                    if fc:
                        rec['fc'] = fc
                    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(4)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #title
            if meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            elif meta['name'] == 'DCTERMS.alternative':
                rec['transtit'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                if not meta['content'] in [u'Tesis y disertaciones académicas', u'Universidad de Salamanca (España)',
                                           'Resumen de tesis', 'Thesis Abstracts']:
                    rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if 'abs' in rec.keys() and (re.search('^\[EN', rec['abs']) or re.search(' the ', rec['abs'])):
                    pass
                else:
                    rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['fulltextlink'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'por':
                    rec['language'] = 'Portuguese'
                elif meta['content'] == 'spa':
                    rec['language'] = 'Spanish'
            #rights
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
            #author
            elif meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #supervisor
            elif meta['name'] == 'DC.contributor':
                rec['supervisor'].append([meta['content']])
    #FFT
    if 'fulltextlink' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['fulltextlink']
        else:
            rec['hidden'] = rec['fulltextlink']
    print '   ', rec.keys()


#closing of files and printing
xmlf  = os.path.join(xmldir, jnlfilename+'.xml')
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
