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

pages = 3+30

hdr = {'User-Agent' : 'Magic Browser'}

for fac in ['510', '530']:
    recs = []
    print '==={ %s }===' % (fac)
    for page in range(pages):
        time.sleep(1)
        tocurl = 'https://ediss.sub.uni-hamburg.de/ergebnis.php?startindex=10&dir=&page=' + str(page+1) + '&suchfeld1=o.sachgruppe_ddc&suchwert1=' + fac + '&suchfeld2=person&suchwert2=&suchfeld3=date_year&suchwert3=&opt1=AND&opt2=AND&suchart=exakt&sort=o.date_year%20DESC,%20o.title&sprache=&Lines_Displayed=10&la=de'
        print tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for tr in tocpage.body.find_all('tr'):
            for td in tr.find_all('td', attrs = {'valign' : 'top'}):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
                for a in tr.find_all('a'):
                    rec['artlink'] = a['href']
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
                #title
                elif meta['name'] == 'citation_title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'citation_date':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    for keyw in re.split(' *, *', meta['content']):
                        rec['keyw'].append(keyw)
                #urn
                elif meta['name'] == 'DC.Identifier':
                    if re.search('^urn:', meta['content']):
                        rec['urn'] = meta['content']
                    else:
                        rec['link'] = meta['content']
        for tr in artpage.body.find_all('tr'):
            tds = tr.find_all('td', attrs = {'class' : 'frontdoor'})
            if len(tds) == 2:
                if re.search('Kurzfassung.*Englisch', tds[0].text):
                    rec['abs'] = tds[1].text.strip()
        print rec.keys()

    jnlfilename = 'THESES-HAMBURG-%s_%s' % (stampoftoday, fac)


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
