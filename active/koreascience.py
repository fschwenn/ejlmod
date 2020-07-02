# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Korea Science
# FS 2019-04-03

import os
import ejlmod2
import re
import sys
import unicodedata
import string
import codecs 
import urllib2
import urlparse
from bs4 import BeautifulSoup
import datetime
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'


journals = {'jkas' : {'issn'      : '1225-4614',
                      'publisher' : 'The Korean Astronomical Society',
                      'jnl'       : 'J.Korean Astron.Soc.',
                      'kojic'     : 'CMHHBA'},
            'jass' : {'issn'      : '2093-5587',
                      'publisher' : 'The Korean Space Science Society',
                      'jnl'       : 'J.Astron.Space Sci.',
                      'kojic'     : 'OJOOBS',
                      'licence'   : {'statement' : 'CC-BY-NC-3.0'}},
            'jkms' : {'issn'      : '0304-9914',
                      'publisher' : 'The Korean Mathematical Society',
                      'jnl'       : 'J.Korean Math.Soc.',
                      'kojic'     : 'DBSHBB'}}



        
journal = sys.argv[1]
vol = sys.argv[2]
iss = sys.argv[3]
if not journals.has_key(journal):
    print 'do not know journal "%s"' % (journal)
    sys.exit(0)
publisher = journals[journal]['publisher']

jnlfilename = '%s%s.%s' % (journal, vol, iss)

#starturl = 'http://koreascience.or.kr/journal/JournalIssueList.jsp?kojic=%s&volno=%s&issno=%s' % (journals[journal]['kojic'], vol, iss)
starturl = 'http://koreascience.or.kr/journal/%s/v%sn%s.page' % (journals[journal]['kojic'], vol, iss)
print starturl
#tocpage = BeautifulSoup(urllib2.urlopen(starturl, timeout=300))
if not os.path.isfile('/tmp/%s.toc' % (jnlfilename)):
    os.system('lynx -source "%s" > /tmp/%s.toc' % (starturl, jnlfilename))
tocf = open('/tmp/%s.toc' % (jnlfilename), 'r')
tocpage = BeautifulSoup(''.join(tocf.readlines()))
tocf.close()
recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'clear'}):
    rec = {'jnl' : journals[journal]['jnl'], 'vol' : vol, 'issue' : iss, 
           'tc' : 'P', 'auts' : [], 'keyw' : [], 'refs' : []}
    if len(sys.argv) > 4:
        rec['tc'] = 'C'
        rec['cnum'] = sys.argv[4]
    for a in div.find_all('a'):
        #if a.has_attr('href') and re.search('society', a['href']):
        if a.has_attr('href'):
            if re.search('doi.org', a['href']):
                #rec['artlink'] = re.sub('.*=', 'http://koreascience.or.kr/article/', a['href']) + '.page'
                rec['artlink'] = a['href']
            elif re.search('pdf$', a['href']):
                if 'licence' in journals[journal].keys(): 
                    rec['FFT'] = a['href']
    recs.append(rec)


i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    if not os.path.isfile('/tmp/%s.%i' % (jnlfilename, i)):
        time.sleep(3)
        os.system('lynx -source "%s" > /tmp/%s.%i' % (rec['artlink'], jnlfilename, i))
    artf = open('/tmp/%s.%i' % (jnlfilename, i), 'r')
    #page = BeautifulSoup(urllib2.urlopen(rec['artlink'], timeout=300))
    page = BeautifulSoup(''.join(artf.readlines()))
    artf.close()
    #pbn
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_firstpage'}):
        rec['p1'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_lastpage'}):
        rec['p2'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_doi'}):
        rec['doi'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_date'}):
        rec['year'] = meta['content']
    #title
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_title'}):
        rec['tit'] = meta['content']
    #fulltext
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
        rec['FFT'] = meta['content']
    #license
    if 'licence'  in journals[journal].keys():
        rec['licence'] = journals[journal]['licence']
    #kewyords
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_keywords'}):
        for keyw in re.split(';', meta['content']):
            rec['keyw'].append(re.sub('<TEX>', '', keyw))
    #authors
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_author'}):
        for author in re.split(' *; *',  meta['content']):
            if re.search(',', author):
                rec['auts'].append(author)
            else:
                rec['auts'].append(re.sub('(.*) (.*)', r'\1, \2', author))
    for div in page.body.find_all('div', attrs = {'class' : 'article-box'}):
        for h4 in div.find_all('h4'):
            #abstract
            if re.search('Abstract', h4.text):
                for p in div.find_all('p'):
                    rec['abs'] = re.sub('[\r\n\t]', '', p.text)
            #references
            elif re.search('References', h4.text):
                for li in div.find_all('li'):
                    adoi = False
                    for a in li.find_all('a'):
                        if a.has_attr('href') and re.search('doi.org', a['href']):
                            adoi = re.sub('.*doi.org.', ', DOI: ', a['href'])
                            a.replace_with('')
                    lit = li.text                    
                    if not re.search('doi.org', lit) and adoi:
                        lit += adoi
#                    lit = re.sub('\.? *https?:\/\/doi.org\/', ', DOI: ', lit)
                    rec['refs'].append([('x', re.sub('  +', '', re.sub('[\r\n\t]', ' ', lit)))])
    print '   { ' + ' | '.join(['%s[%i] ' % (k[0], len(rec[k])) for k in rec.keys()]) + ' }---'

    
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

