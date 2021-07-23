# -*- coding: utf-8 -*-
#harvest theses from Bochum
#FS: 2021-02-09

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

publisher = 'Ruhr U., Bochum (main)'
jnlfilename = 'THESES-BOCHUM-%s' % (stampoftoday)

rpp = 100
pages = 3

boring = ['Literatur / Englische Literatur Amerikas', 'Philosophie und Psychologie / Philosophie',
          'Philosophie und Psychologie / Psychologie', 'Allgemeines, Informatik, Informationswissenschaft / Informatik',
          'Naturwissenschaften und Mathematik / Biowissenschaften, Biologie, Biochemie',
          'Naturwissenschaften und Mathematik / Chemie, Kristallographie, Mineralogie',
          'Naturwissenschaften und Mathematik / Geowissenschaften, Geologie', 'Religion / Bibel',
          'Allgemeines, Informatik, Informationswissenschaft / Nachrichtenmedien, Journalismus, Verlagswesen',
          'Naturwissenschaften und Mathematik / Pflanzen (Botanik)',
          'Naturwissenschaften und Mathematik / Tiere (Zoologie)',
          'Technik, Medizin, angewandte Wissenschaften / Industrielle und handwerkliche Fertigung',
          'Technik, Medizin, angewandte Wissenschaften',
          'Technik, Medizin, angewandte Wissenschaften / Technische Chemie']
hdr = {'User-Agent' : 'Magic Browser'}

prerecs = []
for page in range(pages):
    tocurl = 'https://hss-opus.ub.ruhr-uni-bochum.de/opus4/solrsearch/index/search/searchtype/all/start/' + str(rpp*page) + '/rows/' + str(rpp) + '/doctypefq/doctoralthesis/sortfield/year/sortorder/desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'class' : 'result_box'}):
        for div2 in div.find_all('div', attrs = {'class' : 'results_title'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
            for a in div2.find_all('a'):
                rec['artlink'] = 'https://hss-opus.ub.ruhr-uni-bochum.de' + a['href']
                prerecs.append(rec)
    time.sleep(10)

i = 0
recs= []
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
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
    for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'DC.Creator':
                    rec['autaff'] = [[ meta['content'] ]]
                #URN
                elif meta['name'] == 'DC.Identifier':
                    if re.search('^urn:', meta['content']):
                        rec['urn'] = meta['content']
                #title
                elif meta['name'] == 'DC.title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'citation_date':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.Subject':
                    for keyw in re.split(' *; *', meta['content']):
                        if not keyw in rec['keyw']:
                            rec['keyw'].append(kw2)
                #abstract
                elif meta['name'] == 'DC.Description':
                    if re.search(' the ', meta['content']):
                        rec['abs'] = meta['content']
                    else:
                        rec['abs_de'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['citation_pdf_url'] = meta['content']
                #Rights
                elif meta['name'] == 'DC.rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['license'] = {'url' : meta['content']}
    for table in artpage.find_all('table', attrs = {'class' : 'result-data'}):
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                #author
                if tht == 'Author:':
                    for a in td.find_all('a', attrs = {'class' : 'orcid-link'}):
                        rec['autaff'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                    for a in td.find_all('a', attrs = {'class' : 'gnd-link'}):
                        gndlink = a['href']
                #URN
                elif tht == 'URN:':
                    rec['urn'] = td.text.strip()
                #DOI
                elif tht == 'DOI:':
                    rec['doi'] = re.sub('.*doi.org\/', '', td.text.strip())
                #supervisor
                elif tht == 'Referee:':
                    for a in td.find_all('a'):
                        if re.search('opus4.solrsearch', a['href']):
                            rec['supervisor'].append([a.text.strip()])
                        elif re.search('orcid.org', a['href']):
                            rec['supervisor'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                        elif re.search('nv.info.gnd', a['href']):
                            gnd = a['href']
                #language
                elif tht == 'Language:':
                    if td.text.strip() == 'German':
                        rec['language'] = 'German'
                #aff
                elif tht == 'Granting Institution:':
                    rec['autaff'][-1].append('%s, Bochum, Germany' % (td.text.strip()))
                #Dewey
                elif tht == 'Dewey Decimal Classification:':
                    rec['note'].append(td.text.strip())
                    if td.text.strip() in boring:
                        keepit = False
                        print '  skip', td.text.strip()
                    elif re.search('(K.nste |Literatur|Geografie|Sozialw|Sprache|Religion|Medizin)', td.text):
                        keepit = False
                        print '  skip'
    #abstract
    if not 'abs' in rec.keys() and 'abs_de' in rec.keys():
        rec['abs'] = rec['abs_de']
    #fulltext
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    if keepit:
        recs.append(rec)
        print '  ', rec.keys()

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
