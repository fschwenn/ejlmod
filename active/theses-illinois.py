# -*- coding: utf-8 -*-
#harvest theses from Illinois
#FS: 2020-11-17


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

departments = [('Astronomy', 'Illinois U., Urbana, Astron. Dept.'),
               ('Physics', 'Illinois U., Urbana'),
               ('Mathematics', 'Illinois U., Urbana, Math. Dept.')]
               
publisher = 'Illinois U., Urbana (main)'

rpp = 50
years = [now.year-1, now.year]
##years = [now.year, now.year-1, now.year-2, now.year-3, now.year-4, now.year-5, now.year-6, now.year-7, now.year-8, now.year-9, now.year-10]

hdr = {'User-Agent' : 'Magic Browser'}
for (dep, aff) in departments:
    recs = []
    for year in years:
        tocurl = 'https://www.ideals.illinois.edu/handle/2142/5130/filter-search?etdlevel=Dissertation&date=' + str(year) + '&etdlevel-or=Thesis&etddepartment=' + dep + '&rpp=' + str(rpp)
        print '==={ %s %i }==={ %s }===' % (dep, year, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpages = [ BeautifulSoup(urllib2.urlopen(req)) ]
        for p in tocpages[0].body.find_all('p', attrs = {'class' : 'pagination-info'}):
            numberoftheses = int(re.sub('.*of (\d+).*', r'\1', p.text.strip()))
            numberofpages = (numberoftheses-1) / rpp + 1
        print '  %i theses -> check %i pages' % (numberoftheses, numberofpages)
        for page in range(numberofpages-1):
            print ' =={ %s % i }==={ %i }===' % (dep, year, page+2)
            time.sleep(2)
            req = urllib2.Request(tocurl + '&page=' + str(page+2), headers=hdr)
            tocpages.append(BeautifulSoup(urllib2.urlopen(req)))
        for tocpage in tocpages:
            divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'})
            for div in divs:
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'abs' : '',
                       'supervisor' : []}
                for a in div.find_all('a'):
                    rec['artlink'] = 'https://www.ideals.illinois.edu' + a['href'] #+ '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
        print '   %i theses so far' % (len(recs))
    time.sleep(5)

    i = 0
    for rec in recs:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (dep, i, len(recs), rec['artlink'])
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
                    if re.search('\d\d\d\d\-\d\d\d\d',  meta['content']):
                        rec['autaff'][-1].append('ORCID:' + meta['content'])
                    else:
                        author = re.sub(' *\[.*', '', meta['content'])
                        rec['autaff'] = [[ author ]]
                #supervisor
                elif meta['name'] == 'DC.contributor':
                    rec['supervisor'].append([meta['content']])
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
                    rec['abs'] += meta['content']
                #FFT
                #elif meta['name'] == 'citation_pdf_url':
                #    rec['pdf_url'] = meta['content']
                #pages
                elif meta['name'] == 'DC.description':
                    if re.search('^\d+ p.', meta['content']):
                        rec['pages'] = re.sub(' .*', '', meta['content'])
        rec['autaff'][-1].append(aff)
        #fulltext
        for tr in artpage.find_all('tr', attrs = {'class' : 'ds-table-row'}):
            for a in tr.find_all('a'):                
                if a.has_attr('title') and a.has_attr('href'):
                    restricted = False
                    for img in tr.find_all('img', attrs = {'class' : 'restrict-icon'}):
                        restrictet = True
                    if restricted:
                        print '  restricted!'
                    else:
                        rec['pdf_url'] = 'https://ideals.illinois.edu' + a['href']
        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                if 'pdf_url' in rec.keys():
                    rec['FFT'] = rec['pdf_url']
        #upload PDF at least hidden
        if not 'FFT' in rec.keys() and 'pdf_url' in rec.keys():
            rec['hidden'] = rec['pdf_url']
        print '  ', rec.keys()
    jnlfilename = 'THESES-ILLINOIS-%s_%s' % (stampoftoday, dep)

    #closing of files and printing
    xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
