# -*- coding: utf-8 -*-
#harvest theses from EPFL
#FS: 2019-10-28


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

insttoskip = ['CDH', 'CDM']
                  
now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Ecole Polytechnique, Lausanne'
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
recs = {}
for year in [now.year, now.year-1]: 
    prerecs = []
    print '==={ %i }===' % (year)
    tocurl = 'https://infoscience.epfl.ch/search?ln=en&cc=Infoscience%2FResearch%2FThesis&p=&f=&rm=&ln=en&sf=year&so=d&rg=500&c=Infoscience%2FResearch%2FThesis&c=&of=hb&fct__3=' + '%i' % (year)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(30)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'result-title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'year' : str(year), 'keyw' : [], 'inst' : '', 'date' : str(year)}
            rec['artlink'] = 'https://infoscience.epfl.ch' + a['href']
            rec['tit'] = a.text.strip()
            prerecs.append(rec)
    j = 0
    for rec in prerecs:
        j += 1
        print '---{ %i }---%i/%i }---{ %s }------' % (year, j, len(prerecs), rec['artlink'])
        try:
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req))
            time.sleep(30)
        except:
            print 'wait 10 minutes'
            time.sleep(600)
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req))
            time.sleep(30)        
        for meta in artpage.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'citation_author':
                    rec['autaff'] = [[ meta['content'], 'Ecole Polytechnique, Lausanne']]
                #abstract
                elif meta['name'] == 'description':
                    rec['abs'] = meta['content']
                #keywords
                elif meta['name'] == 'citation_keywords':
                    rec['keyw'].append(meta['content'])
                #DOI
                elif meta['name'] == 'citation_doi':
                    rec['doi'] = meta['content']
                #upload PDF at least hidden
                elif meta['name'] == 'citation_pdf_url':
                    rec['hidden'] = meta['content']
        for a in artpage.body.find_all('a'):
            if a.has_attr('href'):
                if re.search('\/collection\/Infoscience\/Research\/[A-Z]', a['href']):
                    inst = re.sub('.*Research\/(.*)\?.*', r'\1', a['href'])
                    if inst != 'Thesis':
                        print ' . ', inst
                        if len(inst) > len(rec['inst']):
                            rec['inst'] = inst
                            rec['note'] = [ inst ]
        rec['inst'] = re.sub('\/.*', '', rec['inst'])
        if rec['inst'] in insttoskip:
            print 'skip thesis from %s' % (rec['inst'])
        else:
            print 'keep thesis from %s' % (rec['inst'])
            print '  ', rec.keys()
            if rec['inst'] in recs.keys():
                recs[rec['inst']].append(rec)
            else:
                recs[rec['inst']] = [rec]

for inst in recs.keys():                
    jnlfilename = 'THESES-EPFL-%s_%s' % (stampoftoday, inst)            
    #closing of files and printing
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writeXML(recs[inst], xmlfile,publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()


