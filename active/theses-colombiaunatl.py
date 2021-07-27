# -*- coding: utf-8 -*-
#harvest theses from Colombia, U. Natl.
#FS: 2020-11-03

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

publisher = 'Colombia, U. Natl.'

jnlfilename = 'THESES-ColombiaUNatl-%s' % (stampoftoday)
recs = []
hdr = {'User-Agent' : 'Magic Browser'}

tocurl = 'https://repositorio.unal.edu.co/handle/unal/42/browse?type=dateissued&sort_by=2&order=DESC&rpp=' + str(rpp)
print tocurl

recs = []
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
time.sleep(3)
for h4 in tocpage.body.find_all('h4', attrs = {'class' : 'artifact-title'}):
    for a in h4.find_all('a'):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'note' : [], 'refs' : [],
               'supervisor' : []}
        rec['link'] = 'https://repositorio.unal.edu.co' + a['href'] + '?show=full'
        rec['doi'] = '20.2000/ColumbiaUNatl/' + re.sub('\/handle\/', '', a['href'])
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
                rec['autaff'] = [[ meta['content'], publisher ]]
            #supervisor
            #elif meta['name'] == 'DC.contributor':
            #    if re.search('(ad|super)visor',  meta['content']):
            #        rec['supervisor'].append([ re.sub(' \(.*', '', meta['content']) ])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            elif meta['name'] == 'DCTERMS.alternative':
                rec['transtit'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                if meta.has_attr('scheme') and meta['scheme'] == 'DCTERMS.DDC':
                    rec['ddc'] = meta['content']
                else:
                    rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content'][:8]
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['fulltextlink'] = meta['content']
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                rec['pages'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'spa':
                    rec['language'] = 'spanish'
            #rights
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
    #detailed view
    tabelle = {}
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            if label in tabelle.keys():
                tabelle[label].append(td.text.strip())
            else:
                tabelle[label] = [ td.text.strip() ]
    #supervisor
    if 'dc.contributor.advisor' in tabelle.keys():
        for sv in tabelle['dc.contributor.advisor']:
            rec['supervisor'].append([sv])
    #references
    if 'dc.identifier.bibliographicCitation' in tabelle.keys():
        if len(tabelle['dc.identifier.bibliographicCitation']) > 10:
            for ref in tabelle['dc.identifier.bibliographicCitation']:
                rec['refs'].append([('x', ref)])
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
