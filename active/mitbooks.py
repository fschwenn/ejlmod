# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest MIT Books
# FS 2022-06-02

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
import time
import datetime
from bs4 import BeautifulSoup
import json


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

publisher = 'MIT Press'
urltrunc = 'https://mitp-web.mit.edu/topics'

serieses = [('physical-sciences/astronomy', 'a', 1), ('physical-sciences', '', 2),
            ('computer-science', 'c', 3), ('mathematics-statistics', 'm', 2)]
years = 2
now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

#scan serieses
linksdone = []
recs = []
for (series, fc, pages) in serieses:
    for page in range(pages):
        toclink = '%s/%s?page=%i' % (urltrunc, series, page)
        print '---{ %s %i/%i }---{ %s }---' % (series, page+1, pages, toclink)
        tocreq = urllib2.Request(toclink, headers={'User-Agent' : "Magic Browser"}) 
        toc = BeautifulSoup(urllib2.urlopen(tocreq), features="lxml")
        for li in toc.body.find_all('li', attrs = {'class' : 'results__default'}):
            for timetag in li.find_all('time'):
                year = int(re.sub('.*([12]\d\d\d).*', r'\1', timetag.text.strip()))
            if year > now.year-years and now.year >= year:
                for h3 in li.find_all('h3'):
                    for a in h3.find_all('a'):
                        rec = {'tit' : a.text.strip(), 'link' : a['href'], 'note' : [ series ],
                               'tc' : 'B', 'jnl' : 'BOOK', 'auts' : [], 'date' : str(year)}
                        if fc: rec['fc'] = fc
                    if not a['href'] in linksdone:
                        recs.append(rec)
                        linksdone.append(a['href'])
                        print ' ', rec['tit']
        time.sleep(10)

#scan individual book pages
i = 0
for rec in recs:        
        i += 1
        print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['link'])
        artreq = urllib2.Request(rec['link'], headers={'User-Agent' : "Magic Browser"}) 
        art = BeautifulSoup(urllib2.urlopen(artreq), features="lxml")
        #abstract and ISBN
        for meta in art.head.find_all('meta'):
            if meta.has_attr('property'):
                if meta['property'] == 'og:title':
                    rec['tit'] = meta['content']

            elif meta.has_attr('name'):
                #abstract
                if meta['name'] == 'dcterms.description':
                    rec['abs'] = meta['content']
        #authors
        for span in art.body.find_all('span', attrs = {'class' : 'book__authors'}):
            for a in span.find_all('a'):
                rec['auts'].append(a.text)
        #ISBN
        for span in art.body.find_all('span', attrs = {'property' : 'isbn'}):
            rec['isbn'] = span.text
        #pages
        for span in art.body.find_all('span', attrs = {'property' : 'numpages'}):
            rec['pages'] = span.text
        print '  ', rec.keys()
        time.sleep(4)
            

        
jnlfilename = 'MITBooks_%s_%s' % (re.sub('\W', '', series), stampoftoday)

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

        
        
