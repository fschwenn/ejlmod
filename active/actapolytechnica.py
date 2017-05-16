# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Acta Polytechnica (Prague)
# FS 2015-10-13

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


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

issuesstodo = 3

publisher = 'Czech Technical University in Prague'

#all issues page
url = 'https://ojs.cvut.cz/ojs/index.php/ap/issue/archive'
page = BeautifulSoup(urllib2.urlopen(url))

issues = []
for div in page.find_all('div', attrs = {'id' : 'issues'}):
    for a in div.find_all('a')[:issuesstodo]:
        vol = re.sub('.*Vol (\d+).*', r'\1', a.text)
        iss = re.sub('.*No (\d+).*', r'\1', a.text)
        yr = re.sub('.*\((\d+)\).*', r'\1', a.text)
        nr = re.sub('.*\/', '', a['href'])
        jnlfilename = 'actapoly%s.%s_%s' % (vol, iss, nr)
        #check whether file already exists
        goahead = True
        for ordner in ['/', '/zu_punkten/', '/zu_punkten/enriched/', '/backup/', '/onhold/']:
            if os.path.isfile(ejldir + ordner + jnlfilename + '.doki'):
                print '    Datei %s exisitiert bereit in %s' % (jnlfilename, ordner)
                goahead = False
        if goahead:
            print 'Will process Acta Polytechnica (Prague), Volume %s, Issue %s' % (vol, iss)
            issues.append((vol, iss, yr, a['href'], jnlfilename))
        
#issues = [('1', '1', '2014', 'https://ojs.cvut.cz/ojs/index.php/APP/issue/view/415', 'Frascati2013')]


#individual issues
for issue in issues:
    page = BeautifulSoup(urllib2.urlopen(issue[3]))
    jnlfilename = issue[4]
    recs = []
    for table in page.find_all('table', attrs = {'class' : 'tocArticle'}):
        rec = {'jnl' : 'Acta Polytech.', 'vol' : issue[0], 'year' : issue[2], 'issue' : issue[1], 'tc' : 'P'}
        for div in table.find_all('div', attrs = {'class' : 'tocTitle'}):
            for a in div.find_all('a'):
                link = a['href']
                rec['tit'] = a.text
                articlepage = BeautifulSoup(urllib2.urlopen(link))
                for meta in articlepage.head.find_all('meta', attrs = {'name' : 'keywords'}):
                    rec['keyw'] = re.split('; ', meta['content'])
                for meta in articlepage.head.find_all('meta', attrs = {'name' : 'DC.Description'}):
                    rec['abs'] = meta['content']
                for meta in articlepage.head.find_all('meta', attrs = {'name' : 'DC.Rights'}):
                    rec['licence'] = {'url' : meta['content']}
                for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_firstpage'}):
                    rec['p1'] = meta['content']
                for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_lastpage'}):
                    rec['p2'] = meta['content']
                for meta in articlepage.head.find_all('meta', attrs = {'name' : 'DC.Identifier.DOI'}):
                    rec['doi'] = meta['content']
                for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_date'}):
                    rec['date'] = meta['content']
                for meta in articlepage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
                    rec['FFT'] = meta['content']
                rec['autaff'] = []
                autaff = []
                for meta in articlepage.head.find_all('meta'):
                    if meta.has_attr('name') :
                        if meta['name'] == 'citation_author':
                            if len(autaff) > 0:
                                rec['autaff'].append(autaff)
                            autaff = [ meta['content'] ]
                        elif meta['name'] == 'citation_author_institution':
                            autaff.append(meta['content'])
                        
        recs.append(rec)
    #write xml
    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
    ejlmod2.writeXML(recs,xmlfile,publisher)
    xmlfile.close()
    #retrival
    retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
    retfiles_text = open(retfiles_path,"r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()

