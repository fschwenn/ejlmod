# -*- coding: utf-8 -*-
#harvest theses from Universität Erlangen-Nürnberg
#FS: 2019-11-04


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
numofpages = 1

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Erlangen - Nuremberg U.'

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
jnlfilename = 'THESES-ERLANGEN-%s' % (stampoftoday)
for year in [now.year-1, now.year]:
    tocurl = 'https://opus4.kobv.de/opus4-fau/solrsearch/index/search/searchtype/simple/query/%2A%3A%2A/browsing/true/doctypefq/doctoralthesis/start/0/rows/100/institutefq/Naturwissenschaftliche+Fakult%C3%A4t/yearfq/' + str(year)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'results_title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK'}
            rec['link'] = 'https://opus4.kobv.de' + a['href']
            rec['tit'] = a.text.strip()
            recs.append(rec)


            
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['link'])
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
    #license
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #abs
            if meta['name'] in ['DC.Description', 'DC.description']:
                rec['abs'] =  meta['content']
            #keywords
            elif meta['name'] in ['DC.Subject', 'DC.subject']:
                rec['keyw'] =  re.split(', ', meta['content'])
            #URN
            elif meta['name'] in ['DC.Identifier', 'DC.identifier']:
                if re.search('^urn:nbn', meta['content']):
                    rec['urn'] =  meta['content']
            #license
            elif meta['name'] in ['DC.Rights', 'DC.rights']:
                url = re.sub('\/deed.de', '', meta['content'])
                if re.search('creativecommons', url):
                    rec['license'] = {'url' : url}
                    #PDF
                    for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                        rec['FFT'] = meta2['content']
    #upload PDF at least hidden
    if not 'FFT' in rec.keys():
        for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
            rec['hidden'] = meta2['content']
    for table in artpage.body.find_all('table', attrs = {'class' : 'frontdoordata'}):
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                tdt = td.text.strip()
                #Supervisor
                if tht == 'Advisor:':
                    rec['supervisor'] = [[tdt, 'Erlangen - Nuremberg U.']]
                #number of pages
                elif tht == 'Pagenumber:':
                    if re.search('^\d+$', tdt):
                        rec['pages'] = tdt
                #year
                elif tht == 'Year of Completion:':
                    rec['year'] = tdt
                #Language
                elif tht == 'Language:':
                    if tdt == 'German':
                        rec['language'] = 'german'
                        #translated title
                        for h3 in artpage.body.find_all('h3', attrs = {'class' : 'titlemain'}):
                            rec['transtit'] = h3.text.strip()
                #author (becaus of ORCID)
                elif tht == 'Author:':
                    orcid = False
                    for a in td.find_all('a', attrs = {'class' : 'orcid-link'}):
                        orcid = re.sub('.*\/', 'ORCID:', a['href'])
                        a.replace_with('')
                    tdt = td.text.strip()
                    if orcid: 
                        rec['autaff'] = [[ tdt, orcid, 'Erlangen - Nuremberg U.']]
                    else:
                        rec['autaff'] = [[ tdt, 'Erlangen - Nuremberg U.']]
                #date
                elif tht == 'Release Date:':
                    rec['date'] = tdt        
    print '  ', rec.keys()






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
    
