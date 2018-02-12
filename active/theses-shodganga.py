# -*- coding: utf-8 -*-
#harvest theses from Shodghanga
#FS: 2018-02-05


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
startyear = now.year - 1

publisher = 'Shodhganga'

typecode = 'T'

jnlfilename = 'THESES-SHODHGANGA-%s' % (stampoftoday)

tocurl = 'http://shodhganga.inflibnet.ac.in:8080/jspui/handle/10603/1523/simple-search?location=10603%2F1523&query=&filter_field_1=language&filter_type_1=equals&filter_value_1=English&rpp=500&sort_by=score&order=DESC&etal=0&submit_search=Update'

recs = []
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))


recs = []
for tr in tocpage.body.find_all('tr'):
    for td in tr.find_all('td', attrs = {'headers' : 't1'}):        
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : [], 'keyw' : [], 'aff' : []}
        rec['date'] = re.sub('\-', ' ', td.text.strip())
        for td2 in tr.find_all('td', attrs = {'headers' : 't2'}):   
            rec['tit'] = td2.text.strip()
            for a in td2.find_all('a'):                
                rec['link'] = 'http://shodhganga.inflibnet.ac.in:8080' + a['href']
                rec['hdl'] = re.sub('.*handle\/', '',  a['href'])
        for td2 in tr.find_all('td', attrs = {'headers' : 't3'}):   
            rec['auts'] = [ td2.text.strip() ]
        for td2 in tr.find_all('td', attrs = {'headers' : 't4'}):   
            rec['supervisor'].append( [ td2.text.strip() ])
        year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
        if year >= now.year - 1:
            recs.append(rec)



i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    aff = []
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DCTERMS.abstract':
                abs = meta['content']
                if len(abs) > 10:
                    rec['abs'] = abs.strip()
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'DC.type':
                rec['note'] = [ meta['content'] ]
            elif meta['name'] == 'DC.publisher':
                aff.append(meta['content'])
    if aff:
        rec['aff'] = [', '.join(aff)]
    
    
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
