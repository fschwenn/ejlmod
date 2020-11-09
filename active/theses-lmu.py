# -*- coding: utf-8 -*-
#harvest theses from LMU Munich
#FS: 2019-10-23


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

publisher = 'Munich U.'


tocurl = 'https://edoc.ub.uni-muenchen.de/view/subjects/fak17.html'
hdr = {'User-Agent' : 'Magic Browser'}
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))

#get all links 
prerecs = {}
reyear = re.compile('.*\(([12]\d\d\d)\):.*')
for p in tocpage.body.find_all('p'):
    for a in p.find_all('a'):
        rec = {'tc' : 'T',  'jnl' : 'BOOK'}
        rec['artlink'] = a['href']
        pt = re.sub('[\n\t\r]', '', p.text.strip())
        if reyear.search(pt):
            rec['year'] = reyear.sub(r'\1', pt)
            if int(rec['year']) in prerecs.keys():
                prerecs[int(rec['year'])].append(rec)
            else:
                prerecs[int(rec['year'])] = [rec]

for year in [ now.year-1, now.year ]:
    jnlfilename = 'THESES-LMU-%s-%i' % (stampoftoday, year)
    if year in prerecs.keys():
        print year, len(prerecs[year])
        recs = prerecs[year]
        i = 0
        for rec in recs:
            i += 1
            print '---{ %i }---{ %i/%i }---{ %s }------' % (year, i, len(recs), rec['artlink'])
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
                if meta.has_attr('name') and meta.has_attr('content'):
                    #author
                    if meta['name'] == 'DC.creator':
                        author = meta['content']
                        rec['autaff'] = [[ author ]]
                        rec['autaff'][-1].append('Munich U.')
                    #title
                    elif meta['name'] == 'eprints.title_name':
                        rec['tit'] = meta['content']
                    #date
                    elif meta['name'] == 'eprints.date':
                        rec['date'] = meta['content']
                    #keywords
                    elif meta['name'] == 'eprints.keywords':
                        rec['keyw'] = re.split(' *, *', meta['content'])
                    #abstract
                    elif meta['name'] == 'eprints.abstract_name':
                        rec['abs'] = meta['content']
                    #FFT
                    elif meta['name'] == 'eprints.document_url':
                        rec['FFT'] = meta['content']
                    #supervisor
                    elif meta['name'] == 'eprints.referee_one_name':
                        rec['supervisor'] = [[meta['content'], 'Munich U.']]
                    #URN
                    elif meta['name'] == 'eprints.urn':
                        rec['urn'] = meta['content']
                    #language
                    elif meta['name'] == 'eprints.language':
                        if meta['content'] == 'ger':
                            rec['language'] = 'german'
            #DOI
            for div in artpage.body.find_all('div', attrs = {'class' : 'ep_block_doi'}):
                for a in div.find_all('a'):
                    if a.has_attr('href') and re.search('doi.org', a['href']):
                        rec['doi'] = re.sub('.*doi.org\/', '', a['href'])
            if not 'doi' in rec.keys():
                rec['link'] = rec['artlink']
            #license
            for a in artpage.body.find_all('a'):
                if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                    rec['license'] = {'url' : a['href']}
            print '    ', rec.keys()
            
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
    else:
        print year, 0


