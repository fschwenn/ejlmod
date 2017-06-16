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
if   (jnl == 'annphys'): 
    issn = '1521-3889'
    doitrunk = '10.1002/andp'
    jnlname = 'Annalen Phys.'
elif (jnl == 'puz'):
    issn = '1521-3943'
    doitrunk = '10.1002/piuz'
    jnlname = 'Phys.Unserer Zeit'
elif (jnl == 'fortp'):
    issn = '1521-3978'
    doitrunk = '10.1002/prop'
    jnlname = 'Fortsch.Phys.'
elif (jnl == 'mnraa'):
    issn = '1356-2966'
    doitrunk = '10.1111/mnr'
    jnlname = 'Mon.Not Roy.Astron.Soc.'
elif (jnl == 'jamma'):
    issn = '1521-4001'
    doitrunk = '10.1002/zamm'
    jnlname = 'J.Appl.Math.Mech.'
elif (jnl == 'cpama'):
    issn = '1097-0312'
    doitrunk = '10.1002/cpa'
    jnlname = 'Commun.Pure Appl.Math.'
elif (jnl == 'mnraal'):
    issn = '1745-3933'
    doitrunk = '10.1002/mnl'
    jnlname = 'Mon.Not.Roy.Astron.Soc.'
elif (jnl == 'asnaa'):
    issn = '1521-3994'
    doitrunk = '10.1002/asna'
    jnlname = 'Astron.Nachr.'
elif (jnl == 'anyaa'):
    issn = '1749-6643'
    doitrunk = '10.1111/nyas'
    jnlname = 'Annals N.Y.Acad.Sci.'
elif (jnl == 'tnya'):
    doitrunk = '10.1111/tnya'
    jnlname = 'Trans.New York Acad.Sci.'
    



urltrunk = 'http://onlinelibrary.wiley.com/doi'
print "%s%s, Issue %s" %(jnlname,vol,issue)
if re.search('1111',doitrunk):
    toclink = '%s/%s.%s.%s.issue-%s/issuetoc' % (urltrunk,doitrunk,year,vol,issue)
else:
    toclink = '%s/%s.v%s.%s/issuetoc' % (urltrunk,doitrunk,vol,issue)
try:
    print toclink
    tocpage = BeautifulSoup(urllib2.urlopen(toclink,timeout=300))
except:
    toclink = '%s/%s.%s.%s.issue-%s/issuetoc' % (urltrunk, doitrunk, year, vol, issue)
    print toclink
    tocpage = BeautifulSoup(urllib2.urlopen(toclink,timeout=300))

doisoa = {}
for ol in tocpage.find_all('ol', attrs = {'class' : 'articles'}):
    for input in ol.find_all('input', attrs = {'name' : 'doi'}):
        doi = input['value']
        doisoa[doi] = False
        for span in ol.find_all('span', attrs = {'class' : 'freeAccess'}):
            doisoa[doi] = True

recs = []
for doi in doisoa.keys():
    typecode = 'P'
    artlink = '%s/%s/full' % (urltrunk,doi)
    print "check %s... [%s]" %(doi, artlink)
    artpage = BeautifulSoup(urllib2.urlopen(artlink,timeout=300))
    rec = {'doi' : doi, 'year' : year, 'jnl' : jnlname, 'autaff' : [],
           'note' : [], 'vol' : vol, 'issue' : issue, 'keyw' : []}
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
            elif meta['name'] == 'article_references' and not rec.has_key('p1'):
                if re.search(' ([A-Z\d]+)\.?$',  meta['content']):
                    rec['p1'] = re.sub('.* ([A-Z\d]+)\.?$', r'\1', meta['content'])
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
            elif meta['name'] == 'citation_pdf_url' and doisoa[doi]:
                rec['FFT'] = meta['content']
    if not rec.has_key('p1'):
        for meta in artpage.head.find_all('meta', attrs = {'name' : 'article_references'}):
            rec['p1'] = re.sub('.*, (.+?)\..*', r'\1', meta['content'])
    rec['autaff'].append(autaff)
    #abstract
    for section in artpage.body.find_all('section', attrs = {'id' : 'abstract'}):
        rec['abs'] = section.text.strip()
        rec['abs'] = re.sub('^Abstract', '', rec['abs'])
    #special issue
    for p in artpage.body.find_all('p', attrs = {'class' : 'specialIssue'}):
        note = p.text.strip()
        rec['note'].append(note)
        if re.search('(Proceedings|Conference|Workshop)',note):
            typecode = 'C'
    #references
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'article-section__references-list'}):
        rec['refs'] = []
        for li in ul.find_all('li'):
            if not li.has_attr('id'):
                continue
            for span in li.find_all('span', attrs = {'class' : 'bullet'}):
                refno = span.text
                span.replace_with(refno + ') ')
            for a in li.find_all('a'):
                if a.text == 'CrossRef':
                    rdoi = re.sub('http:..dx.doi.org.', '', a['href'])
                    rdoi = re.sub('%28', '(', rdoi)
                    rdoi = re.sub('%29', ')', rdoi)
                    rdoi = re.sub('%2F', '/', rdoi)
                    rdoi = re.sub('%3A', ':', rdoi)
                    a.replace_with(', DOI: %s' % (rdoi))
                else:
                    a.replace_with('')
            ref = li.text.strip()
            rec['refs'].append([('x', ref)])
    if not rec.has_key('tit') or not rec['autaff'][0]:
        continue
    if not jnl in ['puz']:
        rec['tc'] = typecode
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
