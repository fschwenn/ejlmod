# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest De Gruyter journals
# FS 2016-01-04

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup
import datetime


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
urltrunc = 'https://www.degruyter.com'
publisher = 'De Gruyter'

journal = sys.argv[1]
year  = sys.argv[2]
vol = sys.argv[3]
iss = sys.argv[4]

jnlfilename = 'dg%s.%s.%s' %  (journal, vol, iss)
if journal == 'phys':
    if int(vol) <= 12:
        jnl = 'Central Eur.J.Phys.'
    else:        
        jnl = 'Open Phys.'

#get list of volumes
if not os.path.isfile('/tmp/dg%s' % (jnlfilename)):
    os.system("wget -T 300 -t 3 -q -O /tmp/dg%s %s/view/j/%s.%s.%s.issue-%s/issue-files/%s.%s.%s.issue-%s.xml" % (jnlfilename, urltrunc, journal, year, vol, iss, journal, year, vol, iss))
inf = open('/tmp/dg%s' % (jnlfilename), 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()))
inf.close()
#get volumes
recs = []
i = 0
for h3 in tocpage.find_all('h3'):
    for a in h3.find_all('a'):
        if a.has_attr('href') and re.search('^.view', a['href']):
            i += 1
            vollink = urltrunc + a['href']
            print vollink
            rec = {'tc' : 'P', 'jnl' : jnl, 'year' : year, 'vol' : vol, 'issue' : iss,
                   'auts' : [], 'aff' : []}
            #title
            rec['tit'] = a.text.strip()
            #get details
            if not os.path.isfile('/tmp/dg%s.%i' % (jnlfilename, i)):
                os.system("wget -T 300 -t 3 -q -O /tmp/dg%s.%i %s" % (jnlfilename, i, vollink))
            inf = open('/tmp/dg%s.%i' % (jnlfilename, i), 'r')
            artpage = BeautifulSoup(''.join(inf.readlines()))
            inf.close()
            #abstract
            for div in artpage.find_all('div', attrs = {'class' : 'articleBody_abstract'}):
                for p in div.find_all('p'):
                    rec['abs'] = p.text.strip()
            #authors
            for div in artpage.find_all('div', attrs = {'class' : 'contributors'}):
                for sup in artpage.find_all('sup'):
                    for a in sup.find_all('a'):
                        cont = a.text
                        a.replace_with(' / =Aff%s ' % (cont))
                for aut in re.split(' +\/ +', div.text):
                    if re.search('=Aff', aut):
                        rec['auts'].append(aut)
                    else:
                        rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', aut))
            #affiliations
            for div in artpage.find_all('div', attrs = {'class' : 'NLM_affiliations'}):                
                for p in div.find_all('p'):
                    for sup in p.find_all('sup'):
                        cont = sup.text
                        sup.replace_with('Aff%s= ' % (cont))
                    rec['aff'].append(p.text)
            #keywords / PACS
            for p in artpage.find_all('p', attrs = {'class' : 'articleBody_keywords'}):
                for span in p.find_all('span'):
                    if re.search('PACS', span.text):
                        key = 'pacs'                        
                    else:
                        key = 'keyw'
                    rec[key] = []
                for a in p.find_all('a'):
                    if a.text and not a.text in rec[key]:
                        rec[key].append(a.text)
            #references
            referencesection = artpage.find_all('div', attrs = {'class' : 'moduleDetail refList'})
            if not referencesection:
                referencesection = artpage.find_all('ul', attrs = {'class' : 'simple'})
            for div in referencesection:
                rec['refs'] = []
                for li in div.find_all('li'):
                    for a in li.find_all('a'):
                        if a.has_attr('href') and re.search('doi.org', a['href']):
                            doi = re.sub('.*doi.org.', '', a['href'])
                            a.replace_with(', DOI: %s  ' % (doi))                        
                    rec['refs'].append([('x', li.text)])
            #date
            for div in artpage.find_all('div', attrs = {'class' : 'pubHistory'}):
                for dl in div.find_all('dl', attrs = {'id' : 'date-epub'}):
                    for dd in dl.find_all('dd', attrs = {'class' : 'fieldValue'}):
                        rec['date'] = dd.text
            #DOI
            for meta in artpage.find_all('meta', attrs = {'name' : 'citation_doi'}):
                rec['doi'] = meta['content']
            #licence
            for div in artpage.find_all('div', attrs = {'class' : 'permissions'}):
                for a in div.find_all('a'):
                    rec['licence'] = {'url' : a['href']}
                    #fulltext pdf
                    for meta in artpage.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                        rec['FFT'] = meta['content']
            #pages 
            for div in artpage.find_all('div', attrs = {'class' : 'citationInfo'}):
                pages = re.sub('.*Volume \d*(.*)DOI:.*', r'\1', div.text.strip())
                if re.search('[pP]ages \d+\D\d+', pages):
                    rec['p1'] = re.sub('.*[pP]ages (\d+).*', r'\1', pages)
                    rec['p2'] = re.sub('.*[pP]ages \d+\D(\d+).*', r'\1', pages)
            recs.append(rec)


#write xml
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
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

