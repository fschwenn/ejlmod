# -*- coding: UTF-8 -*-
##!/usr/bin/python
#program to harvest Wiley-journals
# FS 2016-12-13

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

publisher = 'WILEY'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]
year = sys.argv[4]
jnlfilename = re.sub('\/','-',jnl+vol+'.'+issue)
#harvested vi desydoc
if   (jnl == 'annphys'):
    issn = '1521-3889'
    doitrunk = '10.1002/andp'
    jnlname = 'Annalen Phys.'
elif (jnl == 'fortp'):
    issn = '1521-3978'
    doitrunk = '10.1002/prop'
    jnlname = 'Fortsch.Phys.'
elif (jnl == 'cpama'):
    issn = '1097-0312'
    doitrunk = '10.1002/cpa'
    jnlname = 'Commun.Pure Appl.Math.'  
#harevsted by hand
elif (jnl == 'mdpc'):
    issn = '2577-6576'
    doitrunk = '10.1002/mdp2'
    jnlname = 'Mater.Des.Proc.Comm.'
elif (jnl == 'anyaa'):
    issn = '1749-6643'
    doitrunk = '10.1111/nyas'
    jnlname = 'Annals N.Y.Acad.Sci.'
elif (jnl == 'ctpp'):
    issn = '1521-3986'
    doitrunk = '10.1002/ctpp'
    jnlname = 'Contrib.Plasma Phys.'
elif (jnl == 'mma'):
    issn = '1099-1476'
    doitrunk = '10.1002/mma'
    jnlname = 'Math.Methods Appl.Sci.'
#not harvested
elif (jnl == 'jamma'):
    issn = '1521-4001'
    doitrunk = '10.1002/zamm'
    jnlname = 'J.Appl.Math.Mech.'
elif (jnl == 'puz'):
    issn = '1521-3943'
    doitrunk = '10.1002/piuz'
    jnlname = 'Phys.Unserer Zeit'
#now at other publishers    
elif (jnl == 'mnraa'): 
    issn = '1356-2966'
    doitrunk = '10.1111/mnr'
    jnlname = 'Mon.Not Roy.Astron.Soc.'
elif (jnl == 'mnraal'):
    issn = '1745-3933'
    doitrunk = '10.1002/mnl'
    jnlname = 'Mon.Not.Roy.Astron.Soc.'
elif (jnl == 'asnaa'):
    issn = '1521-3994'
    doitrunk = '10.1002/asna'
    jnlname = 'Astron.Nachr.'



urltrunk = 'http://onlinelibrary.wiley.com/doi'
print "%s%s, Issue %s" %(jnlname,vol,issue)
if re.search('1111',doitrunk):
    toclink = '%s/%s.%s.%s.issue-%s/issuetoc' % (urltrunk,doitrunk,year,vol,issue)
else:
    toclink = '%s/%s.v%s.%s/issuetoc' % (urltrunk,doitrunk,vol,issue)
    toclink = 'https://onlinelibrary.wiley.com/toc/%s/%s/%s/%s'  % (issn[:4]+issn[5:], year, vol, issue)
try:
    print toclink
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
    #tocpage = BeautifulSoup(urllib2.urlopen(toclink,timeout=300))
except:
    toclink = '%s/%s.%s.%s.issue-%s/issuetoc' % (urltrunk, doitrunk, year, vol, issue)
    print toclink
    tocpage = BeautifulSoup(urllib2.urlopen(toclink,timeout=300))


recs = []
for div in tocpage.find_all('div', attrs = {'class' : 'issue-item'}):
    for h2 in div.find_all('h2'):
        tit = h2.text.strip()
    if tit == 'Contents' or re.search('^Issue Information:', tit) or re.search('^Cover Picture:', tit):
        continue
    rec = {'tit' : tit, 'year' : year, 'jnl' : jnlname, 'autaff' : [],
           'note' : [], 'vol' : vol, 'issue' : issue, 'keyw' : []}
    for a in div.find_all('a', attrs = {'class' : 'issue-item__title'}):
        rec['doi'] = re.sub('.*\/(10\..*)', r'\1', a['href'])
        rec['artlink'] = 'https://onlinelibrary.wiley.com' + a['href']
    recs.append(rec)
    
i = 0
for rec in recs:
    i += 1
    typecode = 'P'
    #rec['cnum'] = 'C18-09-08'
    print '---{ %i/%i }---{ %s }---{ %s }------' % (i, len(recs), rec['doi'], rec['artlink'])
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    autaff = False
    for meta in artpage.head.find_all('meta'):
        if meta.attrs.has_key('name'):
            #title
            if meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #pubnote
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #authors
            elif meta['name'] == 'citation_author':
                if autaff:
                    rec['autaff'].append(autaff)
                autaff = [ meta['content'] ]
            elif meta['name'] == 'citation_author_institution':
                autaff.append(meta['content'])
            elif meta['name'] == 'citation_author_orcid':
                orcid = re.sub('.*\/', '', meta['content'])
                autaff.append('ORCID:%s' % (orcid))
            elif meta['name'] == 'citation_author_email':
                email = meta['content']
                autaff.append('EMAIL:%s' % (email))
            #PDF
            #elif meta['name'] == 'citation_pdf_url':
            #    rec['FFT'] = meta['content']
    if not 'p1' in rec.keys():
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'article_references'}):
            rec['p1'] = re.sub('.*, (.+?)\..*', r'\1', meta['content'].strip())
            rec['p1'] = re.sub('.*: (\d+)', r'\1', rec['p1'])
    if autaff:
        rec['autaff'].append(autaff)
    #abstract
    for section in artpage.body.find_all('section', attrs = {'class' : 'article-section__abstract'}):
        rec['abs'] = section.text.strip()
        rec['abs'] = re.sub('^Abstract', '', rec['abs'])
    #special issue
    for p in artpage.body.find_all('p', attrs = {'class' : 'specialIssue'}):
        note = p.text.strip()
        rec['note'].append(note)
        if re.search('(Proceedings|Conference|Workshop)',note):
            typecode = 'C'
    #references ?
    uls = artpage.body.find_all('ul', attrs = {'class' : 'article-section__references-list'})
    if not uls:
        for section in artpage.body.find_all('section', attrs = {'id' : 'references-section'}):
            uls = section.find_all('ul', attrs = {'class' : 'rlist'})
            len(uls)
    for ul in uls:
        rec['refs'] = []
        for li in ul.find_all('li'):
            if not li.has_attr('data-bib-id'):
                continue
            for span in li.find_all('span', attrs = {'class' : 'bullet'}):
                refno = span.text
                span.replace_with(refno + ') ')
            for a in li.find_all('a'):
                if a.text in ['CrossRef', 'Crossref']:
                    rdoi = re.sub('.*=', '', a['href'])
                    rdoi = re.sub('%28', '(', rdoi)
                    rdoi = re.sub('%29', ')', rdoi)
                    rdoi = re.sub('%2F', '/', rdoi)
                    rdoi = re.sub('%3A', ':', rdoi)
                    a.replace_with(', DOI: %s' % (rdoi))
                else:
                    a.replace_with('')
            ref = li.text.strip()
            ref = re.sub(' ([12]\d\d\d); ([A-Z0-9\(\)]+): ', r'\2 (\1) ', ref)
            rec['refs'].append([('x', ref)])
    if not jnl in ['puz']:
        rec['tc'] = typecode
    else:
        rec['tc'] = ''
    print rec




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
