# -*- coding: utf-8 -*-
#harvest theses from Milan Bicocca U.
#FS: 2020-02-10


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

publisher = 'Milan Bicocca U.'

pages = 5

prerecs = []
jnlfilename = 'THESES-MILANBICOCCAU-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}
for page in range(pages):
    tocurl = 'https://boa.unimib.it/handle/10281/9145?offset=%i&sort_by=-1&order=DESC' % (20*page)
    print '---{ %i/%i }---{ %s }------' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(5)
    for tr in tocpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'headers' : 't1'}):
            for a in td.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
                rec['artlink'] = 'https://boa.unimib.it' + a['href']
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
        for td in tr.find_all('td', attrs = {'headers' : 't2'}):
            rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', td.text.strip())
            if int(rec['year']) >= now.year - 10:
                prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    interesting = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['link'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #email
            elif meta['name'] == 'citation_author_email':
                rec['autaff'][-1].append('EMAIL:' + meta['content'])
            #ORCID
            elif meta['name'] == 'citation_author_orcid':
                rec['autaff'][-1].append('ORCID:' + meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.description':
                if re.search(' (the|of|and) ', meta['content']):
                    rec['abs'] = meta['content']
            #thesis type
            elif meta['name'] == 'DC.type':
                rec['note'].append(meta['content'])
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'ita':
                    rec['language'] = 'italian'
            #department
            elif meta['name'] == 'citation_keywords':
                interesting = False
                if meta['content'][:3] in ['FIS', 'INF', 'ING', 'MAT']: 
                    rec['note'].append(meta['content'])
                    interesting = True
    rec['autaff'][-1].append(publisher)
    #license            
    for table in artpage.body.find_all('table', attrs = {'class' : 'ep_block'}):
        for a in table.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['licence'] = {'url' : a['href']}
    if interesting:
        recs.append(rec)

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
