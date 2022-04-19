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
import ssl


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
urltrunk = 'https://www.flib.sci.am/journal/arm/Phys'
tocurl = '%s/PV%sIss%s.html' % (urltrunk, vol, issue)
tocurl = '%s/%i_%s.html' % (urltrunk, int(vol)+2007, issue)



#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

hdr = {'User-Agent' : 'Magic Browser'}
print "get table of content of %s %s,  No. %s via %s ..." % (jnlname, vol, issue, tocurl)
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
time.sleep(1)
recs = []
for tr in tocpage.body.find_all('tr'):
    rec = {'auts' : [], 'year' : year, 'vol' : vol, 'keyw' : [],
           'issue' : issue, 'jnl' : jnlname, 'note' : [], 'tc' : "P"}
    for a in tr.find_all('a'):
        if a.has_attr('href'):
            rec['artlink'] = a['href']
            recs.append(rec)

if not recs:
    for a in tocpage.body.find_all('a'):
        if a.has_attr('href') and re.search('publication\/\d+', a['href']):
             rec = {'auts' : [], 'year' : year, 'vol' : vol, 'keyw' : [],
                    'issue' : issue, 'jnl' : jnlname, 'note' : [], 'tc' : "P"}
             rec['artlink'] = a['href']
             recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'])
    artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    time.sleep(3)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : re.sub('\/legalcode$', '', a['href'])}
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] in ['eprints.creators_name', 'DC.creator'] :
                rec['auts'].append(meta['content'])
            #title
            elif meta['name'] in ['eprints.title', 'DC.title']:
                rec['tit'] = meta['content']
            #date
            elif meta['name'] in ['DC.date', 'citation_online_date']:
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] in ['eprints.abstract', 'DC.description']:
                rec['abs'] = meta['content']
            #pages
            elif meta['name'] in ['eprints.pagerange', 'DC.coverage']:
                rec['p1'] = re.sub('\-.*', '', meta['content'])
                rec['p2'] = re.sub('.*\-', '', meta['content'])
            #subject
            elif meta['name'] == 'DC.subject':
                rec['note'].append(meta['content'])
            #PDF
            elif meta['name'] == ['eprints.document_url', 'citation_pdf_url']:
                if 'license' in rec.keys():
                    rec['FFT'] = meta['content']
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org', meta['content']):
                    rec['doi'] = re.sub('.*.org\/', '', meta['content'])
                elif re.search('pdf$', meta['content']):  
                    if 'license' in rec.keys():
                        rec['FFT'] = meta['content']
                    else:
                        rec['hidden'] = meta['content']
    #keywords
    for a in  artpage.body.find_all('a', attrs = {'class' : 'object__keyword'}):
        rec['keyw'].append(a.text.strip())
    if not 'doi' in rec.keys():
        rec['link'] = rec['artlink']
        rec['doi'] = '20.2000/ArmenianJPhysics/' + re.sub('\D', '', rec['artlink'])
    print ' ', rec.keys()

xmlf  = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile = open(xmlf,'w')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
