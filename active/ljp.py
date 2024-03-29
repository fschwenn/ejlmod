# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Lithuanian Journal of Physics
# FS 2020-12-05

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
import time
from bs4 import BeautifulSoup


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

issuesstodo = 3

publisher = 'Lithuanian Academy of Sciences'

#all issues page
url = 'https://www.lmaleidykla.lt/ojs/index.php/physics/issue/archive'
page = BeautifulSoup(urllib2.urlopen(url))

issues = []
#for div in page.find_all('div', attrs = {'id' : 'issues'}):
for div in page.find_all('ul', attrs = {'class' : 'issues_archive'}):
    for a in div.find_all('a')[:issuesstodo]:
        at = a.text.strip()
        vol = re.sub('.*Vol\.? (\d+).*', r'\1', at)
        iss = re.sub('.*No\.? (\d+).*', r'\1', at)
        yr = re.sub('.*\((\d+)\).*', r'\1', at)
        nr = re.sub('.*\/', '', a['href'])
        jnlfilename = 'lithpj%s.%s_%s' % (vol, iss, nr)
        #check whether file already exists
        goahead = True
        for ordner in ['/', '/zu_punkten/', '/zu_punkten/enriched/', '/backup/', '/onhold/']:
            if os.path.isfile(ejldir + ordner + jnlfilename + '.doki'):
                print '    Datei %s exisitiert bereit in %s' % (jnlfilename, ordner)
                goahead = False
        if goahead:
            print 'Will process Lithuanian Journal of Physics, Volume %s, Issue %s' % (vol, iss)
            issues.append((vol, iss, yr, a['href'], jnlfilename))
        

#individual issues
for issue in issues:
    print issue
    time.sleep(2)
    page = BeautifulSoup(urllib2.urlopen(issue[3]), features="lxml")
    jnlfilename = issue[4]
    recs = []    
#    for table in page.find_all('table', attrs = {'class' : 'tocArticle'}):
    for div in page.find_all('div', attrs = {'class' : 'obj_article_summary'}):
        rec = {'jnl' : 'Lith.J.Phys.', 'vol' : issue[0], 'year' : issue[2], 'issue' : issue[1], 'tc' : 'P',
               'keyw' : [], 'autaff' : []}
        for h3 in div.find_all('div', attrs = {'class' : 'title'}):            
            for a in h3.find_all('a'):
                link = a['href']
                rec['tit'] = a.text
                articlepage = BeautifulSoup(urllib2.urlopen(link), features="lxml")
                for meta in articlepage.head.find_all('meta'):
                    if meta.has_attr('name') and meta.has_attr('content'):
                        #keywords
                        if meta['name'] == 'citation_keywords':
                            rec['keyw'] += re.split('; ', meta['content'])
                        #author
                        elif meta['name'] == 'citation_author':
                            rec['autaff'].append([meta['content']])
                        elif meta['name'] == 'citation_author_institution':
                            rec['autaff'][-1].append(meta['content'])
                        #citation_date
                        elif meta['name'] == 'citation_date':
                            rec['data'] = meta['content']
                        #pages
                        elif meta['name'] == 'citation_firstpage':
                            rec['p1'] = meta['content']
                        elif meta['name'] == 'citation_lastpage':
                            rec['p2'] = meta['content']
                        #DOI
                        elif meta['name'] == 'citation_doi':
                            rec['doi'] = meta['content']
                        #abstract
                        elif meta['name'] == 'DC.Description':
                            rec['abs'] = meta['content']
                        #FFT
                        elif meta['name'] == 'citation_pdf_url':
                            rec['FFT'] = meta['content']
                for a in articlepage.body.find_all('a'):
                    if a.has_attr('href'):
                        if re.search('creativecommons.org', a['href']):
                            rec['license'] = {'url' : a['href']}
            recs.append(rec)
            print rec.keys()
    #write xml
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

