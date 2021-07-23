# -*- coding: utf-8 -*-
#harvest theses from HUB
#FS: 2019-09-13


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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Humboldt U., Berlin'

typecode = 'T'

jnlfilename = 'THESES-HUB-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
hdls = []
for ddc in ['530+Physik', '510+Mathematik', '539+Moderne+Physik']:
    tocurl = 'https://edoc.hu-berlin.de/handle/18452/2/discover?sort_by=dc.date.issued_dt&order=desc&rpp=50&filtertype_0=subjectDDC&filter_relational_operator_0=equals&filter_0=' + ddc 
    print tocurl
    driver = webdriver.PhantomJS()
    driver.implicitly_wait(120)
    driver.get(tocurl)
    tocpage = BeautifulSoup(driver.page_source)
    time.sleep(3)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'ds-artifact-item'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        rec['note'] = [ ddc ]
        for a in div.find_all('a'):
            rec['artlink'] = 'https://edoc.hu-berlin.de' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('.*handle\/(.*\d).*', r'\1', a['href'])
            if not rec['hdl'] in hdls:
                prerecs.append(rec)
                hdls.append(rec['hdl'])
    print len(prerecs)


recs = []
i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s}------' % (i, len(prerecs), rec['artlink'])
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
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('Humboldt U., Berlin')
            elif meta['name'] == 'DC.identifier':
                #DOI
                if re.search('doi.org', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
                elif re.search('urn:nbn', meta['content']):
                    rec['urn'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'ger':
                    rec['language'] = 'german'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['xml:lang'] == "eng":
                    rec['abs'] = meta['content']
            #license            
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
                    
    recs.append(rec)



	


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
