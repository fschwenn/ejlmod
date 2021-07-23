# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Journal "Quantum"
# FS 2020-11-20

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Verein zur Foerderung des Open Access Publizierens in den Quantenwissenschaften'
vol = sys.argv[1]
jnlfilename = 'quantum%s_%s' % (vol, stampoftoday)

    
urltrunk = 'https://quantum-journal.org/volumes/%s/' % (vol)
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))


recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'list-article-content'}):
    for h2 in div.find_all('h2'):
        for a in h2.find_all('a'):
            rec = {'jnl' : 'Quantum', 'tc' : 'P', 'autaff' : [], 'vol' : vol, 'refs' : []}
            rec['artlink'] = a['href']
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (artlink)
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #title
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content'] 
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
            #first page
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content'] 
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #arXiv number
            elif meta['name'] == 'citation_arxiv_id':
                rec['arxiv'] = re.sub('v\d+$', '', meta['content'])
            #references
            elif meta['name'] == 'citation_reference':
                rec['refs'].append([('x', meta['content'] )])
            #date
            elif meta['name'] == 'dc.date':
                rec['date'] = meta['content']
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content'] 
    #abstract
    for p in artpage.body.find_all('p', attrs = {'class' : 'abstract'}):
        rec['abs'] = p.text.strip()
    #references
    for refs in artpage.body.find_all('div', attrs = {'id' : 'references'}):
        rec['refs'] = []
        for p in refs.find_all('p', attrs = {'class' : 'break'}):
            x = p.text.strip()
            rdoi = ''
            for a in p.find_all('a'):
                if a.has_attr('href') and re.search('doi.org\/10', a['href']):
                    rdoi = re.sub('.*doi.org\/', 'doi:', a['href'])
            if rdoi:
                if re.search('^\[\d+\]', x):
                    o = re.sub('.(\d+).*', r'\1', x)
                    rec['refs'].append([('o', o), ('a', rdoi), ('x', x)])
                else:
                    rec['refs'].append([('a', rdoi), ('x', x)])
            else:
                rec['refs'].append([('x', p.text)])
    print '  ', rec.keys()

                                       
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
 
