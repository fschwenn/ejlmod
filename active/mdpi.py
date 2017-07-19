# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest MDPI journals (Universe, Symmetry, Sensors, Instruments, Galaxies, Entropy)
# FS 2017-07-17

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
def tfstrip(x): return x.strip()

publisher = 'MDPI'
jnl = sys.argv[1]


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = '%s.%s' % (jnl, stampoftoday)

done =  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, jnl)))
done +=  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/%4d/%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, now.year-1, jnl)))
done +=  map(tfstrip,os.popen("grep '^3.*DOI' %s/onhold/%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, jnl)))


starturl = 'http://www.mdpi.com/search?journal=%s&year_from=1996&year_to=2020&page_count=50&sort=pubdate&view=default' % (jnl)
tocpage = BeautifulSoup(urllib2.urlopen(starturl))

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'article-content'}):
    rec = {'jnl' : jnl.title(), 'tc' : 'P', 'keyw' : [], 'aff' : [], 'auts' : [],
           'note' : [], 'refs' : []}
    #title and link
    for a in div.find_all('a', attrs = {'class' : 'title-link'}):
        link = 'http://www.mdpi.com' + a['href']  + '/htm'
        rec['FFT'] = 'http://www.mdpi.com' + a['href']  + '/pdf'
        rec['tit'] = a.text
        print link
    #get detailed page
    page = BeautifulSoup(urllib2.urlopen(link))
    ##Review?1
    for meta in page.head.find_all('meta', attrs = {'name' : 'dc.type'}):
        if meta['content'] == 'Review': rec['tc'] = 'R'
    for atype in page.find_all('span', attrs = {'class' : 'label articletype'}):
        rec['note'].append(atype.text)
        if atype.text == 'Review':
            rec['tc'] = 'R'
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
                rec['note'].append([ a.text ])
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
    #references 
    for section in page.body.find_all('section', attrs = {'id' : 'html-references_list'}):
        for li in section.find_all('li'):
            for a in li.find_all('a', attrs = {'class' : 'cross-ref'}):
                rdoi = re.sub('.*doi\.org\/', 'doi: ', a['href'])
                a.replace_with(rdoi)
            for a in li.find_all('a'):
                a.replace_with('')
            rec['refs'].append([('x', li.text.strip())])
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

