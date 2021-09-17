# -*- coding: utf-8 -*-
#harvest theses from Hamburg
#FS: 2020-01-27


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

publisher = 'U. Hamburg (main)'

typecode = 'T'

pages = 3
rpp = 10

hdr = {'User-Agent' : 'Magic Browser'}

for fac in ['510+Mathematik', '530+Physik']:
    recs = []
    print '==={ %s }===' % (fac)
    for page in range(pages):
        time.sleep(1)
        #tocurl = 'https://ediss.sub.uni-hamburg.de/ergebnis.php?startindex=10&dir=&page=' + str(page+1) + '&suchfeld1=o.sachgruppe_ddc&suchwert1=' + fac + '&suchfeld2=person&suchwert2=&suchfeld3=date_year&suchwert3=&opt1=AND&opt2=AND&suchart=exakt&sort=o.date_year%20DESC,%20o.title&sprache=&Lines_Displayed=10&la=de'
        tocurl = 'https://ediss.sub.uni-hamburg.de/simple-search?query=&location=&filter_field_1=subject&filter_type_1=equals&filter_value_1=' + fac + '&crisID=&relationName=&sort_by=bi_sort_2_sort&order=desc&rpp=' + str(rpp) + '&etal=0&start=' + str(page*rpp)


        print tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for tr in tocpage.body.find_all('tr'):
            for td in tr.find_all('td', attrs = {'headers' : 't1'}):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : []}
                if fac == '510+Mathematik':
                    rec['fc'] = 'm'
                for a in td.find_all('a'):
                    rec['artlink'] = 'https://ediss.sub.uni-hamburg.de' + a['href']
                    recs.append(rec)
    i = 0
    for rec in recs:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (fac, i, len(recs), rec['artlink'])
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
                if meta['name'] == 'citation_author':
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
                    rec['autaff'][-1].append(publisher)
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    if meta.has_attr('xml:lang'):
                        if meta['xml:lang'] == 'en':
                            rec['abs'] = meta['content']
                        elif meta['xml:lang'] == 'de':
                            rec['absde'] = meta['content']
                    else:
                        rec['abs'] = meta['content']
                #supervisor
                elif meta['name'] == 'DC.contributor':
                    rec['supervisor'].append([re.sub(' *\(.*', '', meta['content'])])
                #title
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'DCTERMS.issued':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    for keyw in re.split(' *, *', meta['content']):
                        rec['keyw'].append(keyw)
                #language
                elif meta['name'] == 'language':
                    if meta['content'] == 'de':
                        rec['language'] = 'german'
                #urn
                elif meta['name'] in ['DC.Identifier', 'DC.identifier']:
                    if re.search('^urn:', meta['content']):
                        rec['urn'] = meta['content']
                    else:
                        rec['link'] = meta['content']
                #fulltext
                elif meta['name'] == 'citation_pdf_url':
                    rec['hidden'] = meta['content']
        #abstract
        if not 'abs' in rec.keys() and 'absde' in rec.keys():
            rec['abs'] = rec['absde']
        print rec.keys()

    jnlfilename = 'THESES-HAMBURG-%s_%s' % (stampoftoday, fac)


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
