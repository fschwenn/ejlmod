# -*- coding: UTF-8 -*-
#program to harvest journals from the Royal Society
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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

publisher = 'Royal Society'
jnl = sys.argv[1]
vol = sys.argv[2]
issue = sys.argv[3]
if   (jnl == 'prs'): 
    issn = '1364-5021'
    url = 'PRSLA'
    jnlname = 'Proc.Roy.Soc.Lond.'
    vol = 'A' + vol
    urltrunk = 'http://rspa.royalsocietypublishing.org'
    urltrunk = 'https://royalsocietypublishing.org/toc/rspa'
elif (jnl == 'prts'): 
    issn = '1364-503x'
    url = 'PTRSA'
    vol = 'A' + vol
    jnlname = 'Phil.Trans.Roy.Soc.Lond.'
    urltrunk = 'http://rsta.royalsocietypublishing.org'
    urltrunk = 'https://royalsocietypublishing.org/toc/rsta'

jnlfilename = "%s%s.%s" % (jnl,vol,issue)
toclink = "%s/content/%s/%s.toc" % (urltrunk, re.sub('^[A-Z]', '', vol), issue)
toclink = "%s/%s/%s/" % (urltrunk, re.sub('^[A-Z]', '', vol), issue)

print "%s%s, Issue %s" %(jnlname,vol,issue)
print "get table of content... from %s" % (toclink)

driver = webdriver.PhantomJS()

driver.implicitly_wait(300)
driver.get(toclink)
#tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(toclink))
tocpage = BeautifulSoup(driver.page_source, features="lxml")


recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'issue-item'}):
    rec = {'jnl' : jnlname, 'tc' : 'P', 'vol' : vol, 'issue' : issue, 'autaff' : [], 'autaff2' : []}
    for h5 in div.find_all('h5', attrs = {'class' : 'issue-item__title'}):
        for a in h5.find_all('a'):
            artlink = "%s%s" % ('https://royalsocietypublishing.org', a['href'])
            print artlink
            rec['doi'] = re.sub('.*\/(10\..*)', r'\1', artlink)
            rec['tit'] = a.text.strip()
    for div2 in div.find_all('div', attrs = {'class' : 'toc-item__detail'}):
        div2t = div2.text.strip()
        rec['year'] = re.sub('.*?([12]\d\d\d).*', r'\1', div2t)
        rec['p1'] = re.sub('.*ID: *(\d+).*', r'\1', div2t)
    for div2 in div.find_all('div', attrs = {'class' : 'accordion'}):
        for a in div2.find_all('a'):
            a.replace_with('')
    for ul in div.find_all('ul', attrs = {'aria-label' : 'author'}):
        for li in ul.find_all('li'):
            rec['autaff'].append([li.text.strip()])    
    #details from article page
    try:
        try:
            time.sleep(30)
            driver.get(artlink)
            artpage = BeautifulSoup(driver.page_source, features="lxml")
        except:
            print ' - wait 5 minutes -'
            time.sleep(300)
            driver.get(artlink)
            artpage = BeautifulSoup(driver.page_source, features="lxml")
        #meta
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #if meta['name'] == 'dc.Title':
                #    rec['tit'] = meta['content']
                #elif meta['name'] == 'dc.Creator':
                #    rec['auts'].append(meta['content'])
                if meta['name'] == 'dc.Subject':
                    rec['keyw'] = re.split(' *; *', meta['content'])
                #elif meta['name'] == 'dc.Description':
                #    rec['abs'] = meta['content']
                elif meta['name'] == 'dc.Date':
                    rec['date'] = re.sub('.*?(\d\d\d\\d\-\d+\-\d+)$', r'\1', meta['content'])
                elif meta['name'] == 'dc.Type':
                    rec['note'] = [ meta['content'] ]
                #elif meta['name'] == 'dc.Identifier':
                #    rec['p1'] = re.sub('\D*', '', meta['content'])
        #abstract
        for div in artpage.find_all('div', attrs = {'class' : 'abstractInFull'}):
            rec['abs'] = div.text.strip()
        #license
        for lic in artpage.find_all('license'):
            if lic.has_attr('xlink:href'):
                rec['license'] = {'url' : lic['xlink:href']}
                rec['FFT'] = re.sub('\/doi\/', '/doi/pdf/', artlink)
        #authors
        for div in artpage.find_all('div', attrs = {'class' : 'accordion-tabbed__tab-mobile'}):
            #name
            for span in div.find_all('span'):
                rec['autaff2'].append([span.text.strip()])
            #ORCID
            for p in div.find_all('p', attrs = {'class' : 'orcid-account'}):
                for a in p.find_all('a'):
                    rec['autaff2'][-1].append(re.sub('.*org\/', 'ORCID:', a.text.strip()))
            #email
            if len(rec['autaff2'][-1]) < 2:
                for a in div.find_all('i', attrs = {'class' : 'icon-Email'}):
                    rec['autaff2'][-1].append(re.sub('mailto:', 'EMAIL:', a['title']))
            #affiliation
            for div2 in div.find_all('div', attrs = {'class' : 'author-info'}):
                for a in div2.find_all('a'):
                    a.decompose()
                ps = []
                for p in div2.find_all('p'):
                    pt = p.text.strip()
                    if pt:
                        ps.append(pt)
                if len(ps) > 1:
                    rec['autaff2'][-1] += ps[1:]
        if len(rec['autaff2']) >= len(rec['autaff']):
            rec['autaff'] = rec['autaff2']
            
    except:
        print '...could not get article page ...'
    #references
    try:
        time.sleep(30)
        try:
            driver.get(re.sub('\/doi\/', '/doi/references/', artlink))
            refpage = BeautifulSoup(driver.page_source, features="lxml")
        except:
            print ' - wait 5 minutes -'
            time.sleep(300)
            driver.get(re.sub('\/doi\/', '/doi/references/', artlink))
            refpage = BeautifulSoup(driver.page_source, features="lxml")
        rec['refs'] = []
        for div in refpage.body.find_all('div', attrs = {'class' : 'article__references'}):
            for li in div.find_all('li'):
                for a in li.find_all('a', attrs = {'class' : 'ref__number'}):
                    atext = a.text.strip()
                    a.replace_with(re.sub('^(.*)\.', r'[\1] ', atext))
                for a in li.find_all('a'):
                    atext = a.text.strip()
                    if atext in ['Google Scholar', 'ISI', 'Crossref']:
                        a.replace_with('')
                lit = re.sub('\. \(doi:(10.*)\)', r', DOI: \1', li.text.strip())
                rec['refs'].append([('x', lit)])                
    except:
        print '...could not get reference page ...'
        
    print '  ', rec.keys()
    recs.append(rec)

  
#write xml
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
