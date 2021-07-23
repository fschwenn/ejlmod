# -*- coding: utf-8 -*-
#harvest theses from Lund
#FS: 2020-08-15

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
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Lund U. (main)'

jnlfilename = 'THESES-LUND-%s' % (stampoftoday)
rpp = 20
pages = 1

departments = [('Nuclear Physics', 'Lund U. (main)', 100062),
               ('Atomic Physics', 'Lund U. (main)', 1000622),
               ('Mathematical Physics', 'Lund U. (main)', 1000630),
               ('Particle Physics', 'Lund U.', 1000632),
               ('Solid State', 'Lund U. (main)', 1000623),
               ('Lund Observatory', 'Lund Observ.', 1000643),
	       ('Mathematics', 'Lund U. (main)', 1000665),	  
               ('Theoretical Particle Physics', 'Lund U., Dept. Theor. Phys.', 1000645)]

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for (department, aff, dnr) in departments:
    for page in range(pages):
        tocurl = 'https://lup.lub.lu.se/search/publication?limit=%i&q=documentType+exact+thesis&q=department+exact+v%i&sort=year.desc&start=%i' % (rpp, dnr, rpp*page)
        print '---{ %s }---{ %i/%i }---{ %s }---' % (department, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for li in tocpage.body.find_all('li', attrs = {'class' : 'unmarked-record'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [department],
                   'supervisor' : []}
            for span in li.find_all('span', attrs = {'class' : 'title'}):
                for a in span.find_all('a'):
                    rec['link'] = a['href']
                    rec['doi'] = '20.2000/LUND/' + re.sub('.*\/', '', a['href'])
                    rec['tit'] = a.text.strip()
                    rec['aff'] = aff
            recs.append(rec)
        time.sleep(3)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
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
                rec['autaff'] = [[ meta['content'] ]]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'dc.subject':
                rec['keyw'].append(meta['content'])
            #abstract
            elif meta['name'] == 'dc.description':
                rec['abs'] = meta['content']
            #language
            elif meta['name'] == 'dc.language':
                if meta['content'] != 'eng':
                    if meta['content']== 'swe':
                        rec['lanuage'] = 'swedish'
                    else:
                        rec['lanuage'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #ISBN
            elif meta['name'] == 'citation_isbn':
                if 'isbns' in rec.keys():
                    rec['isbns'].append([('a', re.sub('\-', '', meta['content']))])
                else:
                    rec['isbns'] = [[('a', re.sub('\-', '', meta['content']))]]
    for dl in artpage.body.find_all('dl'):
        for child in dl.children:
            try:
                child.name
            except:
                continue
            if child.name == 'dt':
                dtt = child.text
            elif child.name == 'dd':
                #author's ORCID
                if dtt == 'author':
                    for a in child.find_all('a'):
                        if a.has_attr('href') and re.search('orcid.org\/', a['href']):
                            rec['autaff'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                #supervisor
                elif dtt == 'supervisor':
                    for li in child.find_all('li'):
                        for span in li.find_all('span', attrs = {'class' : 'fn'}):
                            rec['supervisor'].append([span.text.strip()])
                            for a in span.find_all('a'):
                                if a.has_attr('href') and re.search('orcid.org\/', a['href']):
                                    rec['supervisor'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                #pages
                elif dtt == 'pages':
                    if re.search('\d\d', child.text):
                        rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', child.text.strip())
    #author's affiliation
    rec['autaff'][-1].append(rec['aff'])
    print rec.keys()

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
