#!/usr/bin/python
#program to harvest CJP
# FS 2020-03-06

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
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
tmpdir = '/tmp'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
def tfstrip(x): return x.strip()

publisher = 'NRC Research Press'
jnl = sys.argv[1]
vol = sys.argv[2]
isu = sys.argv[3]

month = {'January' : 1, 'February' : 2, 'March' : 3, 'April' : 4,
         'May' : 5, 'June' : 6, 'July' : 7, 'August' : 8,
         'September' : 9, 'October' : 10, 'November' : 11, 'December' : 12}

if   (jnl == 'cjp'): 
    jnlname = 'Can.J.Phys.'
    issn = '0008-4204'

jnlfilename = jnl+vol+'.'+isu

urltrunk = 'http://www.nrcresearchpress.com'
tocurl = '%s/toc/%s/%s/%s' % (urltrunk, jnl, vol, isu)
print "get table of content of %s%s.%s via %s " % (jnlname, vol, isu, tocurl)

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))


grdivs = tocpage.body.find_all('div', attrs = {'class' : 'articleGroup'})
if not grdivs:
    grdivs = tocpage.find_all('body')

recs = []
for grdiv in grdivs:
    section = False
    for h2 in grdiv.find_all('h2'):
        section = h2.text.strip()
    for div in grdiv.find_all('div', attrs = {'class' : 'abstractAndAccess'}):
        for a in div.find_all('a'):
            if re.search('http', a['href']):
                rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : isu, 'tc' : 'P',
                       'note' : [], 'aff' : [], 'auts' : []}
                rec['artlink'] = a['href']
                rec['doi'] = re.sub('.*org.(10.*)', r'\1', a['href'])
                if section: rec['note'].append(section)
                recs.append(rec)


i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    artfile = '/tmp/%s%s%s.%s' % (jnl, vol, isu, re.sub('/','_',rec['doi']))
    if not os.path.isfile(artfile):
        os.system('wget  -T 300 -t 3 -q -O %s "%s"' % (artfile, rec['artlink']))
        time.sleep(2)
    inf = open(artfile, 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #title
            if meta['name'] == 'dc.Title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'dc.Subject':
                rec['keyw'] = re.split('; ', meta['content'])
            #date
            elif meta['name'] == 'dc.Date':
                dates = re.split(' ', meta['content'])
                rec['date'] = '%s-%02i-%02i' % (dates[2], month[dates[1]], int(dates[0]))
            #DOI
            elif meta['name'] == 'dc.Identifier':
                if meta.has_attr('scheme') and meta['scheme'] == 'doi':
                    rec['doi'] = meta['content']
            #language
            elif meta['name'] == 'dc.Language':
                if meta['content'] == 'fr':
                    rec['language'] = 'French'
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'abstractSection'}):
        rec['abs'] = div.text.strip()
        if re.search('PACS Nos.: ', rec['abs']):
            pacss = re.sub('.*PACS Nos.: *', '', rec['abs'])
            rec['abs'] = re.sub('PACS Nos.*', '', rec['abs'])
            rec['pacs'] = re.split(' *, *', pacss)  
    #pages, year
    for p in artpage.body.find_all('p', attrs = {'class' : 'citationLine'}):
        for a in p.find_all(['a', 'span']):
            a.replace_with('')
        pbn = p.text.strip()
        rec['year'] = re.sub('.*?([12]\d\d\d).*', r'\1', pbn)
        p1p2 = re.sub('.*: *(.*?),.*', r'\1', pbn)
        if p1p2 == pbn:
            rec['p1'] = '0'
            rec['p2'] = '0'
        else:
            if re.search('\-', p1p2):
                [rec['p1'], rec['p2']] = re.split('\-', p1p2)
            else:
                rec['p1'] = p1p2
                rec['p2'] = p1p2
                rec['pages'] = '1'
    #affiliations
    for p in artpage.body.find_all('p', attrs = {'class' : 'affiliation'}):
        for sup in p.find_all('sup'):
            supt = sup.text
            sup.replace_with('Aff%s= ' % (supt))
        rec['aff'].append(p.text.strip())
        p.replace_with('')
    #authors
    for p in artpage.body.find_all('p', attrs = {'class' : 'author'}):
        for sup in p.find_all('sup'):
            supt = sup.text
            sup.replace_with(', =Aff%s, ' % (supt))
        for author in re.split(',', re.sub(' and ', ',', re.sub('[\n\t\r]', ' ', p.text.strip()))):
            author = author.strip()
            if author:
                rec['auts'].append(author)
    #references
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'no-bullet'}):
        rec['refs'] = []
        for li in ul.find_all('li'):
            rdoi = False
            for a in li.find_all('a'):
                if re.search('rossref', a.text):
                    rdoi = re.sub('.*key=', '', a['href'])
                    rdoi = re.sub('%2F', '/', rdoi)
                    rdoi = re.sub('%28', '(', rdoi)
                    rdoi = re.sub('%29', ')', rdoi)
                    rdoi = re.sub('%3A', ':', rdoi)
                a.replace_with('')
            reference = [('x', re.sub(', *,', ',', re.sub('[\n\t\r]', ' ', li.text.strip())))]
            if rdoi:
                reference.append(('a', 'doi:%s' % (rdoi)))
            rec['refs'].append(reference)
    print rec
            
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
#xmlfile = open(xmlf, 'w')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs ,xmlfile, publisher)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml' + "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
