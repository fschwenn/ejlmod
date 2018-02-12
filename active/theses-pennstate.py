# -*- coding: utf-8 -*-
#harvest PennSate University theses
#FS: 2018-02-12


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

publisher = 'Penn State University'

typecode = 'T'

jnlfilename = 'THESES-PENNSTATE-%s' % (stampoftoday)

tocurl = 'https://etda.libraries.psu.edu/catalog?f%5Bdegree_name_ssi%5D%5B%5D=PHD&f%5Bprogram_name_ssi%5D%5B%5D=Physics&per_page=100&sort=year_isi+desc%2C+title_ssi+asc'


try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

prerecs = []
for h3 in tocpage.body.find_all('h3', attrs = {'class' : 'document-title-heading'}):
    for a in h3.find_all('a'):
        rec = {'jnl' : 'BOOK', 'tc' : 'T', 'supervisor' : [], 'keyw' : []}
        rec['link'] = 'https://etda.libraries.psu.edu' + a['href']
        rec['doi'] = '20.2000/PENNSTATE/%s' % (re.sub('\W', '', a['href']))
        rec['tit'] = a.text.strip()
        prerecs.append(rec)

recs = []
i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(prerecs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    for li in artpage.body.find_all('li', attrs = {'class' : 'download'}):
        for a in li.find_all('a'):
            if not a['href'] == '/login':
                rec['FFT'] = 'https://etda.libraries.psu.edu' + a['href']
    for dd in artpage.body.find_all('dd', attrs = {'class' : 'blacklight-author_name_tesi'}):
        rec['auts'] = [ dd.text.strip() ]
        rec['aff'] = [ 'Penn State U.' ]
    for dd in artpage.body.find_all('dd', attrs = {'class' : 'blacklight-committee_member_and_role_tesim'}):
        for li in dd.find_all('li'):
            lit = li.text.strip()
            if re.search(', Dissertation Advisor', lit):
                rec['supervisor'].append([re.sub(', Dissertation Advisor.*', '', lit)])
    for dd in artpage.body.find_all('dd', attrs = {'class' : 'blacklight-keyword_ssim'}):
        for li in dd.find_all('li'):
            rec['keyw'].append(li.text.strip())
    for dd in artpage.body.find_all('dd', attrs = {'class' : 'blacklight-abstract_tesi'}):
        rec['abs'] = dd.text.strip()
    for dd in artpage.body.find_all('dd', attrs = {'class' : 'blacklight-defended_at_dtsi'}):
        rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', dd.text.strip())
        try:
            if int(rec['date']) > now.year - 2:
                recs.append(rec)
        except:
            if rec['link'] == 'https://etda.libraries.psu.edu/catalog/25268':
                rec['date'] = '2015'
            else:
                rec['date'] = str(now.year)
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
