# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest theses from Karlsruhe Insitute of Technolgy
# FS 2020-01-13

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import datetime
import time 
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'KIT, Karlsruhe'

typecode = 'T'

jnlfilename = 'THESES-KIT-%s' % (stampoftoday)
pages = 4 

#driver
opts = Options()
opts.add_argument("--headless")
caps = webdriver.DesiredCapabilities().FIREFOX
caps["marionette"] = True
driver = webdriver.Firefox(options=opts, capabilities=caps)
driver.implicitly_wait(30)
driver.set_window_position(0, 0)
driver.set_window_size(1920, 10800)

recs = []
for page in range(pages):
    tocurl = 'https://primo.bibliothek.kit.edu/primo-explore/search?query=any,contains,*&tab=kit&sortby=date&vid=KIT&facet=local5,include,istHochschulschrift&mfacet=local3,include,istFachPhys,1&mfacet=local3,include,istFachMath,1&mode=simple&offset=' + str(10*page) + '&fn=search'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    newrecs = []
    try:
        driver.get(tocurl)
        time.sleep(15)
        tocpage = BeautifulSoup(driver.page_source, features="lxml")
        time.sleep(4)
    except:
        print "retry %s in 300 seconds" % (tocurl)
        time.sleep(300)
        driver.get(tocurl)
        tocpage = BeautifulSoup(driver.page_source, features="lxml")
    for div in tocpage.find_all('div', attrs = {'class' : 'list-item-wrapper'}):
        for div2 in div.find_all('div', attrs = {'class' : 'list-item-primary-content'}):
            rec = {'jnl' : 'BOOK', 'tc' : 'T', 'note' : [], 'keyw' : []}
            rec['data-recordid'] = div2['data-recordid']
            rec['artlink'] = 'https://primo.bibliothek.kit.edu/primo-explore/fulldisplay?docid=' + div2['data-recordid']+ '&context=L&vid=KIT&lang=de_DE'
            recs.append(rec)
    print '  ', len(recs)
        

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    isbns = []
    try:
        driver.get(rec['artlink'])
        time.sleep(4)
        artpage = BeautifulSoup(driver.page_source, features="lxml")
        time.sleep(4)
    except:
        print "retry %s in 300 seconds" % (tocurl)
        time.sleep(300)
        driver.get(rec['artlink'])
        time.sleep(4)        
        artpage = BeautifulSoup(driver.page_source, features="lxml")
    tabelle = {}
    for div in artpage.body.find_all('div', attrs = {'class' : 'full-view-inner-container'}):
        for div2 in div.find_all('div', attrs = {'class' : 'standorte'}):
            for div3 in div2.find_all('div', attrs = {'class' : 'item-details-element-container'}):
                rec['keyw'] += re.split(' \/ ', div3.text.strip())
        for div2 in div.find_all('div', attrs = {'class' : 'full-view-section-content'}):
            for div3 in div2.find_all('div', attrs = {'class' : 'layout-block-xs'}):
                for span in div3.find_all('span', attrs = {'class' : 'bold-text'}):
                    for span2 in div3.find_all('span', attrs = {'class' : 'ng-binding'}):
                        if span.text.strip() in tabelle.keys():
                            tabelle[span.text.strip()].append(span2.text.strip())
                        else:
                            tabelle[span.text.strip()] = [span2.text.strip()]
    if 'Titel' in tabelle.keys():
        rec['tit'] = re.sub(' *\/ von.*', '', tabelle['Titel'][0])
    if 'Jahr' in tabelle.keys():
        rec['year'] = tabelle['Jahr'][0]
    if 'Sprache' in tabelle.keys():
        if tabelle['Sprache'][0] == 'Deutsch':
            rec['language'] = 'German'
    if 'Verfasser' in tabelle.keys():
        rec['autaff'] = [[ re.sub(' *\[.*', '', tabelle['Verfasser'][0]), publisher ]]
    if 'Auflage / Umfang' in tabelle.keys():
        if re.search('\d\d+ Seiten', tabelle['Auflage / Umfang'][0]):
            rec['pages'] = re.sub('.*?(\d\d+) Seiten.*', r'\1', tabelle['Auflage / Umfang'][0])
    if 'Identifikator' in tabelle.keys():
        for ide in tabelle['Identifikator']:
            if re.search('DOI: 10', ide):
                rec['doi'] = re.sub('.*?(10.*)', r'\1', ide)
            elif re.search('\D978.?\d.?\d.?\d', ide):
                isbn = re.sub('\-', '', re.sub('.*?(978.*[\dX]).*', r'\1', ide))
                if not isbn in isbns:
                    isbns.append(isbn)
    if 'doi' in rec.keys():
        if re.search('^10.5445', rec['doi']):
            print '   checking primo-page'
            try:
                time.sleep(10)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('https://doi.org/'+rec['doi']), features="lxml")
            except:
                print "retry %s in 180 seconds" % (rec['link'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('https://doi.org/'+rec['doi']), features="lxml")
            for meta in artpage.head.find_all('meta'):
                if meta.has_attr('name'):
                    #abstract
                    if meta['name'] == 'citation_abstract':
                        rec['abs'] = meta['content']
                    #ISBN
                    elif meta['name'] == 'citation_isbn':
                        isbn = re.sub('\-', '', meta['content'])
                        if not isbn in isbns:
                            isbns.append(isbn)
                    #fulltext
                    elif meta['name'] == 'citation_pdf_url':
                        rec['FFT'] = meta['content']
            for table in artpage.body.find_all('table', attrs = {'class' : 'table'}):
                for tr in table.find_all('tr'):
                    tds = tr.find_all('td')
                    if len(tds) == 2:
                        #Keywords
                        if re.search('Schlagw', tds[0].text.strip()):
                            for keyw in re.split(', ', tds[1].text.strip()):
                                if not keyw in rec['keyw']:
                                    rec['keyw'].append(keyw)
                        #Language
                        elif tds[0].text.strip() == 'Sprache':
                            if tds[1].text.strip() != 'Englisch':
                                if tds[1].text.strip() == 'Deutsch':
                                    rec['language'] = 'german'
                                else:
                                    rec['language'] = tds[1].text.strip()
                        #pages
                        elif tds[0].text.strip() == 'Umfang':
                            if re.search('\d\d\d', tds[1].text.strip()):
                                rec['pages'] = re.sub('.*?(\d\d\d+).*', r'\1', tds[1].text.strip())
                        #supervisor
                        elif re.search('Betreuer', tds[0].text):
                            rec['supervisor'] = [[ re.sub('Prof\. ', '', re.sub('Dr\. ', '', tds[1].text.strip())) ]]
                        #date
                        elif re.search('Pr.fungsdatum', tds[0].text):
                            rec['MARC'] = [ ['500', [('a', 'Presented on ' + re.sub('(\d\d).(\d\d).(\d\d\d\d)', r'\3-\2-\1', tds[1].text.strip()))] ] ]
                        #institue
                        elif tds[0].text.strip() == 'Institut':
                            rec['note'].append(tds[1].text.strip())
                        #urn
                        elif tds[0].text.strip() == 'Identifikator':
                            for br in tds[1].find_all('br'):
                                br.replace_with('#')
                            for tdt in re.split('#',  re.sub('[\n\t\r]', '#', tds[1].text.strip())):
                                if re.search('urn:nbn', tdt):
                                    rec['urn'] = re.sub('.*?(urn:nbn.*)', r'\1', tdt.strip())
            #license
            for a in artpage.body.find_all('a', attrs = {'class' : 'with-popover'}):
                if a.has_attr('data-content'):
                    adc = a['data-content']
                    if re.search('creativecommons.org', adc):
                        rec['license'] = {'url' : re.sub('.*(http.*?) target.*', r'\1', adc)}                                        
    else:
        rec['doi'] = '20.2000/KIT/'+rec['data-recordid']
        rec['link'] = rec['artlink']
    if isbns:
        rec['isbns'] = []
        for isbn in isbns:
            rec['isbns'].append([('a', isbn)])
    
    print rec
    print '  '+', '.join(['%s(%i)' % (k, len(rec[k])) for k in rec.keys()])

    
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
 
            
    
