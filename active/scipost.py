# -*- coding: UTF-8 -*-
#program to harvest journals from SciPost
# FS 2016-09-27


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

regexpsubm1 = re.compile('[sS]ubmissions')
regexpsubm2 = re.compile('.*\/(\d\d\d\d\.\d\d\d\d\d).*')

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
ejldir = '/afs/desy.de/user/l/library/dok/ejl'

publisher = 'SciPost Fundation'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]
if   (jnl == 'sps'): 
    jnlname = 'SciPost Phys.'
    #urltrunk = 'https://scipost.org/10.21468/SciPostPhys'
    urltrunk = 'https://scipost.org/SciPostPhys'    
    toclink = "%s.%s.%s" % (urltrunk, vol, issue)
elif   (jnl == 'spsp'): 
    jnlname = 'SciPost Phys.Proc.'
    urltrunk = 'https://scipost.org/SciPostPhysProc'
    toclink = "%s.%s" % (urltrunk, vol)

jnlfilename = "%s%s.%s" % (jnl, vol, issue)

print "%s%s, Issue %s" %(jnlname,vol,issue)
print "get table of content... from %s" % (toclink)

tocpage = BeautifulSoup(urllib2.urlopen(toclink))
#divs = tocpage.body.find_all('div', attrs = {'class' : 'card card-grey card-publication'})
divs = tocpage.body.find_all('div', attrs = {'class' : ['card', 'card-gray', 'card-publication']})
divs = tocpage.body.find_all('div', attrs = {'class' : 'card-publication'})


recs = []
#for div  in tocpage.body.find_all('div', attrs = {'class' : 'publicationHeader'}):
i = 0
for div  in divs:
    i += 1
    print '---{ %i/%i }---' % (i, len(divs))
    rec = {'jnl' : jnlname, 'tc' : 'P', 'vol' : vol, 'auts' : []}
    if (jnl == 'sps'):
        rec['issue'] = issue
    elif (jnl == 'spsp'):
        rec['cnum'] = issue
        rec['tc'] = 'C'
    for h3 in div.find_all('h3'):
        for a in h3.find_all('a'):
            artlink = 'https://scipost.org' + a['href']
            #title
            rec['tit'] = h3.text.strip()
    #abstract
    #for p in div.find_all('p', attrs = {'class' : 'publicationAbstract'}):
    #for p in div.find_all('p', attrs = {'class' : 'abstract mb-0 py-2'}):
    for p in div.find_all('p', attrs = {'class' : 'abstract'}):
        rec['abs'] = p.text.strip()
    #year
    #for p in div.find_all('p', attrs = {'class' : 'publicationReference'}):
    for p in div.find_all('p', attrs = {'class' : 'card-text text-muted'}):
        rec['year'] = re.sub('.*\((20\d\d)\).*', r'\1', re.sub('[\n\t]', '', p.text.strip()))
    #article page
    print artlink
    artpage = BeautifulSoup(urllib2.urlopen(artlink))  
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #article ID
            if meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #fulltext 
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #authors
            elif meta['name'] == 'citation_author':
                rec['auts'].append(meta['content'])
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
    #arXiv-number
    for a in artpage.body.find_all('a'):
        if a.has_attr('href'):
            if regexpsubm1.search(a.text) and regexpsubm2.search(a['href']):
                rec['arxiv'] = regexpsubm2.sub(r'\1', a['href'])
    #licence
    for a in artpage.body.find_all('a', attrs = {'rel' : 'license'}):
        rec['licence'] = {'url' : 'http:' + a['href']}
    #author
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'list-inline'}):
        if ul['class'] != ['list-inline', 'my-2']:
            continue
        rec['auts'] = []
        for li in ul.find_all('li', attrs = {'class' : ['list-inline-item', 'mr-1']}):            
            sups = []
            for sup in li.find_all('sup'):
                sups.append('=Aff' + sup.text.strip())                
                sup.replace_with('')
            lit = li.text.strip()
            lit = re.sub(', *$', '', lit)
            rec['auts'].append(lit)
            rec['auts'] += sups
    #affiliation
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'list'}):
        if ul['class'] != ['list', 'list-unstyled', 'my-2', 'mx-3']:
            continue
        rec['aff'] = []
        for li in ul.find_all('li'):
            for sup in li.find_all('sup'):
                supnr = sup.text.strip()
                sup.replace_with('')
            rec['aff'].append('Aff%s= %s' % (supnr, li.text.strip()))
    #collaboration
    for p in artpage.body.find_all('p', attrs = {'class' : 'mb-1'}):
        pt = p.text.strip()
        if re.search('[Cc]ollaboration', pt):
            rec['col'] = pt
    print rec
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
