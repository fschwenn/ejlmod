# -*- coding: UTF-8 -*-
##!/usr/bin/python
#program to harvest Proc.Nat.Acad.Sci.
# FS 2019-07-17

import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import time


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'

publisher = 'National Academy of Sciences of the USA'
vol = sys.argv[1]
issues = sys.argv[2]
jnlfilename = 'procnas%s.%s' % (vol, re.sub(',', '_', issues))
jnlname = 'Proc.Nat.Acad.Sci.'
hdr = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
       'Accept-Encoding': 'none',
       'Accept-Language': 'en-US,en;q=0.8',
       'Connection': 'keep-alive'}



recs = []
artlinks = []
for issue in re.split(',', issues):
    (note1, note2) = (False, False)
    tocurl = 'https://www.pnas.org/content/%s/%s' % (vol, issue)
    print '---{ %s of %s }---{ %s}---' % (issue, issues, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    #tocpage = BeautifulSoup(urllib2.urlopen(req))
    tocfilename = '/tmp/procnas%s.%s.toc' % (vol, issue)
    if not os.path.isfile(tocfilename):
        os.system("wget -q -T 300 -O %s %s" % (tocfilename, tocurl))
        time.sleep(7)
    tocfile = open(tocfilename, 'r')
    tocpage = BeautifulSoup(''.join(tocfile.readlines()))
    tocfile.close()

    for contdiv in tocpage.body.find_all('div', attrs = {'class' : 'issue-toc-section'}):
        for child in contdiv.children:
            try:
                childname = child.name
            except:
                continue
            if childname == 'h2':
                note1 = child.text.strip()
                print note1
            elif childname == 'ul':
                for li in child.find_all('li'):
                    if li.has_attr('class'):
                        if 'toc-item' in li['class']:
                            rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'note' : [], 'autaff' : [], 'tc' : 'P'}
                            if note1:
                                rec['note'].append(note1)
                            for a in li.find_all('a', attrs = {'class' : 'highwire-cite-linked-title'}):
                                rec['artlink'] = 'https://www.pnas.org' + a['href']
                            if not rec['artlink'] in artlinks:
                                artlinks.append(rec['artlink'])
                                if not note1 in ['Commentaries', 'This Week in PNAS', 'News Feature']:
                                    recs.append(rec)
                        elif 'issue-toc-section' in li['class']:
                            for grandchild in li.children:
                                try:
                                    grandchildname = grandchild.name
                                except:
                                    continue
                                if grandchildname == 'h2':
                                    note2 = grandchild.text.strip()
                                    print ' ', note2
                                elif grandchildname == 'ul':
                                    for li in grandchild.find_all('li'):
                                        if li.has_attr('class'):
                                            if 'toc-item' in li['class']:
                                                rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : issue, 'note' : [], 'autaff' : [], 'tc' : 'P'}
                                                if note1:
                                                    rec['note'].append(note1)
                                                if note2:
                                                    rec['note'].append(note2)
                                                for a in li.find_all('a', attrs = {'class' : 'highwire-cite-linked-title'}):
                                                    rec['artlink'] = 'https://www.pnas.org' + a['href']
                                                if not rec['artlink'] in artlinks:
                                                    if not re.search('early', rec['artlink']):
                                                        artlinks.append(rec['artlink'])
                                                        if not note1 in ['Commentaries', 'This Week in PNAS', 'News Feature']:
                                                            recs.append(rec)


for i in range(len(recs)):
    print '------{ %5i/%5i }---{ %s }---' % (i+1, len(recs), recs[i]['artlink'])
    #artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(recs[i]['artlink']))
    artfilename = '/tmp/procnas.%s' % (re.sub('\W', '', recs[i]['artlink'][8:]))
    if not os.path.isfile(artfilename):
        os.system("wget -q -T 300 -O %s %s" % (artfilename, recs[i]['artlink']))
        time.sleep(6)
    artfile = open(artfilename, 'r')
    artpage = BeautifulSoup(''.join(artfile.readlines()))
    artfile.close()
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #title
            if meta['name'] == 'citation_title':
                recs[i]['tit'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                recs[i]['doi'] = meta['content']
            #number of pages
            elif meta['name'] == 'citation_num_pages':
                recs[i]['pages'] = meta['content']
            #pubnote
            elif meta['name'] == 'citation_firstpage':
                recs[i]['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                recs[i]['p2'] = meta['content']
            #abstract
            elif meta['name'] == 'citation_abstract' and not meta.has_attr('scheme'):
                recs[i]['abs'] = meta['content']
            #date
            elif meta['name'] == 'article:published_time':
                recs[i]['date'] = meta['content']
            #
            elif meta['name'] == '':
                recs[i][''] = meta['content']
            #authors
            elif meta['name'] == 'citation_author':
                recs[i]['autaff'].append([ meta['content'] ])
            elif meta['name'] == 'citation_author_institution':
                if not meta['content'] in recs[i]['autaff'][-1]:
                    recs[i]['autaff'][-1].append(meta['content'])
            elif meta['name'] == 'citation_author_orcid':
                orcid = re.sub('.*\/', '', meta['content'])
                recs[i]['autaff'][-1].append('ORCID:%s' % (orcid))
            #wrong on webpage: each author has all email adresses :(
            #elif meta['name'] == 'citation_author_email':
            #    email = meta['content']
            #    recs[i]['autaff'][-1].append('EMAIL:%s' % (email))
    #keywords
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'kwd-group'}):
        recs[i]['keyw'] = []
        for li in ul.find_all('li'):
            recs[i]['keyw'].append(li.text.strip())
    #references
    for div in artpage.body.find_all('div', attrs = {'class' : 'section ref-list'}):
        recs[i]['refs'] = []
        for ol in div.find_all('ol', attrs = {'class' : 'cit-list'}):
            for li in ol.children:
                for a in li.find_all('a', attrs = {'class' : 'cit-ref-sprinkles'}):
                    a.replace_with('')
                ref = li.text.strip()            
                for div2 in li.find_all('div'):
                    if div2.has_attr('data-doi'):
                        ref = re.sub('\.$', '', ref)
                        ref += ', DOI: %s.' % (div2['data-doi'])
                recs[i]['refs'].append([('x', ref)])
    print recs[i].keys()
    

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
