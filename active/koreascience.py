# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Korea Science
# FS 2015-11-13

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'


journals = {'jkas' : {'issn'      : '1225-4614',
                      'publisher' : 'The Korean Astronomical Society',
                      'jnl'       : 'J.Korean Astron.Soc.',
                      'kojic'     : 'CMHHBA'},
            'jass' : {'issn'      : '2093-5587',
                      'publisher' : 'The Korean Space Science Society',
                      'jnl'       : 'J.Astron.Space Sci.',
                      'kojic'     : 'OJOOBS'},
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

starturl = 'http://koreascience.or.kr/journal/JournalIssueList.jsp?kojic=%s&volno=%s&issno=%s' % (journals[journal]['kojic'], vol, iss)
print starturl
#tocpage = BeautifulSoup(urllib2.urlopen(starturl, timeout=300))
os.system('lynx -source "%s" > /tmp/%s.toc' % (starturl, jnlfilename))
tocf = open('/tmp/%s.toc' % (jnlfilename), 'r')
tocpage = BeautifulSoup(''.join(tocf.readlines()))
tocf.close()
recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'article_result_list_contain_100'}):
    rec = {'jnl' : journals[journal]['jnl'], 'vol' : vol, 'issue' : iss, 
           'tc' : 'P', 'auts' : [], 'keyw' : [], 'refs' : []}
    if len(sys.argv) > 4:
        rec['tc'] = 'C'
        rec['cnum'] = sys.argv[4]
    for li in div.find_all('li'):
        for a in li.find_all('a'):
            if a.has_attr('href') and re.search('javascript', a['href']):
                articlelink = re.sub("^.*?'(.*?)','(.*?)'.*", r'http://koreascience.or.kr/article/ArticleFullRecord.jsp?cn=\1&ordernum=\2', a['href'])
    print articlelink
    os.system('lynx -source "%s" > /tmp/%s.%i' % (articlelink, jnlfilename, len(recs)))
    artf = open('/tmp/%s.%i' % (jnlfilename, len(recs)), 'r')
    #page = BeautifulSoup(urllib2.urlopen(articlelink, timeout=300))
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
    if journal in ['jass']:
        rec['licence'] = {'statement' : 'CC-BY-3.0'}
    elif journal in ['jkms']:
        rec['licence'] = {'statement' : 'CC-BY-NC'}
    #kewyords
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_keywords'}):
        for keyw in re.split(';', meta['content']):
            rec['keyw'].append(re.sub('<TEX>', '', keyw))
    #authors
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_author'}):
        if re.search(',', meta['content']):
            rec['auts'].append(meta['content'])
        else:
            rec['auts'].append(re.sub('(.*) (.*)', r'\1, \2', meta['content']))
    #abstract
    for div in page.body.find_all('div', attrs = {'id' : 'abs'}):
        rec['abs'] = div.text
    #references
    for div in page.body.find_all('div', attrs = {'class' : 'full_record_block'}):
        for div2 in div.find_all('div', attrs = {'class' : 'full_record_text_r'}):
            for a in div2.find_all('a'):
                if a.has_attr('href') and re.search('dx.doi.org', a['href']):
                    a.replace_with(re.sub('.*dx.doi.org.', ', DOI: ', a['href']))
            rec['refs'].append([('x', re.sub('[\n\t]', '', div2.text))])
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

