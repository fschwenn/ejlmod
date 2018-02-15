# -*- coding: utf-8 -*-
#harvest theses from Digital Commons Network
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

publisher = 'Digital Commons Network'

typecode = 'T'

jnlfilename = 'THESIS-DCN-%s' % (stampoftoday)

tocurl = 'http://network.bepress.com/explore/physical-sciences-and-mathematics/physics/elementary-particles-and-fields-and-string-theory/?facet=publication_type%3A%22Theses%2FDissertations%22&facet=publication_facet%3A%22Doctoral+Dissertations%22'

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'hide floatbox'}):
    for h4 in div.find_all('h4'):
        for small in h4.find_all('small'):
             rec = {'jnl' : 'BOOK', 'tc' : 'T'}
             rec['auts'] = [ re.sub('^ *, *', '', small.text.strip()) ]
             small.replace_with('')
             rec['tit'] = h4.text.strip()
    for p in div.find_all('p'):
        pt = p.text.strip()
        if len(pt) > 2:
            rec['abs'] = pt
    for a in div.find_all('a', attrs = {'title' : 'Opens in new window'}):
        rec['link'] = a['href']
        rec['doi'] = '20.2000/DCN/' + re.sub('\W', '', a['href'][4:])
    #date
    for small in div.previous_sibling.previous_sibling.previous_sibling.previous_sibling.find_all('small', attrs = {'class' : 'pull-right'}):
        rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', small.text.strip())
        if int(rec['date']) > now.year - 2:
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
