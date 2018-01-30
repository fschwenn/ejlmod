# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest theses from NIKHEF
# FS 2018-02-26


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import datetime
import time 

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'NIKHEF'


jnlfilename = 'THESES-NIKHEF-%s' % (stampoftoday)

tocurl = 'https://www.nikhef.nl/pub/services/newbiblio/theses.php'

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for div in tocpage.body.find_all('div', attrs = {'id' : 'main'}):
    for child in div.children:
        try:
            child.name
        except:
            continue
        if child.name == 'dt':
            rec = {'tc' : 'T', 'auts' : [ child.text.strip() ], 'jnl' : 'BOOK'}
        elif child.name == 'dd':
            parts = re.split('\n', child.text.strip())
            for a in child.find_all('a'):
                rec['tit'] = a.text.strip()
                rec['link'] = a['href']
                rec['doi'] = '20.2000/' + re.sub('.*\/', '', rec['link']) + '_' + re.sub('\W', '', rec['auts'][0])
                if re.search('pdf$', rec['link']):
                    rec['FFT'] = a['href']
            #if rec['link'] == 'http://www.nikhef.nl/pub/services/biblio/theses_pdf/thesis_R_Aben.pdf':
            #    rec['date'] = '2015-06-17'
            #    recs.append(rec)
            #elif rec['link'] == 'http://www.nikhef.nl/pub/services/biblio/theses_pdf/thesis_C_Galea.pdf':
            #    rec['date'] = '2008-06-16'
            #    recs.append(rec)
            #elif rec['link'] == 'http://www.nikhef.nl/pub/services/biblio/theses_pdf/thesis_J_Uiterwijk.pdf':
            #    rec['date'] = '2007-06-12'
            #    recs.append(rec)
            if len(parts) > 1:
                rec['date'] = re.sub('Okt', 'Oct', re.sub('\.', '', parts[1].strip()))
                year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
                if year >= now.year - 1:
                    recs.append(rec)
            else:
                print rec

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
 
            
    
