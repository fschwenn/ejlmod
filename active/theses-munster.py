# -*- coding: utf-8 -*-
#harvest theses from Munster
#FS: 2021-02-10


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Munster'
jnlfilename = 'THESES-MUNSTER-%s' % (stampoftoday)

pages = 1

boring = []
hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for dep in ['FB+10%3A+Mathematik+und+Informatik', 'FB+11%3A+Physik']:
    for page in range(pages):
        tocurl = 'https://miami.uni-muenster.de/Search/Results?sort=year&page=' + str(page+1) + '&filter%5B%5D=ulb_DocumentType_facet%3A%22Dissertation%2FHabilitation%22&filter%5B%5D=ulb_affiliation_facet%3A%22' + dep + '%22&type=AllFields'
        print '==={ %s : %i/%i }==={ %s }===' % (dep, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")    
        for div in tocpage.body.find_all('div', attrs = {'class' : 'media'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [dep[9:]], 'supervisor' : []}
            for a in div.find_all('a', attrs = {'class' : ['title', 'getFull']}):
                rec['artlink'] = 'https://miami.uni-muenster.de' + a['href']
                rec['tit'] = a.text.strip()
                recs.append(rec)
        time.sleep(10)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for table in artpage.find_all('table'):
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                #author
                if tht in ['Author:', 'Verfasser:']:
                    for a in td.find_all('a'):
                        if re.search('GND', a.text):
                            gndlink = a['href']
                            a.decompose()
                        elif re.search('VIAF', a.text):
                            a.decompose()
                    for a in td.find_all('a'):
                        rec['autaff'] = [[ a.text.strip(), publisher ]]
                #supervisor
                elif tht in ['Further contributors:', 'Weitere Beteiligte:']:
                    for a in td.find_all('a'):
                        if re.search('GND', a.text):
                            gndlink = a['href']
                            a.decompose()
                        elif re.search('VIAF', a.text):
                            a.decompose()
                    for a in td.find_all('a'):
                        rec['supervisor'].append([a.text.strip()])
                #date
                elif tht in ['Publication date:', 'Erscheinungsdatum:']:
                    rec['date'] = td.text.strip()
                #keywords
                elif tht == 'Subjects:' or re.search('^Schlagw', tht):
                    rec['keyw'] += re.split('; ', td.text.strip())
                #URN
                elif tht == 'URN:':
                    rec['urn'] = td.text.strip()
                elif tht == 'Permalink:':
                    rec['link'] = td.text.strip()
                #license
                elif tht in ['License:', 'Lizenz:']:
                    for a in td.find_all('a'):
                        rec['license'] = {'url' : a['href']}
                #PDF
                elif tht in ['Digital documents:', 'Onlinezugriff:']:
                    for a in td.find_all('a'):
                        rec['citation_pdf_url'] = a['href']
                #language
                elif tht in ['Language:', 'Sprache']:
                    if td.text.strip() == 'German':
                        rec['language'] = 'German'
    #abstract
    for p in artpage.find_all('p', attrs = {'class' : 'summary'}):
        if re.search(' the ', p.text.strip()):
            rec['abs'] = p.text.strip()
        else:
            rec['abs_de'] = p.text.strip()
    if not 'abs' in rec.keys() and 'abs_de' in rec.keys():
        rec['abs'] = rec['abs_de']
    #fulltext
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys() and re.search('creativecommo', rec['license']['url']):
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    print '  ', rec.keys()

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
