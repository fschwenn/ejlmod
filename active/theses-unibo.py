# -*- coding: utf-8 -*-
#harvest theses from Bologna U. 
#FS: 2019-09-13


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

publisher = 'Bologna U.'

typecode = 'T'



for year in [now.year-1, now.year]:
    recs = []
    jnlfilename = 'THESES-UNIBO-%i-%s' % (year, stampoftoday)
    tocurl = 'http://amsdottorato.unibo.it/view/year/%i.html' % (year)
    print tocurl
    hdr = {'User-Agent' : 'Magic Browser'}
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
    for p in tocpage.body.find_all('p'):
        for span in p.find_all('span',  attrs = {'class' : 'nolink'}):
            span.replace_with('')
        for a in p.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'artlink' : a['href'], 'keyw' : []}
            recs.append(rec)
    i = 0
    for rec in recs:
        i += 1
        print '---{ %i }---{ %i/%i }---{ %s }------' % (year, i, len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            time.sleep(3)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            except:
                print "no access to %s" % (rec['link'])
                continue      
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                #author
                if meta['name'] == 'DC.creator':
                    author = re.sub(' *\[.*', '', meta['content'])
                    author = re.sub(' <\d.*', '', author)
                    rec['autaff'] = [[ author ]]
                    rec['autaff'][-1].append('Bologna U.')
                #title
                elif meta['name'] == 'DC.title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'eprints.date':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'eprints.keywords':
                    for keyw in re.split(' *[;\n] *', meta['content']):
                        rec['keyw'].append(keyw.strip())
                #DOI
                elif meta['name'] == 'DC.identifier':
                    if re.search('10.6092', meta['content']):
                        rec['doi'] = re.sub('.*?(10.6092\/.*)\..*', r'\1', meta['content'])
                    elif re.search('urn.nbn.it.unibo', meta['content']):
                        rec['urn'] = meta['content']
                #language
                elif meta['name'] == 'DC.language':
                    if meta['content'] == 'ita':
                        rec['language'] = 'italian'
                #FFT
                elif meta['name'] == 'eprints.document_url':
                    rec['FFT'] = meta['content']
                #abstract
                elif meta['name'] == 'eprints.abstract':
                    rec['abs'] = meta['content']
        #license            
        for table in artpage.body.find_all('table', attrs = {'class' : 'ep_block'}):
            for a in table.find_all('a'):
                if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                    rec['licence'] = {'url' : a['href']}
        if not 'doi' in rec.keys():
            rec['link'] = rec['artlink']
            if not 'urn' in rec.keys():
                rec['doi'] = '20.2000/UNIBO/' + re.sub('.*it\/', '', rec['artlink'])
        print '     ', rec.keys()

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
