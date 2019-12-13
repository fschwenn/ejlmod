#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest ARMENIAN JOURNAL OF PHYSICS
# FS 2019-12-13

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import urllib2
import urlparse
from bs4 import BeautifulSoup
import time



ejdir = '/afs/desy.de/user/l/library/dok/ejl'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'National Academy of Sciences of Armenia'
jnl = 'armjp'
vol = sys.argv[1]
issue = sys.argv[2]
year = str(int(vol)+2007)

jnlfilename = '%s%s.%s' % (jnl, vol, issue)
jnlname = 'Armenian J.Phys.'
issn = "1829-1171"

urltrunk = 'http://www.flib.sci.am/eng/journal/Phys'
#urltrunk = 'http://ajp.asj-oa.am'
tocurl = '%s/PV%sIss%s.html' % (urltrunk, vol, issue)

hdr = {'User-Agent' : 'Magic Browser'}
print "get table of content of %s %s,  No. %s via %s ..." % (jnlname, vol, issue, tocurl)
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
time.sleep(1)
recs = []
for tr in tocpage.body.find_all('tr'):
    rec = {'auts' : [], 'year' : year, 'vol' : vol, 'keyw' : [],
           'issue' : issue, 'jnl' : jnlname, 'note' : [], 'tc' : "P"}
    for a in tr.find_all('a'):
        if a.has_attr('href'):
            rec['link'] = a['href']
            rec['doi'] = '20.2000/' + re.sub('\W', '', a['href'][7:])
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    time.sleep(3)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : re.sub('\/legalcode$', '', a['href'])}
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'eprints.creators_name':
                rec['auts'].append(meta['content'])
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DC.date':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'eprints.abstract':
                rec['abs'] = meta['content']
            #pages
            elif meta['name'] == 'eprints.pagerange':
                rec['p1'] = re.sub('\-.*', '', meta['content'])
                rec['p2'] = re.sub('.*\-', '', meta['content'])
            #subject
            elif meta['name'] == 'DC.subject':
                rec['note'].append(meta['content'])
            #PDF
            elif meta['name'] == 'eprints.document_url':
                if 'license' in rec.keys():
                    rec['FFT'] = meta['content']
    print ' ', rec.keys()                 

xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = open(xmlf,'w')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
