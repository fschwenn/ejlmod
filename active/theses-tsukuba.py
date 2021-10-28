# -*- coding: utf-8 -*-
#harvest theses from Tsukuba U.
#FS: 2021-10-21

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
import requests

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
pages = 1
rpp = 20

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Tsukuba U.'

#driver
opts = Options()
opts.add_argument("--headless")
caps = webdriver.DesiredCapabilities().FIREFOX
caps["marionette"] = True
driver  = webdriver.Firefox(options=opts, capabilities=caps)
#webdriver.PhantomJS()
driver.implicitly_wait(30)

recs = []
jnlfilename = 'THESES-TSUKUBA-%s' % (stampoftoday)
deps = [('253', 1), ('250', 1), ('254', 3)]
for (dep, pages) in deps:
    for i in range(pages):
        tocurl = 'https://tsukuba.repo.nii.ac.jp/items/export?page=' + str(i+1) + '&size=' + str(rpp) + '&sort=-controlnumber&search_type=2&q=' + dep
        print '==={ %s }==={ %i/%i }==={ %s }===' % (dep, i+1, pages, tocurl)
        driver.get(tocurl)
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, 'ng-binding')))
        tocpage = BeautifulSoup(driver.page_source, features="lxml")
        for a in tocpage.body.find_all('a', attrs = {'class' : 'ng-binding'}):
            if a.has_attr('href') and re.search('records', a['href']):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
                rec['link'] = 'https://tsukuba.repo.nii.ac.jp' + a['href']
                rec['doi'] = '30.3000/Tsukuba' + a['href'] 
                recid = int(re.sub('\D', '', a['href']))
                rec['note'].append('DOI guessed from theses ID: 10.15068/%010i' % (recid))
                recs.append(rec)            
        time.sleep(4)

i = 0
for rec in recs:
    i += 1
    disstyp = False
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['link'])
    driver.get(rec['link'])
    artpage = BeautifulSoup(driver.page_source, features="lxml")
    for span in artpage.find_all('span', attrs = {'class' : 'pull-right'}):
        st = re.sub('[\n\t\r]', '', span.text.strip())
        if re.search('handle.net', st):
            rec['hdl'] = re.sub('.*handle.net\/', '', st)
        elif  re.search('doi.org', st):
            rec['doi'] = re.sub('.*doi.org\/', '', st)
    time.sleep(2)    
    artjson = requests.get(rec['link'] + '/export/json').json()          
    time.sleep(4)
    #date
    if 'item_12_date_granted_46' in artjson['metadata'].keys():
        for entry in artjson['metadata']['item_12_date_granted_46']['attribute_value_mlt']:
            if 'subitem_dategranted' in entry.keys():
                rec['date'] = entry['subitem_dategranted']
    elif 'publish_date' in artjson['metadata'].keys():
        rec['date'] = artjson['metadata']['publish_date']
    #abstract
    if 'item_12_description_4' in artjson['metadata'].keys():
        for entry in artjson['metadata']['item_12_description_4']['attribute_value_mlt']:
            if 'subitem_description_type' in entry.keys() and entry['subitem_description_type'] == 'Abstract':
                rec['abs'] = entry['subitem_description']
    #PIDs
    if 'item_12_identifier_34' in artjson['metadata'].keys():
        for entry in artjson['metadata']['item_12_identifier_34']['attribute_value_mlt']:
            if 'subitem_identifier_type' in entry.keys():
                if entry['subitem_identifier_type'] == 'HDL':
                    rec['hdl'] = re.sub('.*handle.net\/', '', entry['subitem_identifier_uri'])
                elif entry['subitem_identifier_type'] == 'DOI':
                    rec['doi'] = re.sub('.*doi.org\/', '', entry['subitem_identifier_uri'])
    #PDF
    if 'item_files' in artjson['metadata'].keys():
        for entry in artjson['metadata']['item_files']['attribute_value_mlt']:
            if 'accessrole' in entry.keys():
                if entry['accessrole'] == 'open_access':
                    for entry in artjson['metadata']['item_files']['attribute_value_mlt']:
                        rec['FFT'] = entry['url']['url']
    #language
    for entry in artjson['metadata']['item_language']['attribute_value_mlt']:
        if entry['subitem_language'] == 'jpn':
            rec['language'] = 'Japanese'
        elif entry['subitem_language'] != 'eng':
            rec['note'].append('language:'+entry['subitem_language'])
            rec['language'] = entry['subitem_language']
    #title
    rec['tit'] = artjson['metadata']['title'][0]
    for entry in artjson['metadata']['item_titles']['attribute_value_mlt']:
        if 'subitem_title_language' in entry.keys():
            if entry['subitem_title_language'] == 'en':
                if 'language' in rec.keys():
                    rec['transtit'] = entry['subitem_title']
                else:
                    rec['tit'] = entry['subitem_title']
            elif entry['subitem_title_language'] == 'ja':
                if 'language' in rec.keys():
                    rec['tit'] = entry['subitem_title']
                else:
                    rec['otits'] = [entry['subitem_title']]
        elif not 'tit' in rec.keys():
            rec['tit'] = entry['subitem_title']
    #author
    for entry in artjson['metadata']['item_creator']['attribute_value_mlt']:
        janame = False
        if 'creatorNames' in entry.keys():
            for subentry in entry['creatorNames']:
                if 'creatorNameLang' in subentry.keys():
                    if subentry['creatorNameLang'] == 'en':
                        rec['auts'] = [ subentry['creatorName'] ]
                    elif subentry['creatorNameLang'] == 'ja':
                        janame = subentry['creatorName']
                else:
                    rec['auts'] = [ subentry['creatorName'] ]
            if janame:
                if 'auts' in rec.keys():
                    rec['auts'][-1] += ', CHINESENAME: ' + janame
                else:
                    rec['auts'] = [ subentry['creatorName'] ]
        rec['aff'] = [publisher]
    print '    ', rec.keys()
    print '    ', rec

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
