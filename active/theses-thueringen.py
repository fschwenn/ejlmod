# -*- coding: utf-8 -*-
#harvest theses from Thueringen
#FS: 2020-04-30


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
    
publisher = 'db-thueringen.de'

typecode = 'T'

startyear = str(now.year - 1)
rpp = 50

driver = webdriver.PhantomJS()
driver.implicitly_wait(30)

for ddc in ['500', '510', '530']:
    recs = []
    jnlfilename = 'THESES-THUERINGEN-%s-%s' % (stampoftoday, ddc)
    tocurl = 'https://www.db-thueringen.de/servlets/solr/select?q=%2Bcategory.top%3A%22SDNB%5C%3A' + ddc + '%22+%2Bmods.dateIssued%3A%7B' + str(startyear) + '+TO+*%5D+%2Bstate%3A%22published%22+%2Bcategory.top%3A%22mir_genres%5C%3Adissertation%22+%2BobjectType%3A%22mods%22&fl=*&sort=mods.dateIssued+desc&version=4.5&mask=content%2Fsearch%2Fcomplex.xed&rows=' + str(rpp)
    print '==={ DDC=%s }==={ 1 }==={ %s }===' % (ddc, tocurl)
    driver.get(tocurl)
    tocpages = [ BeautifulSoup(driver.page_source) ]
    for h1 in tocpages[0].find_all('h1'):
        print h1.text.strip()
        print h1.text.strip()
        if re.search('\d', h1.text):
            numoftheses = int(re.sub('\D', '', h1.text.strip()))
            numofpages = (numoftheses-1) / rpp  + 1
        else:
            numoftheses = 0
            numofpages = 0
    if not numoftheses: continue
    
    for i in range(numofpages-1):
        tocurl = 'https://www.db-thueringen.de/servlets/solr/select?q=%2Bcategory.top%3A%22SDNB%5C%3A' + ddc + '%22+%2Bmods.dateIssued%3A%7B' + str(startyear) + '+TO+*%5D+%2Bstate%3A%22published%22+%2Bcategory.top%3A%22mir_genres%5C%3Adissertation%22+%2BobjectType%3A%22mods%22&fl=*&sort=mods.dateIssued+desc&version=4.5&mask=content%2Fsearch%2Fcomplex.xed&start=' + str(rpp*(i+1)) + '&rows=' + str(rpp)
        print '==={ DDC=%s }==={ %i/%i }==={ %s }===' % (ddc, i+2, numofpages, tocurl)
        driver.get(tocurl)
        tocpages.append(BeautifulSoup(driver.page_source))
    
    i = 0
    recs = []
    for tocpage in tocpages:
        i += 1
        j = 0
        divs = tocpage.find_all('div', attrs = {'class' : 'single_hit_option'})
        for div in divs:
            j += 1
            for a in div.find_all('a'):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
                identifier = re.sub('.*id=(dbt_mods_\d+).*', r'\1', a['href'])
                rec['artlink'] = 'https://www.db-thueringen.de/receive/' + identifier
                print '---{ DDC=%s }---{ %i/%i }---{ %i/%i }---{ %s }---' % (ddc, i, len(tocpages), j, len(divs), rec['artlink'])
                try:
                    driver.get(rec['artlink'])
                    artpage = BeautifulSoup(driver.page_source)
                    time.sleep(3)
                except:
                    try:
                        print "retry %s in 180 seconds" % (rec['artlink'])
                        time.sleep(180)
                        artpage = BeautifulSoup(driver.page_source)
                        time.sleep(3)
                    except:
                        print "no access to %s" % (rec['artlink'])
                        continue    
                for meta in artpage.head.find_all('meta'):
                    if meta.has_attr('name'):
                        #author
                        if meta['name'] == 'DC.creator':
                            author = re.sub(' *\[.*', '', meta['content'])
                            rec['autaff'] = [[ author ]]
        #                                rec['autaff'][-1].append(publisher)
                        #abstract
                        elif meta['name'] == 'DC.description':
                            rec['abs'] = meta['content']
                        #title
                        elif meta['name'] == 'DC.title':
                            rec['tit'] = meta['content']
                        #date
                        elif meta['name'] == 'DC.date':
                            rec['date'] = meta['content']
                            rec['year'] = meta['content']
                        #DOI/URN
                        elif meta['name'] == 'DC.identifier':
                            if re.search('doi.org\/10', meta['content']):
                                rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
                            elif re.search('nbn\-resolving.org', meta['content']):
                                rec['urn'] = re.sub('.*nbn\-resolving.org\/', '', meta['content'])
                        #license
                        elif meta['name'] == 'DC.rights':
                            if re.search('creativecommons.org', meta['content']):
                                rec['license'] = {'url' : meta['content']}
                        #DOI
                        elif meta['name'] == 'citation_doi':
                            rec['doi'] = meta['content']
                for dl in artpage.find_all('dl'):
                    for child in dl.children:
                        try:
                            child.name
                        except:
                            continue
                        if child.name == 'dt':
                            dtt = child.text
                        elif child.name == 'dd':
                            ddt = child.text.strip()
                            if ddt:
                                #language
                                if dtt in ['Sprache', 'Language:'] and ddt in['Deutsch', 'German']:
                                    rec['language'] = 'german'
                                #pages
                                elif dtt in ['Umfang', 'Extent:']:
                                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', ddt)
                                #affiliation
                                elif dtt in ['Einrichtung:', 'Hosting institution:']:
                                    rec['autaff'][0].append(ddt + ', Deutschland')
                                #keywords
                                elif re.search('(Schlagw|Keywords)', dtt):
                                    for sup in child.find_all('sup'):
                                        sup.decompose()
                                    rec['keyw'] = re.split('; ', child.text.strip())
                #fulltext
                for noscript in artpage.find_all('noscript'):
                    nt = noscript.text.strip()
                    if re.search('\.pdf"', nt):
                        pdflink = re.sub('.*?(http.*?pdf)".*', r'\1', nt)
                        if 'license' in rec.keys():
                            rec['FFT'] = pdflink
                        else:
                            rec['hidden'] = pdflink
                #DOI ?
                if not 'doi' in rec.keys():
                    rec['link'] = driver.current_url
                        
                print '   ', rec.keys()
                recs.append(rec)
                
    
    #closing of files and printing
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
        
