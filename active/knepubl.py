# -*- coding: UTF-8 -*-
#program to harvest KnE Energy and Physics
# FS 2018-05-22


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


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'KnE publishing'
tc = 'C'

issuenr = sys.argv[1]

toclink = 'https://knepublishing.com/index.php/KnE-Energy/issue/view/%s' % (issuenr)


jnlfilename = "kne%s" % (issuenr)
if len(sys.argv) > 2:
    jnlfilename = "kne%s.%s" % (issuenr, sys.argv[2])


print "get table of content..."

try:
    tocpage = BeautifulSoup(urllib2.urlopen(toclink))
except:
    print '%s not found' % (toclink)
    sys.exit(0)

recoll = re.compile('.*\(?for t?h?e? *(.*) [cC]ollaboration.*')
recoll2 = re.compile('.*\(?on behalf of t?h?e? *(.*) [cC]ollaboration.*')

recs = []
for div in tocpage.find_all('div', attrs = {'class' : 'detail_box'}):
    rec = {'jnl' : 'KnE Energ.Phys.', 'tc' : tc, 'aff' : [], 'auts' : [], 'refs' : []}
    if len(sys.argv) > 2:
        rec['cnum'] = sys.argv[2]
    for a in div.find_all('a', attrs = {'class' : 'title'}):
        rec['artlink'] =  a['href']
    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    try:
        artpage = BeautifulSoup(urllib2.urlopen(rec['artlink']))
    except:
        print 'waiting 5 minutes'
        time.sleep(300)
        artpage = BeautifulSoup(urllib2.urlopen(rec['artlink']))   
    #header
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content']
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    for div in artpage.find_all('div', attrs = {'class' : 'metadata-group'}):
        if div.find_all('div', attrs = {'class' : 'metadata-chunk'}):
            continue
        #license
        for a in div.find_all('a'):
            if re.search('^Creative Commons', a.text):
                rec['licence'] = {'url' : a['href']}
        #DOI
        for span in div.find_all('span'):
            if re.search('DOI:', span.text):
                rec['doi'] = re.sub('.* (10\..*)', r'\1', div.text.strip())
        #aff
        for div2 in div.find_all('div'):            
            for sup in div2.find_all('sup'):
                sup.replace_with('')
                for a in div2.find_all('a'):
                    if a.has_attr('id'):
                        rec['aff'].append('Aff%s= %s' % (a['id'][1:], re.sub('named anchor ', '', div2.text.strip())))
        #authors
        if 'author-names' in div.attrs['class']:
            for sup in div.find_all('sup'):
                tag = sup.text.strip()
                sup.replace_with(', =Aff%s' % (tag))
            for author in re.split(' *, *', re.sub(' and ', ' ', div.text.strip())):
                auth = re.sub('\n', '', re.sub('named anchor ', '', author))
                if recoll.search(auth):
                    rec['col'] = recoll.sub(r'\1', auth).strip()
                    rec['auts'].append(re.sub('[ \(]for .*', '', auth).strip())
                elif recoll2.search(auth):
                    rec['col'] = recoll2.sub(r'\1', auth).strip()
                    rec['auts'].append(re.sub('\W*on behalf .*', '', auth).strip())
                else:
                    rec['auts'].append(auth)
    #abstract
    for div in artpage.find_all('div', attrs = {'class' : 'acontent'}):
        rec['abs'] = re.sub('  +', ' ', re.sub('[\n\t]', ' ', div.text.strip()))
    #references
    for div in artpage.find_all('div', attrs = {'class' : 'ref-content'}):
        if 'cell' in div.attrs['class']:
            ref = re.sub('named anchor ', '', div.text.strip())
            ref = re.sub('  +', ' ', re.sub('[\n\t]', ' ', ref))
            rec['refs'].append([('x', ref)])
    
    print '---{ %i/%i }---------------------------------------' % (i, len(recs))
    print rec.keys()

  
#write xml
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
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
