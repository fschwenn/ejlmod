# -*- coding: utf-8 -*-
#harvest theses from TEL
#FS: 2019-11-11

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
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

if now.month <= 8:
    years = [now.year-1, now.year]
else:
    years = [now.year]

#which domains (topics) should be checked
subdomains = ["stat.ml", "stat.ap", "stat.co",
              "phys.phys.phys-atom-ph", "phys.phys.phys-data-an", "phys.phys.phys-plasm-ph",
              "phys.phys.phys-ins-det", "phys.phys.phys-comp-ph", "phys.phys.phys-acc-ph",
              "phys.cond.cm-sm", "phys.cond.cm-msqhe", "phys.cond.cm-sce",
              "phys.astr.co", "phys.astr.im", "phys.astr.he", "phys.astr.ga",
              "phys.hexp", "phys.nucl", "phys.mphy", "phys.nexp", "phys.qphy",
              "phys.hthe", "phys.hphe", "phys.grqc", "phys.hlat",
              "math.math-ap", "math.math-pr", "math.math-ag", "math.math-co", "math.math-dg",
              "math.math-nt", "math.math-at", "math.math-rt", "math.math-ca", "math.math-gt",
              "math.math-oa", "math.math-sg", "math.math-qa", "math.math-ra",
              "info.info-ni", "info.info-se", "info.info-dc", "info.info-cv", "info.info-lg",
              "info.info-it", "info.info-sc", "info.info-ms", "info.info-dl"]
domains = {}
for subdom in subdomains:
    dom = re.sub('\..*', '', subdom)
    if dom in domains.keys():
        domains[dom].append(subdom)
    else:
        domains[dom] = [subdom]

#avoid duplicates as some theses are in more than one domain
doiliste = {}

#check theses already done before
retel = re.compile('THESES.TEL.*doki$')
reurl = re.compile('^3URL.*\/(tel.*);')
telnrs = []
for ordner in [ejldir, ejldir+'/onhold', ejldir+'/zu_punkten', ejldir+'/zu_punkten/enriched',
               ejldir+'/backup', ejldir+'/backup/'+str(now.year-1)]:
    for datei in os.listdir(ordner):
        if retel.search(datei):
            print ordner, datei
            inf = open(os.path.join(ordner, datei), 'r')
            for line in inf.readlines():
                if reurl.search(line):
                    telnrs.append(reurl.sub(r'\1', line.strip()))
print '%i tel identifiers to be ignored, e.g.' % (len(telnrs)), telnrs[:5]


publisher = 'TEL'
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
for year in years:
    for dom in domains.keys():
        print '==={ %i }==={ %s }===' % (year, dom)
        prerecs = []
        for subdom in domains[dom]:
            tocurl = 'https://tel.archives-ouvertes.fr/search/index/?q=%2A&domain_t=' + subdom + '&producedDateY_i=' + str(year) + '&rows=100'
            print '           ---{ %s : %s }---' % (subdom, tocurl)
            req = urllib2.Request(tocurl, headers=hdr)
            tocpages = [BeautifulSoup(urllib2.urlopen(req))]
            time.sleep(5)
            for div in tocpages[0].body.find_all('div', attrs = {'class' : 'col-md-3'}):
                divt = re.sub('[\n\t\r]', '', div.text.strip())
                try:
                    results = int(re.sub('.*?(\d+)..?result.*', r'\1', divt))
                    print '           expecting %i results' % (results)
                    for j in range((results-1)/100):
                        ptocurl = tocurl + '&page=' + str(j+2)
                        print '           ---{ %s : %s }---' % (subdom, ptocurl)
                        req = urllib2.Request(ptocurl, headers=hdr)
                        tocpages.append(BeautifulSoup(urllib2.urlopen(req)))
                        time.sleep(5)
                except:
                    print '           could not extract expected number of results'
            for tocpage in tocpages:
                divs = tocpage.body.find_all('div', attrs = {'class' : 'media-body'})
                for div in divs:
                    for a in div.find_all('a', attrs = {'data-toggle' : 'tooltip'}):
                        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'year' : str(year), 'keyw' : [], 
                               'note' : [ subdom ], 'rn' : [], 'refs' : []}
                        rec['link'] = 'https://tel.archives-ouvertes.fr' + a['href']
                        rec['tit'] = a.text.strip()
                    if a['href'][1:] in telnrs:
                        print '           skip %s' % (a['href'][1:])
                    else:
                        prerecs.append(rec)
                print '           %3i theses in %s (%i in %s)' % (len(divs), subdom, len(prerecs), dom)
        j = 0
        recs = []
        for rec in prerecs:
            j += 1
            print '---{ %i.%s }---{ %i/%i (%i) }---{ %s }------' % (year, dom, j, len(prerecs), len(recs), rec['link'])
            try:
                req = urllib2.Request(rec['link'])
                artpage = BeautifulSoup(urllib2.urlopen(req))
                time.sleep(5)
            except:
                print 'wait 5 minutes'
                time.sleep(300)
                req = urllib2.Request(rec['link'])
                artpage = BeautifulSoup(urllib2.urlopen(req))
                time.sleep(10)
            for meta in artpage.find_all('meta'):
                if meta.has_attr('name'):
                    #language
                    if meta['name'] == 'citation_language':
                        if meta['content'] =='fr':
                            rec['language'] = 'french'
                    #report number
                    elif meta['name'] == 'DC.identifier':
                        if re.search('^tel', meta['content']):
                            rec['rn'].append(meta['content'])
                            rec['doi'] = '20.2000/TEL/' + meta['content']
                    #author
                    elif meta['name'] == 'citation_author':
                        rec['autaff'] = [[meta['content']]]
                    #affiliation
                    elif meta['name'] == 'citation_author_institution':
                        rec['autaff'][-1].append(meta['content'] + ', France')
                    #date
                    elif meta['name'] == 'DC.issued':
                        rec['date'] = meta['content']
                    #FFT
                    elif meta['name'] == 'citation_pdf_url':
                        rec['FFT'] = meta['content']
            for div in artpage.body.find_all('div', attrs = {'class' : 'content-en'}):
                #abstract
                for div2 in div.find_all('div', attrs = {'class' : 'abstract-content'}):
                    abs = div2.text.strip()
                    rec['abs'] = re.sub('^Abstract *: *', '', abs)
                #keywords
                for div2 in div.find_all('div', attrs = {'class' : 'keyword-content'}):
                    for a in div2.find_all('a'):
                        rec['keyw'].append(a.text.strip())
            #French National Number (NNT)
            for div in artpage.body.find_all('div', attrs = {'class' : 'ref-biblio'}):
                for a in div.find_all('a'):
                    if a.has_attr('href'):
                        if re.search('www.theses.fr', a['href']):
                            rec['rn'].append(re.sub('.*\/', '', a['href']))
            if not 'doi' in rec.keys():
                rec['doi'] = '20.2000/TEL/' + re.sub('.*\/', '', rec['link'])
            if rec['doi'] in doiliste.keys():
                print '___%s_already_via_different_domain_%s___' % (rec['doi'], doiliste[rec['doi']])
            else:
                doiliste[rec['doi']] = subdom
                #references
                for div in artpage.body.find_all('div', attrs = {'class' : 'references'}):
                    try:
                        req = urllib2.Request(rec['link'] + '/html_references')
                        refpage = BeautifulSoup(urllib2.urlopen(req))
                        time.sleep(5)
                    except:
                        print 'wait 5 minutes to get refernces'
                        time.sleep(300)
                        req = urllib2.Request(rec['link'] + '/html_references')
                        refpage = BeautifulSoup(urllib2.urlopen(req))
                        time.sleep(10)
                    for p in refpage.body.find_all('p'):
                        rec['refs'].append([('x', p.text.strip())])
                print '    ' + ', '.join( ['%s (%i)' % (k, len(rec[k])) for k in rec.keys()] ) + '\n'
                recs.append(rec)            
        jnlfilename = 'THESES-TEL-%s_%s_%i' % (stampoftoday, dom, year)
        print '===[ write %i records to %s ]===' % (len(recs), jnlfilename)
        #closing of files and printing
        if recs:
            xmlf = os.path.join(xmldir, jnlfilename+'.xml')
            xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
            ejlmod2.writeXML(recs, xmlfile,publisher)
            xmlfile.close()
            #retrival
            retfiles_text = open(retfiles_path, "r").read()
            line = jnlfilename+'.xml'+ "\n"
            if not line in retfiles_text: 
                retfiles = open(retfiles_path, "a")
                retfiles.write(line)
                retfiles.close()
            

