# -*- coding: UTF-8 -*-
#!/usr/bin/python
#program to harvest Science
# FS 2020-11-24

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
import ssl
import os
import datetime


xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

publisher = 'American Association for the Advancement of Science'
jnl = sys.argv[1]
year = sys.argv[2]
now = datetime.datetime.now()
hdr = {'User-Agent' : 'Magic Browser'}
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.options import Options

if jnl == 'science':
    jnlname = 'Science'
elif jnl == 'sciadv':
    jnlname = 'Sci.Adv.'

#driver
opts = Options()
opts.add_argument("--headless")
caps = webdriver.DesiredCapabilities().FIREFOX
caps["marionette"] = True
driver  = webdriver.Firefox(options=opts, capabilities=caps)
#webdriver.PhantomJS()
driver.implicitly_wait(30)

def getissuenumbers(jnl, year):
    issues = []
    tocurl = 'https://%s.sciencemag.org/content/by/year/%s' % (jnl, year)
    tocurl = 'https://www.science.org/loi/%s/group/y%s' % (jnl, year)
    print tocurl
    driver.get(tocurl)
    tocpage = BeautifulSoup(driver.page_source, features="lxml")
    #tocreq = urllib2.Request(tocurl, headers=hdr)
    #tocpage = BeautifulSoup(urllib2.urlopen(tocreq, context=ctx), features="lxml")
    for a in tocpage.find_all('a', attrs = {'class' : 'd-flex'}):
            vol = re.sub('.*[a-z]\/(\d+).*', r'\1', a['href'])
            issue = re.sub('.*\/(\d+).*', r'\1', a['href'])
            if re.search('^\d+$', vol) and  re.search('^\d+$', issue):
                issues.append((vol, issue))
    issues.sort()
    print 'available', issues
    return issues

def getdone():
    if jnl == 'science':
        reg = re.compile('science(\d+)\.(\d+)')
    elif jnl == 'sciadv':
        reg = re.compile('sciadv(\d+)\.(\d+)')
    ejldir = '/afs/desy.de/user/l/library/dok/ejl'
    issues = []
    for directory in [ejldir+'/onhold', ejldir+'/zu_punkten/enriched', ejldir+'/backup', ejldir+'/backup/' + str(now.year-1)]:
        for datei in os.listdir(directory):
            if reg.search(datei):
                regs = reg.search(datei)
                vol = regs.group(1)
                issue = regs.group(2)
                if not (vol, issue) in issues:
                    issues.append((vol, issue))
    issues.sort()
    print 'done', issues
    return issues

def harvestissue(jnl, vol, issue):
    tocurl = 'https://www.science.org/toc/%s/%s/%s' % (jnl, vol, issue)
    print "   get table of content of %s %s.%s via %s ..." % (jnlname, vol, issue, tocurl)
    driver.get(tocurl)
    tocpage = BeautifulSoup(driver.page_source, features="lxml")
    recs = []
    for sct in tocpage.find_all('section', attrs = {'class' : 'toc__section'}):
        for h4 in sct.find_all('h4'):
            scttit = h4.text.strip()
        if scttit in ['Editorial', 'In Brief', 'In Depth', 'Feature', 'Working Life',
                      'Books et al.', 'Policy Forum', 'Perspectives', 'Association Affairs',
                      'Products & Materials', 'Careers',
                      'In Other Journals', 'In Science Journals', 'Neuroscience', 'News', 
                      'Social and Interdisciplinary Sciences', 'Biomedicine and Life Sciences']:
            print '      skip', scttit
        else:
            for h3 in sct.find_all('h3'):
                for a in h3.find_all('a'):
                    rec = {'tc' : 'P', 'jnl' : jnlname, 'vol' : vol, 'issue' : issue,
                           'year' : year, 'autaff' : [], 'note' : [scttit], 'refs' : []}
                    rec['artlink'] = 'https://www.science.org%s' % (a['href'])
                    recs.append(rec)
    #check article pages
    i = 0
    for rec in recs:
        i += 1
        print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
        try:
            time.sleep(60)
            driver.get(rec['artlink'])
            page = BeautifulSoup(driver.page_source, features="lxml")
        except:
            print "retry in 300 seconds"
            time.sleep(300)
            pagreq = urllib2.Request(rec['artlink'], headers=hdr)
            page = BeautifulSoup(urllib2.urlopen(pagreq), features="lxml")
        #DOI
        rec['doi'] = re.sub('.*?(10\.\d+\/)', r'\1', rec['artlink'])
        for meta in page.find_all('meta'):
            if meta.has_attr('name') and meta.has_attr('content'):
                #title
                if meta['name'] == 'dc.Title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'dc.Date':
                    rec['date'] = meta['content']
                #pages
                if meta['name'] == 'dc.Identifier':
                    if meta.has_attr('scheme'):
                        if meta['scheme'] == 'publisher-id':
                            rec['p1'] = meta['content']
                        elif meta['scheme'] == 'doi':
                            rec['doi'] = meta['content']
        #authors and affiliations
        for div in page.find_all('div', attrs = {'property' : 'author'}):
            for span in div.find_all('span', attrs = {'property' : 'familyName'}):
                name = span.text.strip()
            for span in div.find_all('span', attrs = {'property' : 'givenName'}):
                name += ', ' + span.text.strip()
            rec['autaff'].append([name])
            for a in div.find_all('a', attrs = {'class' : 'orcid-id'}):
                rec['autaff'][-1].append(re.sub('.*\/', 'ORCID:', a['href']))
            for div2 in div.find_all('div', attrs = {'property' : 'organization'}):
                rec['autaff'][-1].append(div2.text.strip())
        #abstract
        for section in page.find_all('section', attrs = {'id' : 'abstract'}):
            for h2 in section.find_all('h2'):
                h2.decompose()
            rec['abs'] = section.text.strip()
        #strange page
        if not 'p1' in rec.keys():
            rec['p1'] = re.sub('.*\.', '', rec['doi'])
        #references
        divs = page.find_all('div', attrs = {'class' : 'labeled'})
        if not len(divs):
             divs = page.find_all('div', attrs = {'role' : 'doc-biblioentry'})
        for div in divs:
            for d2 in div.find_all('div', attrs = {'class' : 'label'}):
                d2t = d2.text
                d2.replace_with('[%s] ' % d2t)
            for a in div.find_all('a'):
                at = a.text.strip()
                ah = a['href']
                if at == 'Crossref':
                    a.replace_with(re.sub('.*doi.org\/', ', DOI: ', ah))
                else:
                    a.decompose()
            rec['refs'].append([('x', div.text.strip())])
        #for k in rec.keys():
        #    print '  ', k, '::', rec[k]
        print '  (%s)' % (', '.join(['%s:%s' % (k, len(rec[k])) for k in rec.keys()]))
    return recs


done = getdone()
available = getissuenumbers(jnl, year)
todo = []
for tupel in available:
    if not tupel in done:
        todo.append(tupel)
i = 0
for (vol, issue) in todo:
    i += 1
    print '==={ %i/%i }==={ %s, Volume %s, Issue %s }===' % (i, len(todo), jnlname, vol, issue)
    recs = harvestissue(jnl, vol, issue)
    jnlfilename = '%s%s.%s' % (re.sub('\.', '', jnlname.lower()), vol, issue)
    #write recs
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path,"r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text:
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
