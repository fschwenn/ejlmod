# -*- coding: utf-8 -*-
# program to harvest LHEP 


import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Andromeda Publishing and Education Services'

typecode = 'P'

jnl = 'LHEP'
webissue = sys.argv[1]
jnlfilename = '%s%s_%s' % (jnl, webissue, stampoftoday)

tocurl = 'http://journals.andromedapublisher.com/index.php/LHEP/issue/view/%s' % (webissue)


try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'obj_article_summary'}):
    for div2 in div.find_all('div', attrs = {'class' : 'title'}):
        rec = {'jnl' : jnl, 'tc' : typecode, 'autaff' : [], 'keyw' : []}
        rec['tit'] = div2.text.strip()
        for a in div2.find_all('a'):
            rec['artlink'] = a['href']
        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%u }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        time.sleep(3)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'].append([meta['content']])
            #affiliation
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #pbn
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            elif meta['name'] == 'citation_issue':
                rec['issue'] = meta['content']
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.Description':
                rec['abs'] = meta['content']
            #license
            elif meta['name'] == 'DC.Rights':
                rec['licence'] = {'url' : meta['content']}
            elif meta['name'] == '':
                rec[''] = meta['content']
            elif meta['name'] == '':
                rec[''] = meta['content']
    #get PDF to extract DOI !!!
    if not os.path.isfile('/tmp/%s.%s.%i.pdf' % (rec['jnl'], stampoftoday ,i)):
        os.system('wget -O /tmp/%s.%s.%i.pdf "%s"' % (rec['jnl'], stampoftoday ,i, rec['FFT']))
    os.system('pdftotext /tmp/%s.%s.%i.pdf /tmp/%s.%s.%i.txt' % (rec['jnl'], stampoftoday, i, rec['jnl'], stampoftoday ,i))
    inf = open('/tmp/%s.%s.%i.txt' % (rec['jnl'], stampoftoday ,i), 'r')
    for line in inf.readlines():
        if re.search('DOI.*(10\.31526\/)', line) and not rec.has_key('doi'):
            rec['doi'] = re.sub('.*?(10\.31526\/.*)', r'\1', line.strip())
            rec['doi'] = re.sub(' .*', '', rec['doi'])
    inf.close()


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
 
