# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest 'Condensed Matter Phys.'
# FS 2020-06-12

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

'Condensed Matter Phys.'
        
journal = sys.argv[1]
vol = sys.argv[1]
iss = sys.argv[2]
publisher = 'National Academy of Sciences of Ukraine'

jnlfilename =  'condmatphys%s.%s' % (vol, iss)


#find TOC page
starturl = 'http://www.icmp.lviv.ua/journal/Contents.html'
startpage = BeautifulSoup(urllib2.urlopen(starturl, timeout=300), features="lxml")
searchstring = 'V.%s, %s' % (vol, iss)
for a in startpage.find_all('a'):
    if re.search(searchstring, a.text):
        tocurl = 'http://www.icmp.lviv.ua/journal/' + a['href']
        tocurltrunc = re.sub('(.*\/).*', r'\1', tocurl)
        print tocurl

#read TOC
recs = []
tocpage = BeautifulSoup(urllib2.urlopen(tocurl, timeout=300), features="lxml")
for a in tocpage.find_all('a'):
    if a.has_attr('href') and re.search('abstract.html', a['href']):
        rec = {'jnl' : 'Condensed Matter Phys.', 'vol' : vol, 'issue' : iss, 
               'tc' : 'P', 'license' : {'statement' : 'CC-BY-4.0'},
               'autaff' : []}
        rec['artlink'] = tocurltrunc + a['href']
        recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    artpage = BeautifulSoup(urllib2.urlopen(rec['artlink']), features="lxml")
    time.sleep(2)
    for a in artpage.find_all('a'):
        if a.has_attr('href'):
            #DOI
            if re.search('doi.org/10', a['href']):
                rec['doi'] = re.sub('.*doi.org\/', '', a['href'])
                a.replace_with('YYY')
            #fulltext
            elif re.search('pdf$', a['href']):
                rec['FFT'] = re.sub('(.*\/).*', r'\1', rec['artlink']) + a['href']
                a.replace_with('ZZZ')        
    #abstract
    for bq in artpage.find_all('blockquote'):
        rec['abs'] = re.sub('[\n\t\r]', ' ', bq.text.strip())
        bq.replace_with('WWW')
    #affiliations [mal formatted HTML]
    #for font in artpage.find_all('font'):
    #    ft = ''
    #    for aff in re.split('; ', font.text.strip()):
    #        aff = re.sub('^\(', '', aff)
    #        aff = re.sub('\)$', '', aff)
    #        ft += ' Aff=' + aff
    #    font.replace_with(ft)
    #work now on plain text
    at = re.sub('[\n\t\r]', ' ', artpage.text)
    #pubnote
    rec['year'] = re.sub('.* ([12]\d\d\d),.*YYY.*', r'\1', at)
    rec['p1'] = re.sub('.*, (\d+).*YYY.*', r'\1', at)
    #arXiv
    if re.search('arXiv:.*Title:', at):
        rec['arxiv'] = re.sub('.*arXiv:(.*\d).*?Title:.*', r'\1', at)
    #title
    rec['tit'] = re.sub('.*?Title: *(.*) *Author.s.:.*', r'\1', at)
    #keywords
    if re.search('WWW.*Key words:', at):
        rec['keyw'] = re.split(', ', re.sub('.*WWW.*Key words: (.*?) *(PACS|===|Full text).*', r'\1', at))
    #PACS
    if re.search('WWW.*PACS:', at):
        rec['pacs'] = re.split(', ', re.sub('.*WWW.*PACS: (.*?) *(===|Full text).*', r'\1', at))

    #authors
    authors = re.sub('.*Author.s.: *(.*) *WWW.*', r'\1', at)
    authors =  re.sub('^\&nbsp *', '', authors)
    for author in re.split(' *, *\&nbsp *', authors):
        if not re.search('Aff=', author):
            author = re.sub('\((.*)', r' Aff=\1', author)
            author = re.sub('\) *$', '', author)
        rec['autaff'].append(re.split(' *Aff=', author))


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

