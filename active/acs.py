# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest ACS journals
# FS 2020-12-04

import sys
import os
import ejlmod2
import re
import urllib2,cookielib
import urlparse
import codecs
import time
from bs4 import BeautifulSoup
import datetime
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
tmpdir = '/tmp'
def tfstrip(x): return x.strip()

publisher = 'ACS'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
driver = webdriver.PhantomJS()
driver.implicitly_wait(30)

jnl =  sys.argv[1]
vol = sys.argv[2]
iss = sys.argv[3]
jnlfilename = 'acs_%s%s.%s' % (jnl, vol, iss)
if jnl == 'nalefd': # 1 issue per month
    jnlname = 'Nano Lett.'
    letter = ''
elif jnl == 'jpccck': # 1 issue per week
    jnlname = 'J.Phys.Chem.'
    letter = 'C'
elif jnl == 'jctcce': # 1 issue per month
    jnlname = 'J.Chem.Theor.Comput.'
    letter = ''
elif jnl == 'apchd5': # 1 issue per month
    jnlname = 'ACS Photonics'
    letter = ''
elif jnl == 'jacsat': # 1 issue per week
    jnlname = 'J.Am.Chem.Soc.'
    letter = ''
else:
    print ' unknown journal "%s"' % (jnl)
    sys.exit(0)

tocurl = 'https://pubs.acs.org/toc/%s/%s/%s' % (jnl, vol, iss)
print tocurl
driver.get(tocurl)
tocpage =  BeautifulSoup(driver.page_source)
section = False
recs = []
for div in tocpage.find_all('div', attrs = {'class' : 'toc'}):
    for child in div.children:
        try:
            child.name
        except:
            continue
        if child.name == 'h6':
            section = child.text.strip()
            print section
        elif  child.name == 'div':
            if not section in ['Mastheads']:
                for input in child.find_all('input', attrs = {'name' : 'doi'}):
                    rec = {'jnl' : jnlname, 'vol' : letter+vol, 'issue' : iss, 'tc' : 'P',
                           'keyw' : [], 'note' : [], 'autaff' : []}
                    rec['doi'] = input['value']
                    rec['artlink'] = 'https://pubs.acs.org/doi/' + input['value']
                    if section:
                        rec['note'] = [ section ]
                    #title
                    for h5 in child.find_all('h5'):
                        rec['tit'] = h5.text.strip()
                    #authors
                    for author in child.find_all('span', attrs = {'class' : 'hlFld-ContribAuthor'}):
                        rec['autaff'].append([author.text.strip()])
                    #pages
                    for span in child.find_all('span', attrs = {'class' : 'issue-item_page-range'}):
                        rec['p1'] = re.sub('\D*(\d+).*', r'\1', span.text.strip())
                        rec['p2'] = re.sub('.*\D(\d+).*', r'\1', span.text.strip())
                    #abs
                    for span in child.find_all('span', attrs = {'class' : 'hlFld-Abstract'}):
                        rec['abs'] = span.text.strip()
                    #date
                    for span in child.find_all('span', attrs = {'class' : 'pub-date-value'}):
                        rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
                    recs.append(rec)

i = 0
#for rec in recs:
for rec in []:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        time.sleep(60)
        driver.get(rec['artlink'])
        artpage = BeautifulSoup(driver.page_source)
    except:
        try:
            print '   wait 10 minutes'
            time.sleep(600)
            driver.get(rec['artlink'])
            artpage = BeautifulSoup(driver.page_source)
        except:
            print '  keep only', rec.keys()
            continue
    rec['autaff'] = []
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #title
            if meta['name'] == 'dc.Title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'dc.Subject':
                rec['keyw'] += re.split('; ', meta['content'])
            #abstract
            elif meta['name'] == 'twitter:description':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'dc.Date':
                rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', meta['content'])
    #authors
    for span in artpage.find_all('span'):
        for div in span.find_all('div', attrs = {'class' : 'loa-info-name'}):
            rec['autaff'].append([div.text.strip()])
            for a in span.find_all('a', attrs = {'title' : 'Orcid link'}):
                rec['autaff'][-1].append(re.sub('.*\/', r'ORCID:', a['href']))
            for div2 in span.find_all('div', attrs = {'class' : 'loa-info-affiliations-info'}):
                rec['autaff'][-1].append(div2.text.strip())
    #pages
    for span in artpage.find_all('span', attrs = {'class' : 'cit-fg-pageRange'}):
        rec['p1'] = re.sub('\D*(\d+).*', r'\1', span.text.strip())
        rec['p2'] = re.sub('.*\D(\d+).*', r'\1', span.text.strip())
    #references
    for ol in artpage.find_all('ol', attrs = {'id' : 'references'}):
        rec['refs'] = []
        for div in ol.find_all('div', attrs = {'class' : ['citationLinks', 'casRecord']}):
            div.decompose()
        for li in ol.find_all('li'):
            ref = li.text.strip()
            ref = re.sub('[\n\t\r]', ' ', ref)
            rec['refs'].append([('x', ref)])
    print '  ', rec.keys()

xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
driver.close()
