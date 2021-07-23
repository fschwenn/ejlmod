# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Comptes Rendus by the French academy of sciences
# FS 2020-10-20

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special/'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

def tfstrip(x): return x.strip()

publisher = 'Academie des sciences'

jnl = sys.argv[1]
vol = sys.argv[2]
iss = sys.argv[3]

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'cr%s%s.%s_%s' % (jnl, vol, iss, stampoftoday)

#journals have quite different number of articles per month
if jnl == 'mathematique':
    year = str(1662 + int(vol))
    tocurl = 'https://comptes-rendus.academie-sciences.fr/mathematique/issues/CRMATH_%s__%s_%s/' % (year, vol, iss)
    jnlname = 'Compt.Rend.Math.'
elif jnl == 'physique':
    year = str(1999 + int(vol))
    tocurl = 'https://comptes-rendus.academie-sciences.fr/physique/issues/CRPHYS_%s__%s_%s/' % (year, vol, iss)
    jnlname = 'Comptes Rendus Physique'

hdr = {'User-Agent' : 'Mozilla/5.0'}
print tocurl
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
for span in tocpage.body.find_all('span', attrs = {'class' : 'article-title'}):
    for a in span.find_all('a'):
        rec = {'jnl' : jnlname, 'tc' : 'P', 'keyw' : [], 'autaff' : [],
               'year' : year, 'vol' : vol, 'issue' : iss, 'refs' : []}
        rec['artlink'] = 'https://comptes-rendus.academie-sciences.fr' + a['href']
        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    time.sleep(3)
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #DOI
            if meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #pages
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    #abstract
    for div in artpage.body.find_all('div', attrs = {'id' : 'abstract-en'}):
        for p in div.find_all('p'):
            rec['abs'] = p.text.strip()
    #authors
    for div in artpage.body.find_all('div', attrs = {'class' : 'article-author'}):
        for a in div.find_all('a'):
            if re.search('orcid.org', a['href']):
                rec['autaff'][-1].append(re.sub('.*\/', 'ORCID:', a['href']))
            else:
                rec['autaff'].append([a.text.strip()])
    #date
    for div in artpage.body.find_all('div', attrs = {'id' : 'info-tab'}):
        divt = re.sub('[\n\t\r]', ' ', div.text.strip())
        if re.search('Published online: ', divt):
            rec['date'] = re.sub('.*Published online: ([\d\-]+).*', r'\1', divt)
    #references
    for div in artpage.body.find_all('div', attrs = {'id' : 'reference-tab'}):
        for p in div.find_all('p', attrs = {'class' : 'bibitemcls'}):
            for a in p.find_all('a'):
                if a.has_attr('href') and re.search('doi.org', a['href']):
                    rdoi = re.sub('.*doi.org\/', r', DOI: ', a['href'])
                    a.replace_with(rdoi)

            pt = p.text.strip()
            pt = re.sub(', Volume ', ' ', pt)
            #replace ';' in names by ','
            numbers = False
            parts = re.split(';', pt)
            ptnew = parts[0]
            if re.search('\d', re.sub('^[\[\]\d]+', '', ptnew)):
                numbers = True
            for part in parts[1:]:
                if numbers:
                    ptnew += '; ' + part
                else:
                    ptnew += ', ' + part
                if re.search('\d', part):
                    numbers = True
            rec['refs'].append([('x', ptnew)])

    print rec.keys()

  
#write xml
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
