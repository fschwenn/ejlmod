# -*- coding: utf-8 -*-
#harvest theses from Middle East Tech. U., Ankara
#works only on FS' notebook
#FS: 2021-01-02

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
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
pages = 20

publisher = 'Middle East Tech. U., Ankara'
jnlfilename = 'THESES-MiddleEastTechUAnkara-%s' % (stampoftoday)

tocurl = 'https://open.metu.edu.tr/handle/11511/158'

boringdegrees = ['M.S. - Master of Science', 'M.A. - Master of Arts', 'M.Arch. - Master of Architecture', 'Thesis (M.Arch.) -- Graduate School of Natural and Applied Sciences. Architecture.', 'Thesis (M.Arch.) -- Graduate School of Natural and Applied Sciences. Conservation of Cultural Heritage in Architecture.', 'Thesis (M.S.) -- Graduate School of Applied Mathematics. Mathematics.', 'Thesis (M.S.) -- Graduate School of Informatics. Operational Research.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Aerospace Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Archaeometry.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Biochemistry.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Biology.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Biomedical Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Biotechnology.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Building Science in Architecture.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Chemical Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Chemistry.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. City and Regional Planning.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Civil Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Computer Education and Instructional Technology.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Computer Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences . Earthquake Studies.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Earth System Science.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Electrical and Electronics Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Engineering Sciences.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Environmental Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Food Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Geodetic and Geographical Information Technologies.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Geological Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Industrial Design.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Industrial Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Mathematics and Science Education.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Mechanical Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Metallurgical and Materials Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Micro and Nanotechnology.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Mining Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Molecular Biology and Genetics', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Occupational Health and Safety.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Operational Research.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Petroleum and Natural Gas Engineering.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Physics.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Polymer Science and Technology.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Statistics.', 'Thesis (M.S.) -- Graduate School of Natural and Applied Sciences. Urban Design in City and Regional Planning Department.', 'Thesis (M.S.) -- Graduate School of Social Sciences. Elementary Science and Mathematics Education.', 'Thesis (M.S.) -- Graduate School of Social Sciences. Secondary Science and Mathematics Education.']

#driver
opts = Options()
opts.add_argument("--headless")
caps = webdriver.DesiredCapabilities().FIREFOX
caps["marionette"] = True
driver  = webdriver.Firefox(options=opts, capabilities=caps)
#webdriver.PhantomJS()
driver.implicitly_wait(30)

prerecs = []
driver.get(tocurl)
hdls = []
for page in range(pages):
    print '==={ %i/%i }====' % (page+1, pages)
    tocpage = BeautifulSoup(driver.page_source)
    for a in tocpage.body.find_all('a', attrs = {'class' : 'ui-link'}):
        if a.has_attr('href') and re.search('handle', a['href']):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'note' : []}
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            if not rec['hdl'] in hdls:
                print ' ', rec['hdl']
                rec['link'] = 'https://open.metu.edu.tr' + a['href']
                rec['tit'] = a.text.strip()
                prerecs.append(rec)
                hdls.append(rec['hdl'])
    #next page
    driver.find_element_by_class_name("ui-paginator-next").click()
    time.sleep(2)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        driver.get(rec['link'])
        artpage = BeautifulSoup(driver.page_source)
    except:
        print ' ... try again in 5 minutes'
        time.sleep(300)
        driver.get(rec['link'])
        artpage = BeautifulSoup(driver.page_source)       
    time.sleep(3)
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' the ', meta['content']):
                    rec['abs'] = meta['content']
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d\d', meta['content']):
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', meta['content'])
            #license
            elif meta['name'] == 'DC.rights,DCTERMS.URI':
                rec['license'] = {'url' : meta['content']}
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', meta['content'])
                if re.search('[12]\d\d\d\-\d', meta['content']):
                    month = re.sub('.*[12]\d\d\d\-(\d\d?).*', r'\1', meta['content'])
                    rec['date'] += '-%02i' % (int(month))
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #type
            elif meta['name'] == 'DC.description':
                if meta['content'] in boringdegrees:
                    print ' skip "%s"' % (meta['content'])
                    keepit = False
                elif not meta['content'] in ['Ph.D. - Doctoral Program']:
                    rec['note'].append(meta['content'])
    if keepit:
        print rec.keys()
        recs.append(rec)

#closing of files and printing
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
