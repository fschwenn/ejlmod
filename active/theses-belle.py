# -*- coding: utf-8 -*-
#harvest BELLE theses
#FS: 2018-01-31


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

publisher = 'BELLE'

typecode = 'T'

jnlfilename = 'THESES-BELLE-%s' % (stampoftoday)

recs = []

#server1
tocurl = 'http://belle.kek.jp/bdocs/theses.html'
#not valid html :(

#server2
tocurl = 'http://docs.belle2.org/search?ln=en&cc=PhD+Theses&p=&f=&action_search=Search&c=PhD+Theses&c=&sf=&so=d&rm=&rg=25&sc=1&of=xm'
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

for record in tocpage.find_all('record'):
    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'MARC' : []}
    for df in record.find_all('datafield', attrs = {'tag' : '037'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['MARC'].append(('037', [('a', sf.text)]))
    for df in record.find_all('datafield', attrs = {'tag' : '100'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['auts'] = [ sf.text ]
    for df in record.find_all('datafield', attrs = {'tag' : '245'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['tit'] = sf.text
    for df in record.find_all('datafield', attrs = {'tag' : '300'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['pages'] = sf.text
    for df in record.find_all('datafield', attrs = {'tag' : '520'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'a'}):
            rec['abs'] = sf.text
    for df in record.find_all('datafield', attrs = {'tag' : '856'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'u'}):
            rec['FFT'] = re.sub('\?.*', '', sf.text)
            rec['link'] = re.sub('\/files.*', '', sf.text)
            rec['doi'] = '20.2000/BELLE/' + re.sub('\W', '', rec['link'])
    for df in record.find_all('datafield', attrs = {'tag' : '260'}):
        for sf in df.find_all('subfield', attrs = {'code' : 'b'}):
            rec['aff'] = [ sf.text ]
        for sf in df.find_all('subfield', attrs = {'code' : 'c'}):
            rec['date'] = sf.text
            year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
            if year >= now.year - 1:
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
