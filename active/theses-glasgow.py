# -*- coding: utf-8 -*-
#harvest theses from University of Glasgow
#FS: 2020-02-14


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

publisher = 'Glasgow U.'

pages = 4

jnlfilename = 'THESES-GLASGOW-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = 'http://theses.gla.ac.uk/cgi/search/archive/advanced?exp=0%7C1%7C-date%2Fcreators_name%2Ftitle%7Carchive%7C-%7Csubjects%3Asubjects%3AANY%3AEQ%3AQ1+QA+QB+QC%7C-%7Ceprint_status%3Aeprint_status%3AANY%3AEQ%3Aarchive%7Cmetadata_visibility%3Ametadata_visibility%3AANY%3AEQ%3Ashow&_action_search=1&order=-date%2Fcreators_name%2Ftitle&screen=Search&cache=500363&search_offset=' + str(20*page)
    print '---{ %i/%i }---{ %s }---' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr', attrs = {'class' : 'ep_search_result'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
        for a in tr.find_all('a'):
            if a.has_attr('href') and re.search('theses.gla.ac.uk\/\d+.?', a['href']):
                rec['link'] = a['href']
                rec['doi'] = '20.2000/' + re.sub('\W', '', a['href'])
                rec['tit'] = a.text.strip()
                prerecs.append(rec)
    time.sleep(5)

                
i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
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
            if meta['name'] == 'eprints.creators_name':
                rec['autaff'] = [[ meta['content'] ]]
            #email
            elif meta['name'] == 'eprints.creators_id':
                if re.search('@', meta['content']):
                    rec['autaff'][-1].append('EMAIL:' + meta['content'])
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'eprints.date':
                rec['date'] = meta['content']                
            #keywords
            elif meta['name'] == 'DC.subject':
                 rec['keyw'] = re.split(', ', meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['FFT'] = meta['content']
            #thesis type
            elif meta['name'] == 'eprints.thesis_type':
                rec['note'].append( meta['content'] )
            #supervisor
            elif meta['name'] == 'eprints.supervisor_name':
                rec['supervisor'].append([ meta['content'] ])
            elif meta['name'] == 'eprints.supervisor_id':
                if re.search('@', meta['content']):
                    rec['supervisor'][-1].append(meta['content'])
    if not "MSc(R)" in rec['note']:
        if not "MD" in rec['note']:
            if not "MPhil(R)" in rec['note']:
                if not "MVM(R)" in rec['note']:
                    recs.append(rec)
                    print '  ', rec.keys()



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
