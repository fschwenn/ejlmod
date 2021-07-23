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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

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

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'table-of-content'}):
    sectiontitle = False
    for child in div.children:
        try:
            child.name
        except:
            continue
        for h3 in child.find_all('h3'):
            sectiontitle = h3.text.strip()
        for div in child.find_all('div', attrs = {'class' : 'issue-item__title'}):
            for a in div.find_all('a'):
                for h5 in a.find_all('h5'):
                    rec = {'jnl' : jnlname, 'vol' : vol, 'issue' : isu, 'tc' : 'P',
                           'note' : [], 'autaff' : [], 'keyw' : []}
                    rec['artlink'] = 'https://cdnsciencepub.com' + a['href']
                    rec['doi'] = re.sub('.*?(10.1139.*)', r'\1', a['href'])
                    if sectiontitle: rec['note'].append(sectiontitle)
                    recs.append(rec)

i = 0
driver = webdriver.PhantomJS()
driver.implicitly_wait(60)
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    driver.get(rec['artlink'])
    artpage = BeautifulSoup(driver.page_source, features="lxml")
    for meta in artpage.find_all('meta'):
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
    for section in artpage.body.find_all('section', attrs = {'id' : 'abstract'}):
        for h2 in section.find_all('h2'):
            h2.decompose()
        rec['abs'] = section.text.strip()
        if re.search('PACS Nos.: ', rec['abs']):
            pacss = re.sub('.*PACS Nos.: *', '', rec['abs'])
            rec['abs'] = re.sub('PACS Nos.*', '', rec['abs'])
            rec['pacs'] = re.split(' *, *', pacss)
    #pages, year
    for span in artpage.body.find_all('span', attrs = {'property' : 'datePublished'}):
        rec['year'] = span.text.strip()
    for span in artpage.body.find_all('span', attrs = {'property' : 'pageStart'}):
        rec['p1'] = span.text.strip()
    for span in artpage.body.find_all('span', attrs = {'property' : 'pageEnd'}):
        rec['p2'] = span.text.strip()
    #keywords
    for section in artpage.body.find_all('section', attrs = {'property' : 'keywords'}):
        if section.has_attr('xml:lang') and section['xml:lang'] == 'fr':
            continue
        for li in section.find_all('li'):
            keyword = li.text.strip()
            if not keyword in rec['keyw']:
                rec['keyw'].append(keyword)
    #authors
    for section in artpage.body.find_all('section', attrs = {'class' : 'core-authors'}):
        for div in section.find_all('div', attrs = {'property' : 'author'}):
            #name
            for author in div.find_all('div', attrs = {'class' : 'heading'}):
                for fn in author.find_all('span', attrs = {'property' : 'familyName'}):
                    name = fn.text.strip()
                for gn in author.find_all('span', attrs = {'property' : 'givenName'}):
                    name += ', ' + gn.text.strip()
                rec['autaff'].append([name])
                #email
                for email in author.find_all('a', attrs = {'property' : 'email'}):
                    rec['autaff'][-1].append(re.sub('mailto:', 'EMAIL:', email['href']))
            #affiliations
            for aff in div.find_all('div', attrs = {'property' : 'organization'}):
                rec['autaff'][-1].append(aff.text.strip())
    #references
    for section in artpage.body.find_all('section', attrs = {'id' : 'bibliography'}):
        rec['refs'] = []
        for div in section.find_all('div', attrs = {'class' : 'labeled'}):
            rdoi = False
            for a in div.find_all('a'):
                if re.search('rossref', a.text):
                    rdoi = re.sub('.*doi.org\/', '', a['href'])
                    rdoi = re.sub('%2F', '/', rdoi)
                    rdoi = re.sub('%28', '(', rdoi)
                    rdoi = re.sub('%29', ')', rdoi)
                    rdoi = re.sub('%3A', ':', rdoi)
                a.replace_with('')
            reference = [('x', re.sub(', *,', ',', re.sub('[\n\t\r]', ' ', div.text.strip())))]
            if rdoi:
                reference.append(('a', 'doi:%s' % (rdoi)))
            rec['refs'].append(reference)
    print '  ', rec.keys()

xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()

#retrival
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml' + "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
