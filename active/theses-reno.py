# -*- coding: utf-8 -*-
#harvest theses from University of Nevada, Reno 
#FS: 2019-09-25


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

publisher = 'Nevada U., Reno'

typecode = 'T'

jnlfilename = 'THESES-RENO-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
tocurl = 'https://scholarworks.unr.edu/handle/11714/105/discover?rpp=50&filtertype_0=type&filter_relational_operator_0=equals&filter_0=Thesis&filtertype=dateIssued&filter_relational_operator=equals&filter=[' + str(now.year-1) + '+TO+2040]&sort_by=dc.date.issued_dt&order=desc'
#tocurl = 'https://scholarworks.unr.edu/handle/11714/105/discover?rpp=500&filtertype_0=type&filter_relational_operator_0=equals&filter_0=Thesis&filtertype=dateIssued&filter_relational_operator=equals&filter=[' + str(now.year-5) + '+TO+2040]&sort_by=dc.date.issued_dt&order=desc'
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
    for a in div.find_all('a'):
        rec['artlink'] = 'https://scholarworks.unr.edu' + a['href'] #+ '?show=full'
        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
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
                rec['autaff'][-1].append('Nevada U., Reno')
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #supervisor
            elif meta['name'] == 'DC.contributor':
                supervisor = re.sub(' *\[.*', '', meta['content'])
                rec['supervisor'] = [[ supervisor ]]
                rec['supervisor'][-1].append('Nevada U., Reno')



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
