# -*- coding: utf-8 -*-
#harvest Kentucky University theses
#FS: 2018-01-30


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

publisher = 'Kentucky University'

typecode = 'T'

jnlfilename = 'THESES-KENTUCKY-%s' % (stampoftoday)

tocurl = 'https://uknowledge.uky.edu/physastron_etds/'

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
date = False
for div in tocpage.body.find_all('div', attrs = {'id' : 'series-home'}):
    for child in div.children:
        try:
            name = child.name
        except:
            continue
        if name == 'h4':
            for span in child.find_all('span'):
                date = span.text.strip()
        elif name == 'p':
            #year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
            if int(date) >= now.year - 1:
                if child.has_attr('class') and 'article-listing' in child['class']:
                    rec = {'jnl' : 'BOOK', 'tc' : 'T', 'date' : date}
                    for a in child.find_all('a'):                    
                        rec['tit'] = a.text.strip()
                        rec['artlink'] = a['href']
                        a.replace_with('')
                    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'description':
                rec['abs'] = meta['content']
            elif meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            elif meta['name'] == 'bepress_citation_dissertation_name':
                rec['note'] = [ meta['content'] ]
                if meta['content'] == "Doctor of Philosophy (PhD)":
                    rec['MARC'] = [('502', [('d', date), ('c', 'Kentucky U.'), ('b', 'PhD')])]                    
            elif meta['name'] == 'bepress_citation_author':
                rec['auts'] = [ meta['content'] ]
            elif meta['name'] == 'bepress_citation_author_institution':
                if meta['content'] == 'University of Kentucky':
                    rec['aff'] = ['University of Kentucky - Department of Physics and Astronomy, Lexington, KY 40506-0055, USA']
                else:
                    rec['aff'] = [ meta['content'] ]
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['FFT'] = meta['content']
            elif meta['name'] == 'bepress_citation_doi':
                rec['doi'] = re.sub('^ht.*?\/10', '10', meta['content'])
            elif meta['name'] == 'bepress_citation_online_date':
                rec['date'] = meta['content']
    for div in artpage.body.find_all('div', attrs = {'id' : 'advisor1'}):
        for p in div.find_all('p'):
            rec['supervisor'] = [[ re.sub('^Dr. ', '', p.text.strip()) ]]
    for div in artpage.body.find_all('div', attrs = {'id' : 'advisor2'}):
        for p in div.find_all('p'):
            rec['supervisor'].append( [re.sub('^Dr. ', '', p.text.strip())] )
    if not rec.has_key('doi'):
        rec['doi'] = '20.2000/KENTUCKY/' + re.sub('\W', '', re.sub('.*edu', '', rec['artlink']))
        rec['link'] = rec['artlink']

    
    
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
