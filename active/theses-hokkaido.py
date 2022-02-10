# -*- coding: utf-8 -*-
#harvest theses from Hokkaido U.
#FS: 2021-12-17


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

publisher = 'Hokkaido U.'

rpp = 50
pages = 2

jnlfilename = 'THESES-HOKKAIDO-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for page in range(pages):
    tocurl = 'https://eprints.lib.hokudai.ac.jp/dspace/handle/2115/20136/browse?type=dateissued&sort_by=2&order=DESC&rpp=' + str(rpp) + '&etal=-1&null=&offset=' + str(page*rpp)
    print '==={ %i/%i }==={ %s }======' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(5)
    for td in tocpage.body.find_all('td', attrs = {'headers' : 't3'}):
        for a in td.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
            rec['link'] = 'https://eprints.lib.hokudai.ac.jp' + a['href']
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            recs.append(rec)


i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue
    keepit = True
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            elif meta['name'] == 'DCTERMS.alternative':
                rec['transtit'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split('; ', meta['content'])
    #DOI
    for strong in artpage.find_all('strong'):
        if re.search('Please.*doi', strong.text):
            rec['doi'] = re.sub('.*doi.org\/', '', strong.text.strip())
    rec['autaff'][-1].append(publisher)
    print '  ', rec.keys()
    
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
