# -*- coding: utf-8 -*-
#harvest theses from Northeastern U.
#FS: 2020-11-04

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Northeastern U. (main)'
rpp = 20
driver = webdriver.PhantomJS()
driver.implicitly_wait(30)

departments = [('Northeastern U.', '228'), ('Northeastern U., Math. Dept.', '200')]
jnlfilename = 'THESES-NEU-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for (aff, depid) in departments:
    tocurl = 'https://repository.library.northeastern.edu/collections/neu:'+depid+'?utf8=%E2%9C%93&sort=date_ssi+desc&per_page=' + str(rpp) + '&utf8=%E2%9C%93&id=neu%3A' + depid + '&rows=' + str(rpp)
    print '==={ %s }===' % (tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(5)
    for h4 in tocpage.find_all('h4', attrs = {'class' : 'drs-item-title'}):
        for a in h4.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'depaff' : aff, 'supervisor' : [], 'note' : []}
            rec['artlink'] = 'https://repository.library.northeastern.edu' + a['href']
            rec['tit'] = a.text.strip()
            if depid == '200':
                rec['fc'] = 'm'
            recs.append(rec)

j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['artlink'])
    try:
        driver.get(rec['artlink'])
        req = urllib2.Request(rec['artlink'])
        artpage = BeautifulSoup(driver.page_source, features="lxml")
        time.sleep(5)
    except:
        print 'wait 10 minutes'
        time.sleep(600)
        try:
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
            time.sleep(30)
        except:
            continue
    for div in artpage.find_all('div', attrs = {'class' : 'drs-item-add-details'}):
        for child in div.children:
            try:
                name = child.name
            except:
                continue
            if name == 'dt':
                dtt = child.text.strip()
            elif name == 'dd':
                #title
                if dtt == 'Title:':
                    rec['tit'] = child.text.strip()
                #author
                elif dtt == 'Creator:':
                    rec['autaff'] = [[ re.sub(' *\(.*', '', child.text.strip()), rec['depaff'] ]]
                #supervisor
                elif dtt == 'Contributor:':
                    for br in child.find_all('br'):
                        br.replace_with('XXX')
                    for contributor in re.split(' *XXX *', child.text.strip()):
                        if re.search('\(Advisor', contributor):
                            rec['supervisor'].append([re.sub(', \d.*', '', re.sub(' *\(Advisor.*', '', contributor))])
                #date
                elif dtt == 'Date Awarded:':
                    rec['date'] = re.sub('.*?([12]\d\d\d).*', r'\1', child.text.strip())
                #abstract
                elif dtt == 'Abstract/Description:':
                    rec['abs'] = child.text.strip()
                #keywords
                elif dtt == 'Subjects and keywords:':
                    for br in child.find_all('br'):
                        br.replace_with('XXX')
                    rec['keyw'] = re.split(' *XXX *', child.text.strip())
                #HDL
                elif dtt in ['Permanent Link:', 'Permanent URL:']:
                    if re.search('handle.net\/', child.text):
                        rec['hdl'] = re.sub('.*handle.net\/', '', child.text.strip())
                #DOI
                elif dtt == 'DOI:':
                    rec['doi'] = re.sub('.*doi.org\/', '', child.text.strip())
                #rights
                #elif dtt == 'Use and reproduction:':
                #    rec['note'].append(child.text.strip())
    #fulltext
    for section in artpage.body.find_all('section', attrs = {'class' : 'drs-item-derivatives'}):
        for a in section.find_all('a', attrs = {'title' : 'PDF'}):
            rec['hidden'] = 'https://repository.library.northeastern.edu' + a['href']
    print '  ', rec.keys()

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
