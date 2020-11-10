# -*- coding: utf-8 -*-
#harvest theses from Bohr Institute
#FS: 2020-11-09

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Bohr Inst.'
startyear = now.year - 1

jnlfilename = 'THESES-BOHR-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
tocurl = 'https://www.nbi.ku.dk/english/theses/phd-theses/'
print '==={ %s }===' % (tocurl)
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
time.sleep(2)
for article in tocpage.find_all('article', attrs = {'class' : 'tilebox'}):
    print article
    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
    for h2 in article.find_all('h2'):
        rec['autaff'] = [[ h2.text.strip(), publisher ]]
    for a in article.find_all('a'):
        rec['link'] = 'https://www.nbi.ku.dk' + a['href']
        rec['doi'] = '20.2000/NielsBohrInst/' + re.sub('\W', '', a['href'][26:])
    for div in article.find_all('div', attrs = {'class' : 'date'}):
        rec['date'] = re.sub('\.', '-', div.text.strip())
        rec['year'] = rec['date'][:4]
        if int(rec['year']) >= startyear:
            recs.append(rec)

j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'])
        artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(2)
    except:
        print 'wait 10 minutes'
        time.sleep(600)
        try:
            req = urllib2.Request(rec['link'])
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
            time.sleep(30)
        except:
            continue
    for p in artpage.find_all('p'):
        for strong in p.find_all('strong'):
            st = strong.text.strip()
            strong.decompose()
            #title and PDF
            if re.search('[pP]\.?h\.? *[dD]', st):
                for a in p.find_all('a'):
                    at = a.text.strip()
                    if len(at) > 5:
                        rec['hidden'] = 'https://www.nbi.ku.dk' + a['href']
                        rec['tit'] = at
                if not 'tit' in rec.keys():
                    rec['tit'] = p.text.strip()
            #supervisor
            elif st in ['Supervisor:', 'Primary Supervisor:']:
                rec['supervisor'] = [[ re.sub('[Pp]rof\. *', '', re.sub('Dr\. *', '', p.text.strip())) ]]
    print '  ', rec.keys()
    if not 'tit' in rec.keys():
        for meta in artpage.find_all('meta', attrs = {'name' : 'DC.Description'}):
            rec['tit'] = meta['content']

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
