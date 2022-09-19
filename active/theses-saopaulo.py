# -*- coding: utf-8 -*-
#harvest theses from Sao Paulo U.
#FS: 2019-10-29


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
pagestocheck = 2

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Sao Paulo (main) '

hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}
for year in [now.year-1, now.year]:
#for year in [now.year-2, now.year-3, now.year-4, now.year-5, now.year-6, now.year-7, now.year-8, now.year-9]:
    recs = []
    print '==={ %i }===' % (year)
    tocurl = 'https://teses.usp.br/index.php?option=com_jumi&fileid=19&Itemid=87&lang=en&g=4&b0=Physics&c0=c&o0=AND&b1=%i&c1=a&o1=AND&pagina=' % (year)
    print '---{ %i }---{ %s%i }---' % (1, tocurl, 1)
    tocfilename = '/tmp/theses-saopaulo-%s_%i_1' % (stampoftoday, year)
    if not os.path.isfile(tocfilename):
        os.system('wget -T 300 -t 3 -q  -O %s "%s%i"' % (tocfilename, tocurl, 1)) 
    inf = open(tocfilename, 'r')
    tocpages = [BeautifulSoup(''.join(inf.readlines()))]
    inf.close()
    #check how many pages per year there are
    for div in tocpages[0].body.find_all('div', attrs = {'class' : 'dadosLinha'}):
        divt = div.text.strip()
        if re.search('Displaying.*of \d', divt):
            numofpages = int(re.sub('.*of (\d+).*', r'\1', divt))
    #get TOC pages
    for i in range(numofpages-1):
        print '---{ %i/%i }---{ %s%i }---' % (i+2, numofpages, tocurl, i+2)
        tocfilename = '/tmp/theses-saopaulo-%s_%i_%i' % (stampoftoday, year, i+2)
        if not os.path.isfile(tocfilename):
            os.system('wget -T 300 -t 3 -q  -O %s "%s%i"' % (tocfilename, tocurl, i+2)) 
            time.sleep(10)
        inf = open(tocfilename, 'r')
        tocpages.append(BeautifulSoup(''.join(inf.readlines())))
        inf.close()
    #check TOC pages for links
    for tocpage in tocpages:
        for div in tocpage.body.find_all('div', attrs = {'class' : 'dadosDocNome'}):
            for a in div.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : []}
                rec['link'] = re.sub('(.*)\/.*', r'\1', a['href'])
                recs.append(rec)
    #checl individual theses
    i = 0
    for rec in recs:
        i += 1
        print '---{ %i }---{ %i/%i }---{ %s }------' % (year, i, len(recs), rec['link'])
        artfilename = '/tmp/theses-saopaulo-%s_%i_art%04i' % (stampoftoday, year, i)
        if not os.path.isfile(artfilename):
            os.system('wget -T 300 -t 3 -q   -O %s "%s"' % (artfilename, rec['link'])) 
            time.sleep(20)
        inf = open(artfilename, 'r')
        artpage = BeautifulSoup(''.join(inf.readlines()))
        inf.close()        
        #language and title
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'DC.language'}):
            lang = meta['content']
            if lang == 'por':
                rec['language'] = 'portuguese'
                for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'DC.title'}):
                    if meta2['xml:lang'] == 'en':
                        rec['transtit'] = meta2['content']
                    else:
                        rec['tit'] = meta2['content']
            else:
                for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'DC.title'}):
                    if meta2['xml:lang'] == 'en':
                        rec['tit'] = meta2['content']
        #other metadata
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                #author
                if meta['name'] == 'DC.creator':
                    rec['autaff'] = [[ meta['content'] ]]
                #aff
                elif meta['name'] == 'citation_dissertation_institution':
                    rec['autaff'][-1].append(meta['content'] + ', Brazil')
                #date
                elif meta['name'] == 'citation_publication_date':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    if meta['xml:lang'] == 'en':
                        rec['keyw'].append(meta['content'])
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    if meta['xml:lang'] == 'en':
                        rec['abs'] = meta['content']
                #supervisor
                elif meta['name'] == 'DC.contributor':
                    rec['supervisor'] = [[meta['content'], 'U. Sao Paulo (main)']]
                #DOI
                elif meta['name'] == 'DC.identifier':
                    if re.search('10.11606', meta['content']):
                        rec['doi'] = re.sub('.*(10\.11606.*)', r'\1', meta['content'])
                #upload PDF at least hidden
                elif meta['name'] == 'citation_pdf_url':
                    rec['hidden'] = meta['content']
        if not 'doi' in rec.keys():
            rec['doi'] = '20.2000/' + re.sub('\W', '', rec['link'][11:])
        rec['autaff'][-1].append('U. Sao Paulo (main)')
        print '    ', rec.keys()
    jnlfilename = 'THESES-SAOPAULO-%s_%i' % (stampoftoday, year)    
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


