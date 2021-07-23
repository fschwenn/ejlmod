# -*- coding: utf-8 -*-
#harvest Wuppertal U.
#FS: 2020-02-24


import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Wuppertal U.'
hdr = {'User-Agent' : 'Magic Browser'}

docthresh = 1
years = 2

recs = []
prerecs = []
jnlfilename = 'THESES-WUPPERTAL-%s' % (stampoftoday)
tocfilname = '/tmp/%s.toc' % (jnlfilename)

tocurl = 'http://elpub.bib.uni-wuppertal.de/servlets/MCRSearchServlet?mask=browse/ddc.xml&query=(ddc%20=%20%225%22)%20AND%20(status%20=%20%22published%22)%20AND%20(datevalidfrom%20<=%20%2221.2.2020%22)%20AND%20(datevalidto%20>=%20%2221.2.2020%22)&maxResults=0&datecreation.sortField.1=descending'
print tocurl
if not os.path.isfile(tocfilname):
    os.system('wget -T 300 -t 3 -q -O %s "%s"' % (tocfilname, tocurl))
    time.sleep(5)
inf = open(tocfilname, 'r')
tocpage = BeautifulSoup(''.join(inf.readlines()))
inf.close()

for ol in tocpage.find_all('ol', attrs = {'class' : 'results'}):
    for li in ol.find_all('li'):
        for h3 in li.find_all('h3'):
            for a in h3.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'link' : a['href'], 'note' : []}
                rec['docnr'] = int(re.sub('\D', '', a['href']))
                rec['doi'] = '20.2000/Wuppertal/%09i' % (rec['docnr'])
        for div in li.find_all('div', attrs = {'class' : 'types'}):
            rec['MARC'] = [['502', [('c', publisher)]]]
            if div.text.strip() == 'Dissertation':
                rec['MARC'][0][1].append(('b', 'PhD'))
            elif div.text.strip() == 'Habilitation':
                rec['MARC'][0][1].append(('b', 'Habilitation'))
        if rec['docnr'] > docthresh:
            prerecs.append(rec)

i = 0
for rec in prerecs:
    i += 1
    keepit = False
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(10)
    except:
        try:
            print 'retry %s in 180 seconds' % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print 'no access to %s' % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] != 'eng':
                    if meta['content'] == 'deu':
                        rec['language'] = 'german'
                    else:
                        rec['language'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.description':
                rec['abs'] = re.sub('<p>', '', meta['content'])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            elif meta['name'] == 'DC.identifier':
                #urn
                if re.search('^urn', meta['content']):
                    rec['urn'] = meta['content']
                #doi
                elif re.search('doi.org', meta['content']):
                    rec['doi'] = re.sub('.*\/(10\..*)', r'\1', meta['content'])
            #PDF
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
    #date
    for div in artpage.body.find_all('div', attrs = {'class' : 'container_12'}):
        datum = False
        for div2 in div.find_all('div'):
            div2t = div2.text.strip()
            if datum:
                if re.search('.*([12]\d\d\d).*', div2t):
                    rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', div2t)
                    rec['MARC'][0][1].append(('d', rec['year']))
                    rec['date'] =  re.sub('(\d\d).(\d\d).(\d\d\d\d)', r'\3-\2-\1', div2t)                    
                datum = False
            if re.search('Datum der Promotion', div2t):
                datum = True
    rec['autaff'][-1].append(publisher)
    if 'year' in rec.keys() and int(rec['year']) < now.year - years:
        print '  skip', rec['year']
    else:
        print '  ', rec.keys()
        recs.append(rec)
                
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text: 
    retfiles = open(retfiles_path,'a')
    retfiles.write(line)
    retfiles.close()


