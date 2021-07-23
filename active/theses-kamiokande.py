# -*- coding: utf-8 -*-
#harvest KAMIOKANDE theses
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

publisher = 'KAMIOKANDE'

jnlfilename = 'THESES-KAMIOKANDE-%s' % (stampoftoday)

recs = []

#server1
tocurl = 'http://www-sk.icrr.u-tokyo.ac.jp/sk/publications/index-e.html'
print tocurl

hdr = {'User-Agent' : 'Magic Browser'}
try:
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

for p in tocpage.find_all('p'):
    pt = re.sub('[\n\t\r]', ' ', p.text.strip())
    if re.search('PhD', pt):
        rec = {'tc' : 'T', 'jnl' : 'BOOK'}
        for br in p.find_all('br'):
            br.replace_with(', ')
        for a in p.find_all('a'):
            if re.search('pdf$', a['href']):
                rec['link'] = 'http://www-sk.icrr.u-tokyo.ac.jp/sk' + a['href'][2:]
                rec['hidden'] = 'http://www-sk.icrr.u-tokyo.ac.jp/sk' + a['href'][2:]
                rec['doi'] = '20.2000/KAMIOKANDE/' + re.sub('\W', '', a['href'][16:-4])
            a.decompose()
        pt = re.sub('[\n\t\r]', ' ', p.text.strip())
        print pt
        halfs = re.split(' *,? *PhD Thesis *,? *', pt)
        firstparts = re.split(' *, *', halfs[0])
        secondparts = re.split(' *, *', halfs[1])
        print 'SP', secondparts
        if re.search('\d', secondparts[-1]):
            rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', secondparts[-1])
            rec['year'] = rec['date']
            rec['autaff'] = [[ firstparts[-1], ', '.join(secondparts[:-1]) ]]
        else:
            rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', secondparts[-2])
            rec['year'] = rec['date']
            rec['autaff'] = [[ firstparts[-1], ', '.join(secondparts[:-2]) ]]
        rec['tit'] = ', '.join(firstparts[:-1])
        if int(rec['year']) >= now.year - 2:
            recs.append(rec)
            print rec



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
