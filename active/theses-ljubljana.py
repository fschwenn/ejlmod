# -*- coding: utf-8 -*-
#harvest theses from Ljubljana U.
#FS: 2022-02-09


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Ljubljana U.'
jnlfilename = 'THESES-LJUBLJANA-%s' % (stampoftoday)
rpp = 10

years = [now.year, now.year-1]

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for year in years:
    print '==={ %i }===}' % (year)
    tocurl = 'https://repozitorij.uni-lj.si/Iskanje.php?type=napredno&lang=eng&niz0=&stl0=Naslov&op1=AND&niz1=&stl1=Avtor&op2=AND&niz2=&stl2=Opis&op3=AND&niz3=' + str(year) + '&stl3=LetoIzida&vrsta=dok&jezik=0&vir=11'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpages = [BeautifulSoup(urllib2.urlopen(req), features="lxml")]
    for div in tocpages[0].body.find_all('div', attrs = {'class' : 'Stat'}):
        numberoftheses = int(re.sub('\D', '', re.sub('.*\/', '', div.text.strip())))
        print '  %i theses expected' % (numberoftheses)
    for page in range((numberoftheses-1) / rpp):
        tocurlp = tocurl+'&page=' + str(page+2)
        print tocurlp
        req = urllib2.Request(tocurlp, headers=hdr)
        tocpages.append(BeautifulSoup(urllib2.urlopen(req), features="lxml"))
        time.sleep(3)
    for tocpage in tocpages:
        for table in tocpage.body.find_all('table', attrs = {'class' : 'ZadetkiIskanja'}):
            for a in table.find_all('a'):
                if a.has_attr('href') and re.search('IzpisGradiva.*id=\d', a['href']):
                    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'note' : [],
                           'year' : str(year), 'supervisor' : []}
                    rec['link'] = 'https://repozitorij.uni-lj.si/' + a['href']
                    rec['doi'] = '30.3000/Ljubljana/' + re.sub('\W', '', a['href'])

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'].append([ meta['content'], publisher ])
            #supervisor
            elif meta['name'] == 'DC.contributor':
                rec['supervisor'].append([meta['content']])
            #abstract
            elif meta['name'] == 'DC.description':
                rec['abs'] = meta['content']
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = re.sub(': (doctoral thesis|doktorska disertacija|PhD thesis)$', '', meta['content'])
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(', ', meta['content']):
                    rec['keyw'].append(keyw)
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'slv':
                    rec['language'] = 'Slovenian'
    print rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path ,"a")
    retfiles.write(line)
    retfiles.close()
