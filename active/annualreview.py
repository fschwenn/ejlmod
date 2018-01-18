#!/usr/bin/python
#program to harvest Annual Reviews
# FS 2017-01-18

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

recs = []
doisdone = []
for div in tocpage.find_all('article', attrs = {'class' : 'teaser'}):
    #right colume??
    volume = re.sub('.*Vol\. (\d+).*', r'\1', re.sub('[\n\t]', ' ', div.text.strip()))
    print volume, vol
    if volume != vol:
        continue
    rec = {'vol' : vol, 'tc' : 'R', 'jnl' : jnlname, 'auts' : [], 'aff' : []}
    #doi
    for a in div.find_all('a'):
        if a.has_attr('href'):
            ahref= a['href']
            if re.search('doi.*10', ahref):
                doi = re.sub('.*?(10\..*)', r'\1', a['href'])
                if not re.search('#', doi):
                    rec['doi'] = doi
                    rec['artlink'] = 'http://www.annualreviews.org/doi/full/' + rec['doi']
    if rec['doi'] in doisdone:
        continue
    else:
        doisdone.append(rec['doi'])
    print rec['doi']
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #Title
            if meta['name'] == 'dc.Title':
                rec['tit'] = meta['content']
            #Keywords
            elif meta['name'] == 'dc.Subject':
                rec['keyw'] = re.split('; ', meta['content'])
            elif meta['name'] == 'keywords':
                rec['keyw'] = re.split(', ', meta['content'])
            #Abstract
            elif meta['name'] == 'dc.Description':
                rec['abs'] = meta['content']
    #Abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'abstractInFull'}):
        rec['abs'] = div.text.strip() 
    #pubnote
    for div in artpage.body.find_all('div', attrs = {'class' : 'article-header'}):
        divtext = re.sub('[\n\t]', ' ', div.text.strip())
        if re.search('.*?Vol. \d+:\d+\-\d+', divtext):
            rec['p1'] = re.sub('.*?Vol. \d+:(\d+)\-.*', r'\1', divtext)
            rec['p2'] = re.sub('.*?Vol. \d+:\d+\-(\d+).*', r'\1', divtext)
        rec['year'] = re.sub('.*Volume.*? (20\d\d).*', r'\1', divtext)
        if re.search('Advance', divtext):
            if re.search('Advance on [A-Za-z]+ \d+, \d+', divtext):
                rec['date'] = re.sub('.*Advance on ([A-Za-z]+) (\d+), (\d+).*', r'\2 \1 \3', divtext)
            else:
                rec['date'] = re.sub('.*Advance.* (20\d\d).*', r'\1', divtext)
    for div in artpage.body.find_all('div', attrs = {'class' : 'hlFld-ContribAuthor'}):
        #Authors
        for p in div.find_all('p', attrs = {'class' : 'name'}):
            for sup in p.find_all('sup'):
                afftext = ''
                for aff in re.split(',', sup.text):
                    afftext += '; =Aff%s' % (aff)
                sup.replace_with(afftext + '; ')
            ptext = re.sub(',', '', p.text.strip())
            ptext = re.sub(' and ', '; ', ptext)
            for aut in re.split('; ', ptext):
                if len(aut.strip()) > 2:
                    rec['auts'].append(aut.strip())
        #Affiliations
        for p in div.find_all('p'):
            if p.has_attr('class'): continue
            for sup in p.find_all('sup'):
                afftext = 'Aff%s= ' % (sup.text)
                sup.replace_with(afftext)
            rec['aff'].append(re.sub(' email.*', '', p.text.strip()))
    #Reference
    for div in artpage.body.find_all('div', attrs = {'class' : 'lit-cited'}):
        for ul in div.find_all('ul', attrs = {'class' : 'otherReviewsList'}):
            ul.replace_with('')
        rec['refs'] = []
        for li in div.find_all('li'):
            if not li.has_attr('refid'): continue
            refdoi = False
            for a in li.find_all('a'):
                if re.search('Crossref', a.text):
                    refdoi = re.sub('.*key=', '', a['href'])
                    refdoi = re.sub('%2F', '/', refdoi)
                    refdoi = re.sub('%28', '(', refdoi)
                    refdoi = re.sub('%29', ')', refdoi)
                    refdoi = re.sub('%3A', ':', refdoi)
                    refdoi = re.sub('%5B', '[', refdoi)
                    refdoi = re.sub('%5D', ']', refdoi)
                a.replace_with('')
            reftext = li.text.strip()
            if refdoi:
                reftext = '%s, DOI: %s' % (reftext, refdoi)
            rec['refs'].append([('x', reftext)])
    print rec['tit']
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
 
