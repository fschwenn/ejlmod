# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest ANNALES DE L'INSTITUT FOURIER
# FS 2019-10-22

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

tmpdir = '/tmp'
def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

publisher = 'Annales de lInstitut Fourier'
vol = sys.argv[1]
iss = sys.argv[2]
year = str(int(vol) + 1950)
if iss == '7':
    typecode = 'C'
else:
    typecode = 'P'
jnlfilename = 'annif%s.%s' % (vol, iss)
tocurl = 'https://aif.centre-mersenne.org/issues/AIF_%s__%s_%s/' % (year, vol, iss)

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(10)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for span in tocpage.body.find_all('span', attrs = {'class' : 'article-title'}):
    rec = {'jnl' : 'Annales Inst.Fourier', 'vol' : vol, 'issue' : iss, 'tc' : typecode, 
           'refs' : [], 'auts' : [], 'year' : year}
    for a in span.find_all('a'):
        rec['artlink'] = 'https://aif.centre-mersenne.org' + a['href']
        rec['tit'] = a.text.strip()
    recs.append(rec)

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    time.sleep(2)
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req))
    #artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #pages
            if meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content'] 
            #pdf
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #authors
            elif meta['name'] == 'citation_author':
                rec['auts'].append(meta['content'])
    #abstract
    for div in artpage.body.find_all('div', attrs = {'id' : 'abstract-en'}):
        rec['abs'] = div.text.strip()
    #DOI and keywords and date
    for div in artpage.body.find_all('div', attrs = {'id' : 'info-tab'}):
        for a in div.find_all('a'):
            rec['doi'] = re.sub('.*org\/', '', a['href'])
        divt = re.sub('[\n\t\r]', ' ', div.text.strip())
        keywords = re.sub('.*Keywords: *', '', divt)
        rec['keyw'] = re.split(', ', keywords)
        if re.search('Published online', divt):
            rec['date'] = re.sub('.*Published online *: *([\d\-]+).*', r'\1', divt)
        elif re.search('Publi. le', divt):
            rec['date'] = re.sub('.*Publi. le *: *([\d\-]+).*', r'\1', divt)
    #references
    for p in artpage.body.find_all('p', attrs = {'class' : 'bibitemcls'}):
        doi = False
        for a in p.find_all('a'):
            if re.search('doi.org', a['href']):
                doi = re.sub('.*org\/', 'doi:', a['href'])
                a.replace_with('')
        pt = re.sub('[\n\t\r]', ' ', p.text.strip())
        if doi:
            nr = re.sub('^ *\[(\d+)\].*', r'\1', pt)
            rec['refs'].append([('o', nr), ('a', doi), ('x', pt)])
        else:
            rec['refs'].append([('x', pt)])
    #translated title
    for span in artpage.body.find_all('span', attrs = {'class' : 'article-trans-title'}):
        rec['language'] = 'french'
        rec['transtit'] = re.sub('.*?\[(.*)\].*', r'\1', span.text)
    #license
    if int(vol) >= 65:
        rec['license'] =  {'statement' : 'CC-BY-ND-3.0'}
    print '    ', rec.keys()

                                       
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
 
