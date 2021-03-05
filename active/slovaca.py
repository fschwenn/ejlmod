# -*- coding: UTF-8 -*-
#program to harvest acta physica slovaca
# FS 2021-02-21


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


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"+'_special'

publisher = 'Slovak Academy of Sciences'

year = sys.argv[1]
issue = sys.argv[2]

toclink = 'http://www.physics.sk/aps/pub.php?y=%s&pub=aps-%s-%02i' % (year, year[2:], int(issue))
jnlfilename = "slovaca%s.%s" % (year, issue)

print "get table of content... from %s" % (toclink)

driver = webdriver.PhantomJS()
driver.implicitly_wait(30)

driver.get(toclink)
tocpage =  BeautifulSoup(driver.page_source)

recs = []
lis = []
for ul in tocpage.find_all('ul'):
    for li in ul.find_all('li'):
        lis.append(li)
if not lis:
    for td in tocpage.find_all('td', attrs = {'class' : 'home'}):
        lis.append(td)

i = 0
for li in lis:
    i += 1
    print '---{ %i/%i }---' % (i, len(lis))
    rec = {'jnl' : 'Acta Phys.Slov.', 'tc' : 'P', 'issue' : issue, 'note' : [],
           'auts' : [], 'keyw' : [], 'year' : year}
    #FFT
    for a in li.find_all('a', attrs = {'class' : 'pub'}):
        if re.search('http', a['href']):
            pdflink = a['href']
        else:
            pdflink = 'http://www.physics.sk/aps' + a['href']
        rec['FFT'] = pdflink
        rec['link'] = pdflink
        if a.text.strip() != 'pdf':
            rec['tit'] = a.text.strip()
    bs = li.find_all('b')
    if len(bs) > 3:
        #title
        rec['tit'] = bs[0].text.strip()        
        #authors
        for sup in bs[1].find_all('sup'):
            supt = ''
            for aff in re.split(',', sup.text.strip()):
                supt += ', =Aff%s' % (aff)
            sup.replace_with(supt+', ')
        authors = re.sub(' and ', ', ', bs[1].text.strip())
        for aut in re.split(' *, *', authors):
            if len(aut) > 1:
                rec['auts'].append(aut)
        #affiliations
        for it in li.find_all('i'):
            if not 'aff' in rec.keys():
                if not re.search('eceived.*ccepted', it.text):
                    rec['aff'] = []
                    for sup in it.find_all('sup'):
                        supt = 'XAFFX Aff%s=' % (sup.text.strip())
                        sup.replace_with(supt)
                    itt = re.sub('[\n\t\r]', '', it.text.strip())                
                    for aff in re.split(' *XAFFX ', itt):
                        if len(aff) > 5:
                            rec['aff'].append(aff)
    else:   
        #authors
        rec['auts'] = re.split(' *, *', bs[0].text.strip())
        
    for b in bs:
        bt = b.text.strip().lower()
        b.replace_with('XXXX' + bt + 'YYYY')
    lit = re.sub('[\n\t\r]', ' ', li.text.strip())
    lit = re.sub('  +', ' ', lit)
    parts = re.split('XXXX', lit)
    for part in parts:
        subparts = re.split('YYYY', part)
        if len(subparts) == 2:
            #abstract
            if subparts[0] == 'abstract:':
                rec['abs'] = subparts[1]
            #DOI
            elif subparts[0] == 'doi:':
                rec['doi'] = subparts[1].strip()
            #PACS
            elif subparts[0] == 'pacs:':
                rec['pacs'] = re.split(' *[;,] *', subparts[1].strip())
            #keywords
            elif subparts[0] == 'keywords:':
                rec['keyw'] = re.split(' *[,;] *', subparts[1].strip())
        #pubnote
        if re.search('Acta Physica Slovaca', part):
            rec['vol'] = re.sub('.*Acta Physica Slovaca (\d+).*', r'\1', part)
            if re.search('No\. *\d+, *\d+', part):
                rec['p1'] = re.sub('.*No\. *\d+, *(\d+).*', r'\1', part)
            else:
                rec['p1'] = re.sub('.*Acta Physica Slovaca.*?(\d+) \(.*', r'\1', part)
            if re.search('No\. *\d+, *\d+\D+\d+.*\(', part):
                rec['p2'] = re.sub('.*No\. *\d+, *\d+\D+(\d+).*\(.*', r'\1', part)
    print rec.keys()
        
    recs.append(rec)

    
#write xml
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
