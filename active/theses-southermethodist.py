# -*- coding: utf-8 -*-
#harvest theses from Southern Methodist U.
#FS: 2020-04-28


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
pagestocheck = 2

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Southern Methodist U. (main)'
jnlfilename = 'THESES-SOUTHERNMETHODIST-%s' % (stampoftoday)

tocurl = 'https://scholar.smu.edu/hum_sci_physics_etds/'
hdr = {'User-Agent' : 'Magic Browser'}
recs = []

req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
for div in tocpage.body.find_all('div', attrs = {'id' : 'series-home'}):
    for child in div.children:
        try:
            child.name
        except:
            continue
        if child.name == 'h4':
            for span in child.find_all('span'):
                year = re.sub('.*(20\d\d).*', r'\1', span.text.strip())
            print year
        elif child.name == 'p' and child.has_attr('class') and 'article-listing' in child['class']:
            if int(year) > now.year - 2:
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'year' : year}
                for a in child.find_all('a'):
                    rec['link'] = a['href']
                    rec['doi'] = '20.2000/SoutherMethodist/' + re.sub('\W', '', a['href'][23:])
                    recs.append(rec)

#check individual thesis pages
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
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
            if meta['name'] == 'bepress_citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #abstract
            elif meta['name'] == 'description':
                rec['abs'] = meta['content']
            #title
            elif meta['name'] == 'twitter:title':
                rec['tit'] = meta['content']
            #fulltext
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['fulltext'] = meta['content']
    for div in artpage.body.find_all('div', attrs = {'class' : 'element'}):
        if div.has_attr('id'):
            #date
            if div['id'] == 'publication_date':
                for p in div.find_all('p'):
                    if re.search('\d+\-\d+\-\d+', p.text):
                        rec['date'] = re.sub('.*?(\d+)\-(\d+)\-(\d+).*', r'\3-\2-\1', p.text.strip())
            #supervisor
            elif div['id'] == 'advisor1':
                for p in div.find_all('p'):
                    rec['supervisor'] = [[ p.text.strip() ]]
            #pages
            elif div['id'] == 'number_of_pages':
                for p in div.find_all('p'):
                    rec['pages'] = p.text.strip()
    #license
    for link in artpage.find_all('link', attrs = {'rel' : 'license'}):
        rec['license'] = {'url' : link['href']}
    #FFT
    if 'fulltext' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['fulltext']
        else:
            rec['hidden'] = rec['fulltext']                
    print '    ', rec.keys()
    print rec
    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()


