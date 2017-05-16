#!/usr/bin/python
# -*- coding: UTF-8 -*-
#program to harvest "symmetry" (ISSN 2073-8994)
# FS 2012-06-01

import os
import ejlmod2
import codecs
import re
import sys
import urllib2
import urlparse
from bs4 import BeautifulSoup
import unicodedata

tmpdir = '/tmp'
xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

def tfstrip(x): return x.strip()

publisher = 'MDPI'
vol = sys.argv[1]
issue = sys.argv[2]
jnl = 'Symmetry'
jnlfilename = 'symmetry'+vol+'.'+issue
issn = '2073-8994'


print "get table of content..."
url = "http://www.mdpi.com/%s/%s/%s?view=compact" %(issn, vol, issue)
tocpage = BeautifulSoup(urllib2.urlopen(url))
recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'article-content'}):
    rec = {'jnl' : jnl, 'autaff' : [], 'tc' : 'P', 'vol' : vol, 'issue' : issue, 
           'keyw' : [], 'note' : [], 'autaff' : [], 'year' : str(2008 + int(vol))}
    #title
    for a in div.find_all('a', attrs = {'class' : 'title-link'}):
        rec['tit'] = a.text
        artlink = "http://www.mdpi.com" + a['href']
        artpage =  BeautifulSoup(urllib2.urlopen(artlink))
        #infos in meta-tags
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'publicationDate'}):
            rec['date'] = meta['content']
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'dc.identifier'}):
            rec['doi'] = meta['content']
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'dc.rights'}):
            rec['licence'] = {'url' : meta['content']}
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'dc.description'}):
            rec['abs'] = meta['content']
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'dc.subject'}):
            rec['keyw'].append(meta['content'])
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'prism.startingPage'}):
            rec['p1'] = meta['content']
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
            rec['FFT'] = meta['content']
        #special issue
        for div2 in artpage.body.find_all('div', attrs = {'class' : 'belongsTo'}):
            rec['note'].append(div2.text.strip())
        #article type
        for atype in artpage.find_all('span', attrs = {'class' : 'label articletype'}):
            rec['note'].append(atype.text)
            if atype.text == 'Review':
                rec['tc'] = 'R'
        #affiliations
        affdict = {}
        for affdiv in artpage.body.find_all('div', attrs = {'class' : 'affiliation'}):
            for affname in affdiv.find_all('div', attrs = {'class' : 'affiliation-name'}):
                for item in affdiv.find_all('div', attrs = {'class' : 'affiliation-item'}):
                    affdict[item.text] = affname.text
        #authors
        for autdiv in artpage.body.find_all('div', attrs = {'class' : 'art-authors'}):
            for span in autdiv.find_all('span'):
                for name in span.find_all('a', attrs = {'itemprop' : 'author'}):
                    author = re.sub('\&nbsp', ' ', name.text)
                    autaff = [ re.sub('(.*) (.*)', r'\2, \1', author) ]
                    items = []
                    for sup in span.find_all('sup'):
                        items += re.split(' *, *', sup.text.strip())
                    if items:
                        for item in items:
                            if affdict.has_key(item):
                                autaff.append(affdict[item])
                            elif re.search('[0-9a-zA-Z]', 'item'):
                                print 'no aff-item "%s" for author "%s"'  % (item, name.text)
                    else:
                        autaff.append(affname)
                    rec['autaff'].append(autaff)
                        
    recs.append(rec)
        
	







xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
#xmlfile  = open(xmlf,'w')
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








