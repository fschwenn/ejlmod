# -*- coding: utf-8 -*-
#harvest theses from Louvain 
#FS: 2020-08-26

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d_boring' % (now.year, now.month, now.day)

publisher = 'Louvain U.'
                                                                                
boringdeps = ['SSH/IACS', 'SSH/ILC', 'SSH/ILC/PCOM', 'SSH/ILC/PLIN', 'SSH/INCA',
              'SSH/IPSY', 'SSH/JURI', 'SSH/JURI/PJPR', 'SSH/JURI/PJPU',
              'SSH/LIDAM/CORE', 'SSH/LIDAM/IRES', 'SSH/LouRIM', 'SSH/RSCS',
              'SSH/SPLE', 'SSS/DDUV/CELL', 'SSS/DDUV', 'SSS/DDUV/LPAD',
              'SSS/DDUV/SIGN', 'SSS/IONS/CEMO', 'SSS/IONS/COSY', 'SSS/IONS',
              'SSS/IREC/EPID', 'SSS/IREC/FATH', 'SSS/IREC/GAEN', 'SSS/IREC/GYNE',
              'SSS/IREC/IMAG', 'SSS/IREC', 'SSS/IREC/LTAP', 'SSS/IREC/MIRO',
              'SSS/IRSS', 'SSS/LDRI', 'SST/ELI', 'SST/ELI/ELIA', 'SST/ELI/ELIB',
              'SST/ELI/ELIC', 'SST/ELI/ELIE', 'SST/IMCN/MODL', 'SST/IMMC/IMAP',
              'SST/LIBST']
#boringdeps = []

hdr = {'User-Agent' : 'Magic Browser'}
for year in [now.year, now.year-1]:
#for year in [now.year, now.year-1, now.year-2, now.year-3, now.year-4, now.year-5, now.year-6, now.year-7, now.year-8, now.year-9, now.year-10]:
    prerecs = []
    jnlfilename = 'THESES-LOUVAIN-%s_%i' % (stampoftoday, year)
    tocurl = 'https://dial.uclouvain.be/pr/boreal/en/search/site/%2A%3A%2A?page=1&f%5B0%5D=sm_type%3ATh%C3%A8se%20%28Dissertation%29&f%5B1%5D=sm_date%3A' + str(year) + '&solrsort=ss_date%20desc'
    print '---{ %i }---{ 1 }---{ %s }---' % (year, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpages = [BeautifulSoup(urllib2.urlopen(req))]
    for div in tocpages[0].body.find_all('div', attrs = {'class' : 'result-label'}):
        numofrecs = int(re.sub('.*of *(\d+).*', r'\1', div.text.strip()))
        numofpages = (numofrecs-1) / 25 + 1
    for page in range(numofpages-1):
        tocurl = 'https://dial.uclouvain.be/pr/boreal/en/search/site/%2A%3A%2A?page=' + str(page+2) + '&f%5B0%5D=sm_type%3ATh%C3%A8se%20%28Dissertation%29&f%5B1%5D=sm_date%3A' + str(year) + '&solrsort=ss_date%20desc'
        print '---{ %i }---{ %i/%i }---{ %s }---' % (year, page+2, numofpages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpages.append(BeautifulSoup(urllib2.urlopen(req)))
        time.sleep(5)
    for tocpage in tocpages:
        for div in tocpage.body.find_all('div', attrs = {'class' : 'publication'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'year' : str(year), 'date' : str(year), 'note' : [],
                   'oa' : False, 'ftispdf' : False, 'supervisor' : [], 'keyw' : [], 'departments' : []}
            for a in div.find_all('a', attrs = {'class' : 'cart_update'}):
                rec['link'] = re.sub('.*A', 'https://dial.uclouvain.be/pr/boreal/object/boreal:', a['href'])
            for span in div.find_all('span', attrs = {'class' : 'title'}):
                for a in span.find_all('a'):
                    rec['hdl'] = re.sub('.*net\/', '', a['href'])
                    rec['tit'] = a.text.strip()
                    prerecs.append(rec)

    i = 0
    recs = []
    for rec in prerecs:
        keepit = True
        i += 1
        print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            time.sleep(4)
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
                if meta['name'] == 'citation_author':
                    rec['autaff'] = [[ meta['content'], publisher ]]
        #fulltext
        for div in artpage.body.find_all('div', attrs = {'class' : 'datastream-small'}):
            for li in div.find_all('li'):
                if re.search('Open access', li.text):
                    rec['oa'] = True
                elif re.search('PDF', li.text):
                    rec['ftispdf'] = True
            if rec['oa'] and rec['ftispdf']:
                for a in div.find_all('a'):
                    rec['FFT'] = a['href']
        #abstract
        for p in artpage.body.find_all('p', attrs = {'class' : 'publication-metadata'}):
            rec['abs'] = p.text.strip()
        for table in artpage.body.find_all('table', attrs = {'class' : 'publication-metadata'}):
            for tr in table.find_all('tr'):
                for th in tr.find_all('th'):
                    tht = th.text.strip()
                for td in tr.find_all('td'):
                    #language
                    if tht == 'Language':
                        if td.text.strip()[:3] == 'Fra':
                            rec['language'] = 'French'
                    #supervisor
                    elif tht == 'Promotors':
                        for sv in re.split(' *\| *', td.text.strip()):
                            rec['supervisor'].append([sv])
                    #keywords
                    elif tht == 'Keywords':
                        for a in td.find_all('a'):
                            rec['keyw'].append(a.text.strip())
                    #Department
                    elif tht == 'Affiliations':
                        for a in td.find_all('a'):
                            if re.search('^[A-Z][A-Z]', a.text):
                                dep = re.sub(' .*', '', a.text.strip())
                                if dep in boringdeps:
                                    try:
                                        print '  skip "%s"' % (a.text.strip())
                                    except:
                                        print '  skip "%s"' % (dep)
                                    keepit = False
                                else:
                                    rec['departments'].append(dep)
        if keepit:
            print rec.keys()
            recs.append(rec)

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
    time.sleep(60)
