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
if jnl == 'proceedings':
    vol = sys.argv[2]
    iss = sys.argv[3]
    cnum = sys.argv[4]

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)



if jnl == 'proceedings':
    starturl = 'http://www.mdpi.com/2504-3900/%s/%s' % (vol, iss)
    #starturl = 'https://www.mdpi.com/journal/universe/special_issues/ICNFP2018'
    jnlfilename = 'mdpi_proc%s.%s_%s' % (vol, iss, cnum)
    done = []
else:
    starturl = 'http://www.mdpi.com/search?journal=%s&year_from=1996&year_to=2025&page_count=10&sort=pubdate&view=default' % (jnl)
    starturl = 'http://www.mdpi.com/search?journal=%s&year_from=2016&year_to=2025&page_count=10&sort=pubdate&view=default' % (jnl)
    jnlfilename = '%s.%s' % (jnl, stampoftoday)
    done =  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/*%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, jnl)))
    done +=  map(tfstrip,os.popen("grep '^3.*DOI' %s/backup/%4d/*%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, now.year-1, jnl)))
    done +=  map(tfstrip,os.popen("grep '^3.*DOI' %s/onhold/*%s*doki |sed 's/.*=//'|sed 's/;//'" % (ejldir, jnl)))
    print 'already done:', done




hdr = {'User-Agent' : 'Mozilla/5.0'}
artlinks = []
if jnl == 'proceedings':
#    starturl = 'https://www.mdpi.com/journal/galaxies/special_issues/non-thermalUniverse'
#    done = []
    print starturl
    req = urllib2.Request(starturl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('div', attrs = {'class' : 'article-content'})
    for div in divs:
        for a in div.find_all('a', attrs = {'class' : 'title-link'}):
            artlinks.append(('http://www.mdpi.com' + a['href'], a.text))
else:
    for j in range(40-20):
        print '%s&page_no=%i' % (starturl, j+1)
        req = urllib2.Request('%s&page_no=%i' % (starturl, j+1), headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        divs = tocpage.body.find_all('div', attrs = {'class' : 'article-content'})
        for div in divs:
            for a in div.find_all('a', attrs = {'class' : 'title-link'}):
                if not ('http://www.mdpi.com' + a['href'], a.text) in artlinks:
                    artlinks.append(('http://www.mdpi.com' + a['href'], a.text))

done = []
                    
i=0
recs = []
for artlink in artlinks:
    rec = {'jnl' : jnl.title(), 'tc' : 'C', 'keyw' : [], 'aff' : [], 'auts' : [],
           'note' : [], 'refs' : []}#, 'cnum' : 'C18-09-18.1'}
    i += 1
    #title and link
    if jnl == 'proceedings':
        rec['jnl'] = 'MDPI Proc.'
        rec['tc'] = 'C'
        rec['cnum'] = cnum
    elif jnl == 'condensedmatter':
        rec['jnl'] = 'Condens.Mat.'
    elif jnl == 'physics':
        rec['jnl'] = 'MDPI Physics'
    print '---{ %i/%i }---{ %s }---' % (i, len(artlinks), artlink[0])
    rec['FFT'] = artlink[0] + '/pdf'
    rec['tit'] = artlink[1]
    #get detailed page
    artreq = urllib2.Request(artlink[0], headers=hdr)
    page = BeautifulSoup(urllib2.urlopen(artreq))
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
            for a2 in div.find_all('a'):
                rec['note'].append([ a2.text ])
    ##authors and affiliations
    for div in page.body.find_all('div', attrs = {'class' : 'art-authors'}):                    
#        for div in diva.find_all('div', attrs = {'class' : 'author'}):
            for sup in div.find_all('sup'):
                newcont = ''
                for cont in re.split(' *, *', sup.text):
                    if re.search('\d', cont):
                        newcont += ' , =Aff%s, ' % (cont.strip())
                sup.replace_with(newcont)
            for script in page.body.find_all('script'):
                script.replace_with('')
            #ORCIDs
            for a in div.find_all('a', attrs = {'itemprop' : 'author'}):
                if a.has_attr('href') and re.search('orcid=[0-9]', a['href']):
                    orcid = re.sub('.*orcid=', 'ORCID:', a['href'])
                    author = a.text.strip()
                    a.replace_with('%s; %s' % (author, orcid))
            authors = re.sub(' and ', ' , ', re.sub('\xa0', ' ', div.text))
            authors = re.sub('&nbsp;', ' ', authors)
            authors = re.sub('\*', ' ', authors)
            for author in re.split(' *, *', re.sub('[\n\t]', '', authors)):
                if len(author.strip()) > 2:
                    if re.search('ORCID', author):
                        parts = re.split(' *; *', author)
                        rec['auts'].append('%s, %s' % (ejlmod2.shapeaut(parts[0]), parts[1]))
                    else:
                        rec['auts'].append(author.strip())        
    for diva in page.body.find_all('div', attrs = {'class' : 'art-affiliations'}):
        for div in diva.find_all('div', attrs = {'class' : 'affiliation'}):
            for sup in div.find_all('sup'):
                sup.replace_with('Aff%s= ' % (sup.text))
            for span in div.find_all('span'):
                span.replace_with(';;;')
            for aff in re.split(' *;;; *', re.sub('[\n\t]', '', div.text)):
                rec['aff'].append(aff.strip())
    #references
    reflink = artlink[0]  + '/htm'
    refreq = urllib2.Request(reflink, headers=hdr)
    refpage = BeautifulSoup(urllib2.urlopen(refreq))
    for section in refpage.body.find_all('section', attrs = {'id' : 'html-references_list'}):
        for li in section.find_all('li'):
            for a2 in li.find_all('a', attrs = {'class' : 'cross-ref'}):
                rdoi = re.sub('.*doi\.org\/', 'doi: ', a2['href'])
                a2.replace_with(rdoi)
            for a2 in li.find_all('a'):
                a2.replace_with('')
            lit = re.sub('\[\]', '', li.text.strip())
            lit = re.sub('\.? *\[(doi:.*?)\]', r', \1', lit)
            lit = re.sub('\.? *\[(http.*?)\]', r', \1', lit)
            lit = re.sub('\[Google Scholar\]', '', lit)
            #Semikolon between authors
            lit = re.sub('([A-Z]\.); ([A-Z][a-zA-Z\-]+), ([A-Z\.]+);', r'\1, \2 \3,', lit)
            lit = re.sub('([A-Z]\.); ([A-Z][a-zA-Z\-]+), ([A-Z\.]+);', r'\1, \2 \3,', lit)
            rec['refs'].append([('x', lit)])
    recs.append(rec)
print '%i new records' % (len(recs)) 

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

