#program to harvest "Revista Mexicana de Fisica"
# -*- coding: UTF-8 -*-
## FS 2018-11-12

import os
import ejlmod2
import codecs
import re
import sys
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time


tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

def tfstrip(x): return x.strip()

publisher = 'Sociedad Mexicana de Fisica'
volume = sys.argv[1]
issue = sys.argv[2]
jnl = 'Rev.Mex.Fis.'
jnlfilename = 'rmf'+volume+'.'+issue
tc = 'P'

#load list of issues
jtocurl = 'https://rmf.smf.mx/ojs/rmf/issue/archive'
try:
    jtocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(jtocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (jtocurl)
    time.sleep(180)
    jtocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(jtocurl))

#find issue link
for h4 in jtocpage.body.find_all('h4'):
    if re.search('.*Vol %s, No %s .*' % (volume, issue), h4.text):
        for a in h4.find_all('a'):
            tocurl = a['href']
            print tocurl

#load table of contents
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    
#go through table of contents
for title in tocpage.head.find_all('title'):
    year = re.sub('.*\((\d\d\d\d)\).*', r'\1', title.text.strip())
recs = []
for table in tocpage.body.find_all('table', attrs = {'class' : 'tocArticle'}):
    rec = {'jnl' : jnl, 'vol' : volume, 'issue' : issue, 'year' : year,
           'tc' : tc, 'keyw' : [], 'autaff' : []}
    #title and article link
    for div in table.find_all('div', attrs = {'class' : 'tocTitle'}):
        rec['tit'] = div.text.strip()
        for a in div.find_all('a'):
            rec['articlelink'] = a['href']
    recs.append(rec)


#details from individual article pages
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['articlelink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['articlelink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['articlelink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['articlelink']))
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DC.Date.issued':
                rec['date'] = meta['content']
            elif meta['name'] == 'DC.Description':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.Identifier.DOI':
                rec['doi'] = meta['content']
            elif meta['name'] == 'DC.Rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : meta['content']}
            elif meta['name'] == 'DC.Subject':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = re.sub('view', 'download', meta['content'])
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])


xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
#xmlfile  = open(xmlf,'w')
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












