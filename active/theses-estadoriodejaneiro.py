# -*- coding: utf-8 -*-
#harvest theses from Rio de Janeiro State U.
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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Rio de Janeiro State U.'
jnlfilename = 'THESES-RioDeJaneiroStateU-%s' % (stampoftoday)

rpp = 20
pages = 1

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for (fc, depno) in [('', '3687'), ('m', '3696')]:
    for page in range(pages):
        tocurl = 'https://www.bdtd.uerj.br:8443/handle/1/' + depno + '/browse?type=dateissued&sort_by=2&order=DESC&rpp=' + str(rpp) + '&etal=-1&null=&offset=' + str(rpp*page) 
        print '==={ %s %i/%i }==={ %s }===' % (depno, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for tr in tocpage.body.find_all('tr'):
            for td in tr.find_all('td', attrs = {'headers' : 't3'}):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'note' : [], 'keyw' : []}
                if fc:
                    rec['fc'] = fc
                for a in td.find_all('a'):
                    rec['link'] = 'https://www.bdtd.uerj.br:8443' + a['href']
                    rec['doi'] = '20.2000/EstadoDeRioDeJaneiro/' + re.sub('.*handle\/', '',  a['href'])
                    prerecs.append(rec)
    time.sleep(7)

i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(prerecs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue

    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                if re.search('\d\d\d\d\-\d\d\d\d',  meta['content']):
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                elif re.search(' ', meta['content']):
                    author = meta['content']
                    rec['autaff'].append([ author ])
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'por':
                    rec['language'] = 'Portuguese'
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                if not re.search('::', meta['content']):
                    rec['keyw'].append(meta['content'])
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    if len(rec['autaff']) == 1:
        rec['autaff'][-1].append(publisher)
    recs.append(rec)
    print ' ', rec.keys()
    
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
