# -*- coding: UTF-8 -*-
#program to harvest journals from Association for Computing Machinery'
# FS 2021-02-26

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
from selenium.webdriver.firefox.options import Options
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

recs = []

publisher = 'Association for Computing Machinery'
jnl = sys.argv[1]
if jnl == 'proceedings':
    procnumber = sys.argv[2]
    jnlname = 'BOOK'
    tc = 'C'
    if len(sys.argv) > 3:
        cnum = sys.argv[3]
    else:
        cnum = False
    jnlfilename = "acm_%s%s" % (jnl, procnumber)
    tocurl = 'https://dl.acm.org/doi/proceedings/10.1145/' + procnumber
else:
    year = sys.argv[2]
    vol = sys.argv[3]
    issue = sys.argv[4]
    tc = 'P'
    if (jnl == 'tqc'): 
        jnlname = 'ACM Trans.Quant.Comput.'
    elif (jnl == 'toms'): 
        jnlname = 'ACM Trans.Math.Software'
    elif (jnl == 'cacm'): 
        jnlname = 'Commun.ACM'
    elif (jnl == 'jacm'): 
        jnlname = 'J.Assoc.Comput.Machinery'
    elif (jnl == 'tocs'): 
        jnlname = 'ACM Trans.Comp.Syst.'
    elif (jnl == 'csur'): 
        jnlname = 'ACM Comput.Surveys'
    elif (jnl == 'tog'): 
        jnlname = 'ACM Trans.Graph.'
    elif (jnl == 'tomacs'): 
        jnlname = 'ACM Trans.Model.Comput.Simul.'
    elif (jnl == 'trets'): 
        jnlname = 'ACM Trans.Reconf.Tech.Syst.'

    now = datetime.datetime.now()
    stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

    jnlfilename = "acm_%s%s.%s" % (jnl, vol, issue)
    tocurl = 'https://dl.acm.org/toc/%s/%s/%s/%s' % (jnl, year, vol, issue)

    print "%s, Volume %s, Issue %s" % (jnlname, vol, issue)

print "get table of content... from %s" % (tocurl)

driver = webdriver.PhantomJS()
driver.implicitly_wait(300)

driver.get(tocurl)
tocpage = BeautifulSoup(driver.page_source)

for span in tocpage.body.find_all('span', attrs = {'class' : 'in-progress'}):
    jnlfilename = "acm_%s%s.%s_in_progress_%s" % (jnl, vol, issue, stampoftoday)

if jnl == 'proceedings':
    #year
    for div in tocpage.find_all('div', attrs = {'class' : 'coverDate'}):
        year = div.text.strip()
    #Hauptaufnahme
    rec = {'jnl' : jnlname, 'tc' : 'K', 'auts' : [], 'year' : year}
    rec['doi'] = '10.1145/' + procnumber
    for div in tocpage.body.find_all('div', attrs = {'class' : 'colored-block__title'}):
        if not 'tit' in rec.keys():
            rec['tit'] = div.text.strip()
            if cnum:
                rec['cnum'] = cnum
            for divr in div.find_all('div', attrs = {'class' : 'item-meta-row'}):
                for divh in divr.find_all('div', attrs = {'class' : 'item-meta-row'}):
                    divht = div.text.strip()
                for divc in divr.find_all('div', attrs = {'class' : 'item-meta-row__value'}):
                    #ISBN
                    if divht == 'ISBN:':
                        rec['isbn'] = divc.text.strip()
                    #details
                    elif divht == 'Conference:':
                        rec['note'] = [divc.text.strip()]
            #authors
            for ul in tocpage.body.find_all('ul', attrs = {'title' : 'list of authors'}):
                for a in ul.find_all('a'):
                    if not re.search('\+ *\d', a.text):
                        rec['auts'].append(re.sub('(.*) (.*)', r'\2, \1 (ed.)', a.text.strip()))
            recs = [rec]
                    
for div in tocpage.body.find_all('div', attrs = {'class' : 'issue-item__content'}):
    if jnl == 'proceedings':
        rec = {'jnl' : jnlname, 'tc' : tc, 'year' : year}
        if cnum:
            rec['cnum'] = cnum
    else:
        rec = {'jnl' : jnlname, 'tc' : tc, 'vol' : vol, 'issue' : issue, 'year' : year}
    for h5 in div.find_all('h5', attrs = {'class' : 'issue-item__title'}):
        for a in h5.find_all('a'):
            rec['artlink'] = 'https://dl.acm.org' + a['href']
            rec['doi'] = re.sub('.*?\/(10\..*)', r'\1', rec['artlink'])
            rec['tit'] = a.text.strip()
    for div2 in div.find_all('div', attrs = {'class' : 'issue-item__detail'}):
        div2t = div2.text.strip()
        #pages
        if re.search(' pp \d+\D\d+', div2t):
            pages = re.split('\D', re.sub('.*pp (\d+\D\d+).*', r'\1', div2t))
            rec['pages'] = str(int(pages[1]) - int(pages[0]))
        #p1
        if re.search('(Paper|Article) No\.: \d+', div2t):
            rec['p1'] = re.sub('.*(Paper|Article) No\.: (\d+).*', r'\2', div2t)            
    recs.append(rec)

print ' %i recs from TOC' % (len(recs))
inps = tocpage.body.find_all('input', attrs = {'class' : 'section--dois'})
ndois = 0 
for inp in inps:
    if inp.has_attr('value'):
        for doi in re.split(',', inp['value']):
            if jnl == 'proceedings':
                rec = {'jnl' : jnlname, 'tc' : tc, 'year' : year}
                if cnum:
                    rec['cnum'] = cnum
            else:
                rec = {'jnl' : jnlname, 'tc' : tc, 'vol' : vol, 'issue' : issue, 'year' : year}
            rec['doi'] = doi
            rec['artlink'] = 'https://dl.acm.org/doi/' + doi
            recs.append(rec)
            ndois += 1
print ' %i additional recs from %i sections' % (ndois, len(inps))

i = 0
for rec in recs:
    i += 1
    if not 'artlink' in rec.keys():
        continue
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    time.sleep(10)
    driver.get(rec['artlink'])
    artpage = BeautifulSoup(driver.page_source)

    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #keywords
            if meta['name'] == 'dc.Subject':
                rec['keyw'] = re.split(' *; *', meta['content'])
            #date
            elif meta['name'] == 'dc.Date':
                rec['date'] = re.sub('.*?(\d\d\d\\d\-\d+\-\d+)$', r'\1', meta['content'])
            #type
            elif meta['name'] == 'dc.Type':
                rec['note'] = [ meta['content'] ]
            #article no
            elif meta['name'] == 'dc.Identifier':
                if meta.has_attr('scheme') and meta['scheme'] == 'article-no':
                    rec['p1'] = meta['content']
    #tile
    for h1 in artpage.find_all('h1', attrs = {'class' : 'citation__title'}):
        rec['tit'] = h1.text.strip()
    #authors
    for ul in artpage.find_all('ul', attrs = {'ariaa-label' : 'authors'}):
        rec['autaff'] = []
        for li in ul.find_all('li'):
            for span in li.find_all('span', attrs = {'class' : 'loa__author-name'}):
                rec['autaff'].append([span.text.strip()])
            for span in li.find_all('span', attrs = {'class' : 'loa_author_inst'}):
                rec['autaff'][-1].append(span.text.strip())
    #abstract
    for div in artpage.find_all('div', attrs = {'class' : 'abstractInFull'}):
        for sup in div.find_all('sup'):
            supt = sup.text.strip()
            sup.replace_with('$^{%s}$' % (supt))
        for sub in div.find_all('sub'):
            subt = sub.text.strip()
            sub.replace_with('$_{%s}$' % (subt))
        rec['abs'] = div.text.strip()
    #references
    for ol in artpage.find_all('ol', attrs = {'class' : 'references__list'}):
        rec['refs'] = []
        for li in ol.find_all('li'):
            refno = ''
            if li.has_attr('id'):
                refno = '[%s] ' % (re.sub('^0*', '', re.sub('\D', '', li['id'])))
            for a in li.find_all('a'):
                if a.has_attr('href') and re.search('doi=10.*key=10', a['href']):
                    rdoi = re.sub('.*key=', '', a['href'])
                    rdoi = re.sub('%28', '(', rdoi)
                    rdoi = re.sub('%29', ')', rdoi)
                    rdoi = re.sub('%2F', '/', rdoi)
                    rdoi = re.sub('%3A', ':', rdoi)
                    a.replace_with(', DOI: %s' % (rdoi))
                else:
                    a.decompose()
            rec['refs'].append([('x', refno + li.text.strip())])                        
    print '   ', rec.keys()
  
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
