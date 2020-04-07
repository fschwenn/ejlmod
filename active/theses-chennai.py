# -*- coding: utf-8 -*-
#harvest theses from IMSc, Chennai
#FS: 2020-04-03

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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'IMSc, Chennai'
rpp = 20


hdr = {'User-Agent' : 'Magic Browser'}
recs = []
jnlfilename = 'THESES-CHENNAI-%s' % (stampoftoday)


years = [now.year, now.year-1]
for year in years:
    tocurl = 'https://www.imsc.res.in/xmlui/browse?type=datesubmitted&value=%i&rpp=100' % (year)
    print year, tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : []}
            rec['link'] = 'https://www.imsc.res.in' + a['href']
            rec['doi'] = '20.2000/IMScChennai/' + re.sub('.*\/', '', a['href'])
            if re.search('MSc', a.text):
                print '   skip Master', a.text.strip()
            else:
                recs.append(rec)

j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['link'])
    req = urllib2.Request(rec['link'])
    artpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    #author
    for meta in artpage.find_all('meta', attrs = {'name' : 'DC.creator'}):
        rec['autaff'] = [[ meta['content'], publisher ]]
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content'][:10]
                rec['year'] = meta['content'][:4]
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = re.sub('\[HBNI.*', '', meta['content'])
            #keywords
            elif meta['name'] == 'DC.subject':
                if not re.search('^HBNI', meta['content']):
                    rec['keyw'].append( meta['content'] )
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #pages
            elif meta['name'] == 'DC.description':
                if re.search('^\d+p\.',  meta['content']):
                    rec['pages'] = re.sub('\D.*', '', meta['content'])
    for div  in artpage.body.find_all('div', attrs = {'class' : 'simple-item-view-other'}):
        spans = div.find_all('span')
        if len(spans) == 2:
            if spans[0].text.strip() == 'Advisor:':
                rec['supervisor'] = [[ spans[1].text.strip() ]]
            elif spans[0].text.strip() == 'Degree:':
                degree = spans[1].text.strip()
                rec['note'].append(degree)                
            elif spans[0].text.strip() == 'Institution:':
                inst = spans[1].text.strip()
                if inst == 'HBNI': inst = 'HBNI, Mumbai'
            elif spans[0].text.strip() == 'Year:':
                rec['year'] = spans[1].text.strip()        
    if degree == 'Ph.D':
        rec['MARC'] = [ ('502', [('b', 'PhD'), ('c', inst), ('d', rec['year'])]) ]
    elif  degree == 'M.Sc':
        rec['MARC'] = [ ('502', [('b', 'Master'), ('c', inst), ('d', rec['year'])]) ]
    print '  ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
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
