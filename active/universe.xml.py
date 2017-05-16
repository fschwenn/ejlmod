# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Universe
# FS 2015-11-11

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

publisher = 'MDPI'

def tfstrip(x): return x.strip()
done =  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/universe*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir)))

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'universe.%s' % (stampoftoday)

starturl = 'http://www.mdpi.com/search?journal=universe&year_from=1996&year_to=2020&page_count=50&sort=pubdate&view=default'
tocpage = BeautifulSoup(urllib2.urlopen(starturl))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'article-content'}):
    rec = {'jnl' : 'Universe', 'tc' : 'P', 'keyw' : [], 'aff' : [], 'auts' : []}
    #title and link
    for a in div.find_all('a', attrs = {'class' : 'title-link'}):
        link = 'http://www.mdpi.com' + a['href']
        rec['FFT'] = link + '/pdf'
        rec['tit'] = a.text
        print link
    #get detailed page
    page = BeautifulSoup(urllib2.urlopen(link))
    ##Review?
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.type'}):
        if meta['content'] == 'Review': rec['tc'] = 'R'
    ##Date
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.date'}):
        rec['date'] = meta['content']
    ##licence
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.rights'}):
        rec['licence'] = {'url' : re.sub('\/$', '', meta['content'])}
    ##keywords
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.subject'}):
        if meta['content'] != 'n/a':
            rec['keyw'].append(meta['content'])
    ##pbn
    for meta in page.head.find_all('meta', attrs = {'name' : 'prism.volume'}):
        rec['vol'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'prism.number'}):
        rec['issue'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'prism.startingPage'}):
        rec['p1'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'prism.endingPage'}):
        rec['p2'] = meta['content']
    for meta in page.head.find_all('meta', attrs = {'name' : 'citation_doi'}):
        rec['doi'] = meta['content']
        if rec['doi'] in done: continue        
    ##abstract
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.description'}):
        rec['abs'] = meta['content']
    ##special issue
    for div in page.body.find_all('div', attrs = {'class' : 'belongsTo'}):
        if re.search('Special Issue', div.text):
            for a in div.find_all('a'):
                rec['note'] = [ a.text ]
    ##authors and affiliations
    for div in page.body.find_all('div', attrs = {'class' : 'art-authors'}):
        for sup in div.find_all('sup'):
            newcont = ''
            for cont in re.split(' *, *', sup.text):
                if re.search('\d', cont):
                    newcont += ' , =Aff%s, ' % (cont.strip())
            sup.replace_with(newcont)
        for script in page.body.find_all('script'):
            script.replace_with('')
        authors = re.sub(' and ', ' , ', re.sub('\xa0', ' ', div.text))
        authors = re.sub('&nbsp;', ' ', authors)
        for author in re.split(' *, *', re.sub('[\n\t]', '', authors)):
            if len(author.strip()) > 2:
                rec['auts'].append(author.strip())        
    for div in page.body.find_all('div', attrs = {'class' : 'art-affiliations'}):
        for sup in div.find_all('sup'):
            sup.replace_with('Aff%s= ' % (sup.text))
        for span in div.find_all('span'):
            span.replace_with(';;;')
        for aff in re.split(' *;;; *', re.sub('[\n\t]', '', div.text)):
            rec['aff'].append(aff.strip())
    ##references are in link + '/xml', but too much work
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

