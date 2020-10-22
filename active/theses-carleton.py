# -*- coding: utf-8 -*-
#harvest theses from Carleton U. (main)
#FS: 2019-12-12


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

publisher = 'Carleton U. (main)'

hdr = {'User-Agent' : 'Magic Browser'}
for discipline in ['Physics', 'Mathematics']:
    recs = []
    for year in [str(now.year), str(now.year-1)]:
        tocurl = 'https://curve.carleton.ca/167299e9-53e6-48d7-a28d-8af2f87719ec?f%5B0%5D=thesis_degree_level%3ADoctoral&f%5B1%5D=dcterms_date%3A' + year + '&f%5B2%5D=thesis_degree_discipline%3A' + discipline
        print tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        divs = tocpage.body.find_all('div', attrs = {'class' : 'views-row'})
        for div in divs:
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
            for div2 in div.find_all('div', attrs = {'class' : 'views-field-title'}):
                for a in div2.find_all('a'):
                    rec['link'] = 'https://curve.carleton.ca' + a['href']
                    recs.append(rec)
    time.sleep(30)

    i = 0
    for rec in recs:
        rec['doi'] = '20.2000/' + re.sub('\W', '', rec['link'][6:])
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (discipline, i, len(recs), rec['link'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            time.sleep(3)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            except:
                print "no access to %s" % (rec['link'])
                continue    
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'dcterms.creator':
                    author = meta['content']
                    rec['autaff'] = [[ author, publisher ]]
                #title
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'dcterms.date':
                    rec['date'] = meta['content']
                #abstract
                elif meta['name'] == 'abstract':
                    rec['abs'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['pdf_url'] = meta['content']

        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                if 'pdf_url' in rec.keys():
                    rec['FFT'] = rec['pdf_url']
        print '  ', rec.keys()
        #doi
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('doi.org\/10\.22215', a['href']):
                rec['doi'] = re.sub('.*doi.org\/', '', a['href'])
    jnlfilename = 'THESES-CARLETON-%s_%s' % (stampoftoday, re.sub('\W', '', discipline))


    #closing of files and printing
    xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
