# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Acta Phys.Sin.
# FS 2020-02-23

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time
import datetime

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Chinese Academy of Sciences'
year = sys.argv[1]
issue = sys.argv[2]
jnlfilename = 'actaphyssin%s.%s' % (year, issue)

urltrunk = 'http://wulixb.iphy.ac.cn/en/custom/%s/%s' % (year, issue)
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk), features="lxml")
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk), features="lxml")

recs = []
section = False
for div in tocpage.body.find_all('div', attrs = {'class' : 'main-right'}):
    for child in div.children:
        try:
            child.name
        except:
            continue
        if child.name == 'h6':
            section = child.text.strip()
        elif child.name == 'div':
            for div in child.find_all('div', attrs = {'class' : 'article-list-title'}):
                for a in div.find_all('a'):
                    rec = {'jnl' : 'Acta Phys.Sin.', 'tc' : 'P', 'auts' : [], 'aff' : [],
                           'note' : [], 'issue' : issue, 'refs' : []}
                    if section:
                        rec['note'].append(section)
                    rec['artlink'] = a['href']
                    rec['tit'] = a.text.strip()
                    recs.append(rec)
time.sleep(3)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(13)
    except:
        print "retry %s in 180 seconds" % (rec['artlink'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #DOI
            if meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #abs
            elif meta['name'] == 'dc.description':
                rec['abs'] = meta['content']
            #volume
            elif meta['name'] == 'citation_volume':
                rec['vol'] = meta['content']
            #pages
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            elif meta['name'] == 'citation_lastpage':
                rec['p2'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
            #rights
            elif meta['name'] == 'dc.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['license'] = {'url' : meta['content']}
            #keywords
            elif meta['name'] == 'dc.keywords':
                rec['keyw'] = re.split(', ', meta['content'])
    #fulltext
    if 'citation_pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['citation_pdf_url']
        else:
            rec['hidden'] = rec['citation_pdf_url']
    #references
    for li in artpage.body.find_all('li', attrs = {'id' : 'References'}):
        for table in li.find_all('table', attrs = {'class' : 'reference-tab'}):
            for tr in table.find_all('tr'):
                for a in tr.find_all('a'):
                    if a.has_attr('href') and re.search('doi.org\/10', a['href']):
                        rdoi = re.sub('.*doi.org\/', ', DOI: ', a['href'])
                        a.replace_with(rdoi)
                rec['refs'].append([('x', tr.text.strip())])
    #PACS
    for inp in artpage.body.find_all('input', attrs = {'id' : 'pcas_txt'}):
        rec['pacs'] = re.split(' *[;,] *', inp['value'])
    #authors
    for ul in artpage.body.find_all('ul', attrs = {'class' : 'article-author'}):
        for sup in ul.find_all('sup'):
            affs = ''
            for aff in re.split(',', sup.text.strip()):
                affs += ', =Aff' + aff
            sup.replace_with(affs)
        ult = re.sub('[\n\t\r]', ' ', ul.text.strip())
        for part in re.split(' *, *', ult):
            if len(part) > 3:
                rec['auts'].append(part)
    #affiliations
    for li in artpage.body.find_all('li', attrs = {'class' : 'article-author-address'}):
        for span in li.find_all('span'):
            spant = re.sub('[\n\t\r]', '', span.text.strip())
            spant = re.sub('(\d+).*', r'Aff\1= ', spant)
            span.replace_with(spant)
        rec['aff'].append(li.text.strip())
    #pages
    if re.search('\d+\-1', rec['p1']) and re.search('\d+\-\d', rec['p2']):
        rec['pages'] = re.sub('.*\-', '', rec['p2'])
        rec['p1'] = re.sub('\-.*', '', rec['p2'])
        del rec['p2']
    print '   ', rec.keys()

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

