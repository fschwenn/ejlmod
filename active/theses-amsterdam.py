# -*- coding: utf-8 -*-
#harvest theses from Amsterdam
#FS: 2020-11-02


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'THESES-AMSTERDAM-%s' % (stampoftoday)

publisher = 'Amsterdamh U.'

pages = 10
boringinstitutes = ['InstituteforBiodiversityandEcosystemDynamicsIBED',
                    'InstituteforLogicLanguageandComputationILLC',
                    'KortewegdeVriesInstituteforMathematicsKdVI',
                    'SwammerdamInstituteforLifeSciencesSILSInstituteforBiodiversityandEcosystemDynamicsIBED',
                    'SwammerdamInstituteforLifeSciencesSILS',
                    'InstituteforBiodiversityandEcosystemDynamicsIBEDSwammerdamInstituteforLifeSciencesSILS',
                    'VanderWaalsZeemanInstituteWZI',
                    'VantHoffInstituteforMolecularSciencesHIMSSwammerdamInstituteforLifeSciencesSILS',
                    'VantHoffInstituteforMolecularSciencesHIMS']

driver = webdriver.PhantomJS()
driver.implicitly_wait(30)
driver.get('https://dare.uva.nl')
driver.page_source

prerecs = []
for page in range(pages):
    tocurl = 'https://dare.uva.nl/search?sort=year;field1=meta;join=and;field2=meta;smode=advanced;sort-publicationDate-max=2100;typeClassification=PhD%20thesis;organisation=Faculty%20of%20Science%20(FNWI);startDoc='+str(10*page+1)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    driver.get(tocurl)
    tocpage = BeautifulSoup(driver.page_source)
    for i in tocpage.body.find_all('i', attrs = {'class' : 'fa-square-o'}):
        if i.has_attr('data-identifier'):
            rec = {'tc' : 'T',  'jnl' : 'BOOK', 'autaff' : [], 'note' : [], 'supervisor' : []}
            rec['artlink'] = 'https://dare.uva.nl/search?identifier=' + i['data-identifier']
            rec['hdl'] = '11245.1/' + i['data-identifier']
            prerecs.append(rec)
    time.sleep(2)

recs = []
i = 0 
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        driver.get(rec['artlink'])
        artpage = BeautifulSoup(driver.page_source)
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #ISBN
            elif meta['name'] == 'citation_isbn':
                rec['isbn'] = meta['content']
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
    for dl in artpage.body.find_all('dl'):
        for child in dl.children:
            try:
                child.name
            except:
                continue
            if child.name == 'dt':
                dtt = child.text
            elif child.name == 'dd':
                #author
                if dtt == 'Author':
                    for a in child.find_all('a'):
                        if a.has_attr('href'):
                            if re.search('field1=dai', a['href']):
                                rec['autaff'] = [[ a.text.strip() ]]
                            elif re.search('orcid.org', a['href']):
                                rec['autaff'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                #supervisor
                if dtt == 'Supervisors':
                    for div in child.find_all('div'):
                        for a in div.find_all('a'):
                            if a.has_attr('href'):
                                if re.search('search', a['href']):
                                    rec['supervisor'].append([ a.text.strip() ])
                                elif re.search('orcid.org', a['href']):
                                    rec['supervisor'][-1].append(re.sub('.*orcid.org\/', 'ORCID:', a['href']))
                #apges
                if dtt == 'Number of pages':
                    rec['pages'] = re.sub('\D*(\d\d+).*', r'\1', child.text.strip())
                #Institute
                if dtt == 'Institute':
                    institute = re.sub('\W', '', child.text.strip())
                    if institute in boringinstitutes:
                        keepit = False
                        print '  skip "%s"' % (institute)
                    else:
                        rec['note'].append(child.text.strip())
                #Abstract
                if dtt == 'Abstract':
                    rec['abs'] = child.text.strip()
                #HDL
                if dtt == 'Permalink':
                    for a in child.find_all('a'):
                        if a.has_attr('href'):
                            if re.search('handle.net', a['href']):
                                rec['hdl'] = re.sub('.*handle.net\/', '', a['href'])
    if keepit:
        recs.append(rec)
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



