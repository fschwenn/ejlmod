# -*- coding: utf-8 -*-
#harvest theses from U. Geneva
#FS: 2020-11-13

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

publisher = 'U. Geneva (main)'

rpp = 50
startyear = now.year-1
pages = 2
departments = [(242, 'Departement de physique nucleaire et corpusculaire', 'Geneva U.'),
               (369, 'Departement de physique theorique', 'Geneva U., Dept. Theor. Phys.'),
               (10103, 'Section de mathematiques', publisher),
               (10107, 'Departement dastronome', publisher)]
jnlfilename = 'THESES-GENEVE-%s' % (stampoftoday)


hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for (cn, dep, aff) in departments:
    print '======{ %s }===' % (dep)
    year = now.year
    section = False
    for page in range(pages):
        tocurl = 'https://archive-ouverte.unige.ch/structures/view/page:%i?cn=%i' % (page+1, cn)
        print '   ==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for div in tocpage.body.find_all('div', attrs = {'class' : 'documents_list_year'}):
            for child in div.children:
                try:
                    child.name
                except:
                    continue
                if child.name == 'h3':
                    year = int(child.text.strip())
                    print '     ', year
                elif child.name == 'h4':
                    section = child.text.strip()
                    print '       ', section
                elif child.name == 'table':
                    if year >= startyear and section == 'Doctoral Thesis':
                        for td in child.find_all('td'):
                            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [],
                                   'affiliation' : aff, 'note' : [ dep ]}
                            for a in td.find_all('a'):
                                if a.has_attr('href') and re.search('unige:\d+', a['href']):
                                    rec['tit'] = a.text.strip()
                                    rec['artlink'] = 'https://archive-ouverte.unige.ch' + a['href']
                                    recs.append(rec)
        time.sleep(5)
        
i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
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
            #date
            if meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], rec['affiliation'] ]] 
            #doi
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #pdf
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'fre':
                    rec['language'] = 'french'
    for tr in artpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'property'}):
            #supervisor                
            if td.text.strip() == 'Director':
                for span in tr.find_all('span', attrs = {'class' : 'unige_author'}):
                    rec['supervisor'].append([span.text.strip()])
            #URN
            elif td.text.strip() == 'Identifiers':
                for div in tr.find_all('div'):
                    if re.search('urn.nbn.ch', div.text):
                        rec['urn'] = re.sub('.*?(urn.nbn.ch.*)', r'\1', div.text.strip())
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'citation_pdf_url' in rec.keys():
                rec['FFT'] = rec['citation_pdf_url']
    #hiddenPDF
    if not 'license' in rec.keys() and 'citation_pdf_url' in rec.keys():
        rec['hidden'] = rec['citation_pdf_url']
    print '  ', rec.keys()



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
