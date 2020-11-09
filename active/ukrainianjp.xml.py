#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest Ukrainian Journal of Physics
# FS 2019-01-22

import os
import ejlmod2
import codecs
import re
import sys
import urllib2
import urlparse
from bs4 import BeautifulSoup
import time



tmpdir = '/tmp'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

publisher = 'National Academy of Sciences of Ukraine'
tc = 'P'
jnl = 'ujp'
jnlname = 'Ukr.J.Phys.'

tocurl = 'https://ujp.bitp.kiev.ua/index.php/ujp/issue/view/%s' % (sys.argv[1])
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
#for div in tocpage.body.find_all('div', attrs = {'class' : 'title'}):
for div in tocpage.body.find_all('h3', attrs = {'class' : 'title'}):
    rec = {'jnl' : jnlname, 'tc' : tc, 'autaff' : [], 'keyw' : []}
    for a in div.find_all('a'):
        rec['artlink'] = a['href']
        rec['tit'] = a.text.strip()                    
    recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
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
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            elif meta['name'] == 'DC.Type.articleType':
                rec['note'] = [meta['content']]                
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'DC.Description':
                if meta['xml:lang'] == 'en':
                    rec['abs'] = meta['content']
    if 'Reviews' in rec['note']:
        rec['tc'] = 'R'
    for a in artpage.body.find_all('a', attrs = {'class' : 'obj_galley_link pdf'}):
        if a.text.strip() == 'PDF':
            rec['FFT'] = a['href']
    for div in artpage.body.find_all('div', attrs = {'class' : 'item references'}):
        rec['refs'] = []
        for p in div.find_all('p'):
            for a in p.find_all('a'):
                atext = a.text.strip()
                if re.search('doi.org', atext):
                    a.replace_with(re.sub('.*doi.org\/', ', DOI: ', atext))
            rec['refs'].append([('x', p.text.strip())])
    print '   ', rec.keys()
            
jnlfilename = '%s%s.%s' % (jnl, rec['vol'], rec['issue'])


                                       
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
