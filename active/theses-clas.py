# -*- coding: utf-8 -*-
#harvest CLAS theses
#FS: 2018-01-29


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
from afftranslator2 import *
from invenio.search_engine import search_pattern

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'CLAS'

typecode = 'T'

jnlfilename = 'THESES-CLAS-%s' % (stampoftoday)

tocurl = 'https://www.jlab.org/Hall-B/general/clas_thesis.html'

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for table in tocpage.body.find_all('table', attrs = {'class' : 'sortable'}):
    isnew = True
    for tbody in table.find_all('tbody'):
        for tr in tbody.find_all('tr'):
            tds = tr.find_all('td')
            if len(tds) == 8:
                rec = {'jnl' : 'BOOK', 'tc' : typecode, 'supervisor' : []}
                rec['date'] = re.sub('(.*) (.*)', r'\2 \1', tds[2].text.strip())
                icn = bestmatch(tds[3].text.strip(), 'ICN')[0][1]
                for sv in re.split(' *[&,] ', tds[4].text.strip()):
                    rec['supervisor'].append([sv, icn ])
                rec['autaff'] = [ [ '%s, %s' % (tds[1].text.strip(), tds[0].text.strip()), tds[3].text.strip() ] ]
                rec['tit'] = tds[5].text.strip()
                for a in tds[5].find_all('a'):
                    rec['link'] = 'https://www.jlab.org/Hall-B/general/' + a['href']
                    rec['FFT'] = 'https://www.jlab.org/Hall-B/general/' + a['href']
                    rec['doi'] = '20.2000/CLAS/' + re.sub('\W', '', a['href'])
                rawexperiment = tds[7].text.strip()
                if re.search('^E(\d+)\-(\d+)', rawexperiment):
                    exp = re.sub('^E\d?(\d\d)\-(\d+)', r'JLAB-E-\1-\2', rawexperiment)
                    if search_pattern(p='980__a:EXPERIMENT 119__a:%s' % (exp)):
                        rec['exp'] = exp
                if re.search('20\d\d', rec['date']):
                    year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
                elif re.search('19\d\d', rec['date']):
                    year = int(re.sub('.*(19\d\d).*', r'\1', rec['date']))
                if year >= now.year - 1:
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
