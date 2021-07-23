# -*- coding: utf-8 -*-
#harvest theses from Frankfurt
#FS: 2019-09-15


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

publisher = 'Goethe U., Frankfurt (main)'

typecode = 'T'

jnlfilename = 'THESES-FRANKFURT-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for page in ['0', '10', '20']:
    tocurl = 'http://publikationen.ub.uni-frankfurt.de/solrsearch/index/search/searchtype/simple/query/%2A%3A%2A/browsing/true/doctypefq/doctoralthesis/start/' + page + '/rows/10/institutefq/Physik/sortfield/year/sortorder/desc'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
    for dt in tocpage.body.find_all('dt', attrs = {'class' : 'results_title'}):
        for a in dt.find_all('a'):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
            rec['artlink'] = 'http://publikationen.ub.uni-frankfurt.de' + a['href']
            rec['tit'] = a.text.strip()
            recs.append(rec)


i = 0
for rec in recs:
    i += 1
    time.sleep(3)
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
                rec['autaff'][-1].append('Goethe U., Frankfurt (main)')
            #abstract
            elif meta['name'] == 'DC.Description':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #URN & link
            elif meta['name'] == 'DC.Identifier':
                if re.search('^urn:', meta['content']):
                    rec['urn'] = meta['content']
                elif re.search('http.*docId', meta['content']):
                    rec['link'] = meta['content']
    for tr in artpage.body.find_all('tr'):
        for td in tr.find_all('td'):
            tdt = td.text.strip()
        for th in tr.find_all('th'):
            tht = th.text.strip()
            if tht == 'Advisor:':
                rec['supervisor'] = [[ tdt, 'Goethe U., Frankfurt (main)' ]]
            elif tht == 'Language:':
                if tdt == 'German':
                    rec['language'] = 'german'
            elif tht == 'Release Date:':
                rec['date'] = tdt
            elif tht == 'Pagenumber:':
                rec['pages'] = re.sub('\D*(\d+).*', r'\1', tdt)







	


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
