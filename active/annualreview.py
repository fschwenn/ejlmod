#!/usr/bin/python
#program to harvest Annual Reviews
# FS 2012-06-01

import os
import ejlmod2
import re
import sys
import unicodedata
import urllib2
import urlparse
from bs4 import BeautifulSoup
import codecs


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'Annual Reviews'
jnl = sys.argv[1]
vol = sys.argv[2]

jnlfilename = jnl+vol

if   (jnl == 'arnps'): 
    jnlname = 'Ann.Rev.Nucl.Part.Sci.'
    urltrunk = 'http://www.annualreviews.org/toc/nucl/%s/1' % (vol)
elif (jnl == 'araa'):
    jnlname = 'Ann.Rev.Astron.Astrophys.'
    urltrunk = 'http://www.annualreviews.org/toc/astro/%s/1' % (vol)


print "get table of content of %s%s ... via %s" %(jnlname,vol, urltrunk)
tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk))

for title in tocpage.find_all('title'):
    year = re.sub('.*(20\d\d)$', r'\1', title.text.strip())

recs = []
for div in tocpage.find_all('div', attrs = {'class' : 'articleBox'}):
    rec = {'year' : year, 'vol' : vol, 'tc' : 'R', 'jnl' : jnlname, 'auts' : [], 'aff' : []}
    #doi
    for inp in div.find_all('input', attrs = {'name' : 'doi'}):
        rec['doi'] = inp['value']
    #title
    for h2 in div.find_all('h2'):
        rec['tit'] = h2.text.strip()
        #details
        for a in h2.find_all('a'):
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('http://www.annualreviews.org' + a['href']))
            #remove disturbiung stuff
            for div2 in artpage.find_all('div', attrs = {'class' : 'accordionContentWrapper'}):
                div2.replace_with('')
            #pages 
            for div2 in artpage.find_all('div', attrs = {'class' : 'issueInfo'}):
                if re.search('Vol\.', div2.text.strip()):
                    pages = re.sub('.*?: *([\d\-]+).*', r'\1', re.sub('\n', ' ', div2.text.strip()))
                    rec['p1'] = re.sub('\-.*', '', pages)
                    if re.search('\-', pages):
                        rec['p2'] = re.sub('.*\-', '', pages)
            #affiliations
            for div2 in artpage.find_all('div', attrs = {'class' : 'fulltext'}):
                for sup in div2.find_all('sup'):
                    affno = sup.text.strip()
                    sup.replace_with('Aff%s= ' % (affno))
                rec['aff'].append(re.sub('[;,]? email.*', '', div2.text.strip()))
                div2.replace_with('')
            #authors
            for div2 in artpage.find_all('div', attrs = {'class' : 'artAuthors'}):
                for sup in div2.find_all('sup'):
                    affno = sup.text.strip()
                    sup.replace_with(', =Aff' + ', =Aff'.join(re.split(' *, *', affno)) + ', ')
                authors = re.sub(' and ', ', ', div2.text.strip())
                for aut in re.split(' *, *', authors):
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\. ([A-Z])\.', r'.\1.',aut)
                    aut = re.sub('\.\-([A-Z])\.', r'.\1.',aut)
                    if aut:
                        rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1', aut))
            #abstract
            for div2 in artpage.find_all('div', attrs = {'class' : 'abstractSection'}):
                rec['abs'] = div2.text.strip()
    recs.append(rec)

                                       
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
 
