# -*- coding: utf-8 -*-
#harvest theses from Warwick
#FS: 2020-08-10

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Warwick U.'

jnlfilename = 'THESES-WARWICK-%s' % (stampoftoday)
startyear = now.year-1

tocurl = 'http://wrap.warwick.ac.uk/view/theses/Department_of_Physics.html'
print tocurl
hdr = {'User-Agent' : 'Magic Browser'}
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
prerecs = []
ps = tocpage.body.find_all('p')
i = 0
for p in ps:
    i += 1
    for span in p.find_all('span', attrs = {'class' : 'person_name'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for a in p.find_all('a'):
            rec['link'] = a['href']
            rec['doi'] = '20.2000/WARWICK/' + re.sub('\W', '', re.sub('.*=', '', a['href']))
            rec['tit'] = a.text.strip()
            a.replace_with('')
        pt = re.sub('[\n\t\r]', ' ', p.text.strip())
        if re.search('\(\d\d\d\d\)', pt):
            rec['date'] = re.sub('.*\((\d\d\d\d)\).*', r'\1', pt)
            if rec['date'] >= str(startyear):
                prerecs.append(rec)
    print '%i/%i %s %i' % (i, len(ps), rec['date'], len(prerecs))

i = 0
recs = []
for rec in prerecs:
    i += 1
    time.sleep(3)
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    req = urllib2.Request(rec['link'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))

    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'eprints.creators_name':
                rec['autaff'] = [[ meta['content'] ]]
                rec['autaff'][-1].append(publisher)
            #keywords
            elif meta['name'] == 'eprints.keywords':
                for keyw in re.split(' *, *', meta['content']):
                    rec['keyw'].append(keyw)
            #FFT
            elif meta['name'] == 'eprints.document_url':
                rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.description':
                rec['abs'] = meta['content']
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
    for tr in artpage.body.find_all('tr'):
        for th in tr.find_all('th'):
            tht = th.text.strip()
            for td in tr.find_all('td'):
                #keywords
                if tht == 'Library of Congress Subject Headings (LCSH):':
                    rec['keyw'] = re.split(', ', re.sub(' \-\-', ', ', td.text.strip()))
                #pages
                elif tht == 'Extent':
                    if re.search('\d\d', td.text):
                        rec['pages'] = re.sub('.*(\d\d+).*', r'\1', td.text.strip())
                #supervisor
                elif tht == 'Supervisor(s)/Advisor:':
                    rec['supervisor'] = []
                    for sv in re.split('; ', td.text.strip()):
                        rec['supervisor'].append([re.sub(' \(.*', '', sv)])
    recs.append(rec)
    print ' ', rec.keys()

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
