# -*- coding: utf-8 -*-
#harvest theses from Oklahoma
#FS: 2019-11-06


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
import json

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
numopages = 5
articlesperpage = 50

hdr = {'User-Agent' : 'Magic Browser'}
for uni in [('Oklahoma U.', '11244/10476'), ('Oklahome State U.', '11244/10462')]:
    publisher = uni[0]
    jnlfilename = 'THESES-%s-%s' % (re.sub('\W', '', uni[0].upper()), stampoftoday)
    recs = []
    for i in range(numopages):
        tocurl = 'https://shareok.org/handle/%s/browse?rpp=%i&sort_by=2&type=dateissued&offset=%i&etal=-1&order=DESC' % (uni[1], articlesperpage, articlesperpage*i)
        print '---{ %s }---{ %i/%i }---{ %s }---' % (uni[0], i+1, numopages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(10)
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
            for a in div.find_all('a'):
                rec['artlink'] = 'https://shareok.org' + a['href'] + '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                recs.append(rec)
    i = 0
    for rec in recs:
        i += 1
        print '---{ %i/%i}---{ %s}------' % (i, len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            time.sleep(3)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['artlink'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            except:
                print "no access to %s" % (rec['artlink'])
                continue      
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'DC.creator':
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
                    rec['autaff'][-1].append(publisher)
                #title
                elif meta['name'] == 'DC.title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'DCTERMS.issued':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    for keyw in re.split(' *; *', meta['content']):
                        rec['keyw'].append(keyw)
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    rec['abs'] = meta['content']
                #license            
                elif meta['name'] == 'DC.rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
                        for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                            rec['FFT'] = meta2['content']
                #upload PDF at least hidden
                if not 'FFT' in rec.keys():
                    for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                        rec['hidden'] = meta2['content']
        for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
            (label, word) = ('', '')
            for td in tr.find_all('td', attrs = {'class' : 'label-cell'}): 
                label = td.text.strip()
            for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
                word = td.text.strip()
            #ORCID
            if re.search('shareok.orcid', label):
                rec['autaff'] = [[ author, 'ORCID:' + re.sub('.*.org/', '', word), publisher ]]
            #supervisor
            elif re.search('dc.contributor.advisor', label):
                rec['supervisor'] = [[ word, publisher ]]
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
                                   
