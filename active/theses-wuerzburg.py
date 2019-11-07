# -*- coding: utf-8 -*-
#harvest theses from U. Wurzburg (main) 
#FS: 2019-11-06


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

publisher = 'U. Wurzburg (main)'

hdr = {'User-Agent' : 'Magic Browser'}
repacs = re.compile('.*(\d\d\.\d\d\...).*')
for inst in ['Physikalisches+Institut', 'Institut+f%C3%BCr+Theoretische+Physik+und+Astrophysik']:
    recs = []
    jnlfilename = 'THESES-WURZBURG-%s-%s' % (stampoftoday, re.sub('\W', '', inst))
    for year in [now.year, now.year-1]:
        tocurl = 'https://opus.bibliothek.uni-wuerzburg.de/solrsearch/index/search/searchtype/simple/query/%2A%3A%2A/browsing/true/doctypefq/doctoralthesis/start/0/rows/100/institutefq/' + inst + '/yearfq/' + str(year)
        print '---{ %s }---{ %i }---{ %s }---' % (inst, year, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(5)
        for div in tocpage.body.find_all('div', attrs = {'class' : 'result_box'}):
            for div2 in div.find_all('div', attrs = {'class' : 'results_title'}):
                for a in div2.find_all('a'):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'pacs' : []}
                    rec['link'] = 'https://opus.bibliothek.uni-wuerzburg.de' + a['href']
                    rec['tit'] = a.text.strip()
                    rec['year'] = str(year)
                    recs.append(rec)
            
    i = 0
    for rec in recs:
        i += 1
        print '---{ %i/%i }---{ %s }------{ %s }---' % (i, len(recs), inst, rec['link'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
            time.sleep(10)
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
                #abstract
                elif meta['name'] == 'description':
                    rec['abs'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    rec['keyw'].append(meta['content'])
                #urn
                elif meta['name'] == 'DC.Identifier':
                    if re.search('^urn:', meta['content']):
                        rec['urn'] = meta['content']
                #license
                elif meta['name'] == 'DC.rights':
                    if re.search('reativecommons.org', meta['content']):
                        rec['license'] = {'url' : re.sub('.deed.de', '', meta['content'])}
                        for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                            rec['FFT'] = meta2['content']
        for tr in artpage.body.find_all('tr'):
            for th in tr.find_all('th'):
                #PACS
                if re.search('PACS..lassification', th.text.strip()):
                    for td in tr.find_all('td'):
                        for pacspart in re.split('\/' ,td.text.strip()):
                            if repacs.search(pacspart):
                                pacs = repacs.sub(r'\1', pacspart)
                                if not re.search('00', pacs):
                                    rec['pacs'].append(pacs)
                #Language
                if re.search('Language', th.text.strip()):
                    for td in tr.find_all('td'):
                        if re.search('erman', td.text.strip()):
                            rec['language'] = 'german'
                            #translated title
                            for h3 in artpage.body.find_all('h3', attrs = {'class' : 'titlemain', 'lang' : 'en'}):
                                rec['transtit'] = h3.text.strip()
        print rec.keys()

    #closing of files and printing
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writeXML(recs, xmlfile, publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
    
