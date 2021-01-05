# -*- coding: utf-8 -*-
#harvest theses from Leuven U.
#FS: 2020-12-22

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Leuven U.'
pages = 7 
jnlfilename = 'THESES-LEUVEN-%sY' % (stampoftoday)

recs = []

driver = webdriver.PhantomJS()
driver.implicitly_wait(120)
driver.set_page_load_timeout(30)
for page in range(pages):
    tocurl = 'https://limo.libis.be/primo-explore/search?query=any,contains,lirias,AND&tab=default_tab&search_scope=Lirias&sortby=date&vid=Lirias&facet=local16,include,thesis-dissertation&lang=en_US&mode=advanced&offset=' + str(10*page)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    driver.get(tocurl)
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'result-item-text')))
    tocpage = BeautifulSoup(driver.page_source, features="lxml")
    time.sleep(10)
    for div in tocpage.find_all('div', attrs = {'class' : 'result-item-text'}):
        for a in div.find_all('a', attrs = {'class' : 'md-primoExplore-theme'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'oa' : False}
            liriasnr = a['data-emailref']
            rec['doi'] = '20.2000/Leuven/' + liriasnr
            rec['link'] = 'https://limo.libis.be/primo-explore/fulldisplay?docid=' + liriasnr + '&context=L&vid=Lirias&search_scope=Lirias&tab=default_tab&lang=en_US'
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    driver.get(rec['link'])
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.CLASS_NAME, 'item-detail')))
    artpage = BeautifulSoup(driver.page_source, features="lxml")
    time.sleep(20)
    #abstract
    for meta in artpage.find_all('meta', attrs = {'name' : 'description'}):
        rec['abs'] = meta['content']
    #title
    for span in artpage.find_all('span', attrs = {'data-field-selector' : '::title'}):
        for span2 in span.find_all('span', attrs = {'dir' : 'auto'}):
            rec['tit'] = span2.text.strip()
    #author
    for span in artpage.find_all('span', attrs = {'data-field-selector' : 'creator'}):
        for span2 in span.find_all('span', attrs = {'dir' : 'auto'}):
            rec['autaff'] = [[ span2.text.strip(), publisher ]]
    #supervisor
    for span in artpage.find_all('span', attrs = {'data-field-selector' : 'contributor'}):
        for span2 in span.find_all('span', attrs = {'dir' : 'auto'}):
            svs = re.sub('\(.*?\)', '', span2.text.strip())
            for sv in re.split(' *; *', svs):
                rec['supervisor'].append([sv])
    #date
    for span in artpage.find_all('span', attrs = {'data-field-selector' : 'creationdate'}):
        for span2 in span.find_all('span', attrs = {'dir' : 'auto'}):
            rec['date'] = span2.text.strip()
    #pen access
    for div in artpage.find_all('div', attrs = {'class' : 'open-access-mark'}):
        for svg in div.find_all('svg', attrs = {'id' : 'open-access_cache14'}):
            rec['oa'] = True
    #fulltext
    if rec['oa']:
        for a in artpage.find_all('a', attrs = {'class' : 'arrow-link'}):
            if re.search('\.pdf', a.text):
                rec['FFT'] = a['href']
    print rec.keys()
	


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
