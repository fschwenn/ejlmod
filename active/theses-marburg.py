# -*- coding: utf-8 -*-
#harvest theses from Philipps U. Marburg
#FS: 2022-04-19


import getopt
import sys
import os
import urllib2
import urlparse
from bs4 import BeautifulSoup
import re
import ejlmod2
import codecs
import datetime
import time
import json
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Philipps U. Marburg'

pages = 1

jnlfilename = 'THESES-MARBURG-%s' % (stampoftoday)

recs = []
hdr = {'User-Agent' : 'Magic Browser'}
driver = webdriver.PhantomJS()
driver.implicitly_wait(300)
for (fc, fachbereich) in [('', 'Fachbereich+Physik'), ('m', 'Fachbereich+Mathematik+und+Informatik')]:
    for page in range(pages):
        tocurl = 'https://archiv.ub.uni-marburg.de/ubfind/Search/Results?sort=year&filter%5B%5D=%7Eformat%3A%22DoctoralThesis%22&filter%5B%5D=building%3A%22' + fachbereich + '%22&join=AND&bool0%5B%5D=AND&lookfor0%5B%5D=&type0%5B%5D=AllFields&page=' + str(page+1)
        print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for div in tocpage.body.find_all('div', attrs = {'class' : 'result-body'}):
            for a in div.find_all('a', attrs = {'class' : 'title'}):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : []}
                rec['artlink'] = 'https://archiv.ub.uni-marburg.de' + a['href']
                recs.append(rec)
        time.sleep(5)

i = 0
redoi = re.compile('.*(citeseerx.ist.*doi=|doi.org\/|link.springer.com\/|tandfonline.com\/doi\/abs\/|link.springer.com\/article\/|link.springer.com\/chapter\/|nlinelibrary.wiley.com\/doi\/|ournals.aps.org\/pr.*\/abstract\/|scitation.aip.org\/.*)(10\.[0-9]+\/.*)')
rebase = re.compile('base\-search.net')
for rec in recs:
    i += 1
    time.sleep(3)
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'] + '/Description', headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for tr in  artpage.body.find_all('tr'):
        for th in tr.find_all('th'):
            tht = th.text.strip()
        for td in tr.find_all('td'): 
            #language
            if tht in ['Sprache', 'Language:']:
                language = td.text.strip()
                if not language in ['Englisch', 'English']:
                    if language == 'Deutsch':
                        rec['language'] = 'German'
                    else:
                        rec['language'] = language
            #keywords
            elif tht in ['Subjects:', 'Schlagworte:']:
                for a in td.find_all('a'):
                    rec['keyw'].append(a.text.strip())
            #abstract
            elif tht in ['Summary:', 'Zusammenfassung:']:
                rec['abs'] = td.text.strip()
            #pages
            elif tht in ['Physical Description:', 'Umfang']:
                pages = td.text.strip()
                if re.search('\d\d', pages):
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', pages)
            #DOI
            elif tht == 'DOI:':
                rec['doi'] = re.sub('.*doi.org\/', '', td.text.strip())
    #title
    for h1 in artpage.body.find_all('h1', attrs = {'property' : 'name'}):
        rec['tit'] = h1.text.strip()
    #author
    for span in artpage.body.find_all('span', attrs = {'property' : 'author'}):
        rec['autaff'] = [[ span.text.strip(), publisher ]]
    #supervisor
    for span in artpage.body.find_all('span', attrs = {'property' : 'contributor'}):
        for sp in span.find_all('span', attrs = {'class' : 'author-property-role'}):
            if re.search('(advisor|etreuer)', sp.text):
                sp.decompose()
                rec['supervisor'].append([re.sub(' *\(.*', '', span.text.strip())])
    #date
    for span in artpage.body.find_all('span', attrs = {'property' : 'datePublished'}):
        rec['date'] = span.text.strip()
    #PDF
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'citation_pdf_url'}):
        rec['hidden'] = 'https:' + meta['content']
    #references
    time.sleep(2)
    driver.get(rec['artlink'] + '/References')
    refpage = BeautifulSoup(driver.page_source, features="lxml")
    for div in refpage.body.find_all('div', attrs = {'class' : 'references-tab'}):
        rec['refs'] = []
        for p in div.find_all('p'):
            pt = re.sub('\.$', '', p.text.strip())
            doi = False
            for a in p.find_all('a'):
                link = a['href']
            if redoi.search(link):
                doi = redoi.sub(r'doi:\2', link)
            elif not rebase.search(link):
                pt += ', ' + link
            if doi:
                rec['refs'].append([('x', pt), ('a', doi)])
            else:
                rec['refs'].append([('x', pt)])
    print '   ', rec.keys()
    if not 'doi' in rec.keys():
        rec['doi'] = '20.2000/Marburg/' + re.sub('\W', '', rec['artlink'][40:])
        rec['link'] = rec['artlink']

#closing of files and printing
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
