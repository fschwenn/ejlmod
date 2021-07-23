# -*- coding: utf-8 -*-
#harvest University College London Theses
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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'University Coll. London'
hdr = {'User-Agent' : 'Magic Browser'}

pages = 5

recs = []
jnlfilename = 'THESES-UCLONDON-%s' % (stampoftoday)
for page in range(pages):
    #tocurl = 'https://discovery.ucl.ac.uk/cgi/search/archive/advanced?exp=0%7C1%7C-date%2Fcreators_name%2Ftitle%7Carchive%7C-%7Cdivisions%3Adivisions%3AANY%3AEQ%3AMI+MJ%7Ctype%3Atype%3AANY%3AEQ%3Athesis%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow&_action_search=1&order=-date%2Fcreators_name%2Ftitle&screen=Search&cache=40354498&search_offset=' + str(20*page)
    tocurl = 'https://discovery.ucl.ac.uk/cgi/search/archive/advanced?screen=Search&dataset=archive&documents_merge=ALL&documents=&title_merge=ALL&title=&creators_name_merge=ALL&creators_name=&editors_name_merge=ALL&editors_name=&abstract_merge=ALL&abstract=&divisions=C06&divisions_merge=ANY&date=&type=thesis&satisfyall=ALL&order=-date%2Fcreators_name%2Ftitle&_action_search=Search&search_offset=' + str(20*page)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(2)
    for tr in tocpage.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        for a in tr.find_all('a'):
            if a.has_attr('href') and re.search('discovery.ucl.ac.uk\/id\/\eprint', a['href']):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'link' : a['href'], 'note' : []}
                rec['tit'] = a.text.strip()
                rec['doi'] = '20.2000/UCLodon/' + re.sub('\D', '', a['href'])
                recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(10)
    except:
        try:
            print 'retry %s in 180 seconds' % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print 'no access to %s' % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'eprints.creators_name':
                rec['autaff'] = [[ meta['content'] ]]
            #ORCID
            elif meta['name'] == 'eprints.creators_orcid':
                rec['autaff'][-1].append(re.sub('.*(\d{4}\-\d{4}\-\d{4}\-\d{4}).*', r'ORCID:\1', meta['content']))
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'eprints.date':
                rec['date'] = meta['content']
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', meta['content'])
            #DOI
            elif meta['name'] == 'eprints.doi':
                rec['doi'] = meta['content']
            #number of pages
            elif meta['name'] == 'eprints.pages':
                rec['pages'] = meta['content']
            #PDF
            elif meta['name'] == 'eprints.document_url':
                rec['FFT'] = meta['content']
            #PDF
            elif meta['name'] == 'eprints.thesis_award':
                rec['note'].append(meta['content'])
    rec['autaff'][-1].append(publisher)
    print '  ', rec.keys()
                
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text: 
    retfiles = open(retfiles_path,'a')
    retfiles.write(line)
    retfiles.close()


