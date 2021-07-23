# -*- coding: utf-8 -*-
#harvest theses from University of Bern
#FS: 2019-09-27


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

publisher = 'Bern U.'

typecode = 'T'

jnlfilename = 'THESES-BERN-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
tocurl = 'https://boris.unibe.ch/cgi/search/advanced?screen=Search&_action_search=Search&eprintid=&date=&title_merge=ALL&title=&contributors_name_merge=ALL&contributors_name=&contributors_orcid=&editors_name_merge=ALL&editors_name=&publication_merge=ALL&publication=&abbrev_publication_merge=ALL&abbrev_publication=&publisher_merge=ALL&publisher=&event_title_merge=ALL&event_title=&event_location_merge=ALL&event_location=&issn=&isbn=&book_title_merge=ALL&book_title=&abstract_merge=ALL&abstract=&keywords_merge=ALL&keywords=&note_merge=ALL&note=&divisions=DCD5A442C024E17DE0405C82790C4DE2&divisions=DCD5A442C44AE17DE0405C82790C4DE2&divisions=DCD5A442BE78E17DE0405C82790C4DE2&divisions=DCD5A442C6C6E17DE0405C82790C4DE2&divisions_merge=ANY&grad_school_merge=ANY&type=thesis&refereed=EITHER&doc_content_merge=ANY&doc_license_merge=ANY&doc_format_merge=ANY&doi_name=&id_fs=&doi=&pubmed_id=&wos_id=&satisfyall=ALL&order=-date%2Fcreators_name%2Ftitle'
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'ep_search_results'}):
    for a in div.find_all('a'):
        if re.search('^http', a['href']):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
            rec['artlink'] = a['href']
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i}---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('Bern U.')
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DC.date':
                rec['date'] = meta['content']
            #DOI
            elif meta['name'] == 'eprints.doi_name':
                rec['doi'] = meta['content']
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #pages
            elif meta['name'] == 'eprints.pages':
                rec['pages'] = meta['content']
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['FFT'] = meta['content']
            #supervisor
            elif meta['name'] == 'DC.contributor':
                supervisor = re.sub(' *\[.*', '', meta['content'])
                rec['supervisor'] = [[ supervisor ]]
                rec['supervisor'][-1].append('Bern U.')
    #license
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            atext = a.text.strip()
            if re.search('\(CC.[A-Z][A-Z]', atext):
                rec['license'] = {'statement' : re.sub('.*\((CC.*?)\).*', r'\1', atext)}
            



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
