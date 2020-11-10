# -*- coding: utf-8 -*-
#harvest theses from Danish National Research Database
#FS: 2020-11-09

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Danish National Research Database'

jnlfilename = 'THESES-FORSKNINGSDATABASEN-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
rpp = 10


tocurl = 'https://www.forskningsdatabasen.dk/en/catalog?f%5Bformat_orig_s%5D%5B%5D=dtd&f%5Bresearch_area_ss%5D%5B%5D=Science%2Ftechnology&per_page=' + str(rpp) + '&q=&search_field=publications&sort=pub_date_tsort+desc%2C+journal_vol_tsort+desc%2C+journal_issue_tsort+desc%2C+journal_page_start_tsort+asc%2C+title_sort+asc'
print '==={ %s }===' % (tocurl)
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
time.sleep(2)
for div in tocpage.find_all('div', attrs = {'class' : 'document'}): 
    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
    #title
    for h5 in div.find_all('h5', attrs = {'class' : 'doctitle'}):
        for a in h5.find_all('a'):
            rec['tit'] = a.text.strip()
            rec['artlink'] = 'https://www.forskningsdatabasen.dk' + a['href']
            rec['doi'] = '20.2000/DNRB/' + a['href']
    for dl in div.find_all('dl'):
        for child in dl.children:            
            try:
                child.name
            except:
                continue
            if child.name == 'dt':
                dtt = child.text
            elif child.name == 'dd':
                ddt = child.text.strip()
                #author
                if dtt == 'Authors:':
                    rec['autaff'] = [[ ddt ]]
                #aff and date
                elif dtt == 'Publisher:':
                    if re.search('[12]\d\d\d', ddt):
                        rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', ddt)
                    rec['autaff'][-1].append(re.sub(', *[12]\d\d\d$', '', ddt))
                #ORCID
                elif dtt == 'ORCID:':
                    rec['autaff'][-1].append('ORCID:'+ddt)
            elif child.name == 'div':
                for dt in div.find_all('dt'):
                    if dt.text.strip() == 'Data providers:':
                        for a in child.find_all('a'):
                            rec['link'] = a['href']
    recs.append(rec)
                    
j = 0
for rec in recs:
    j += 1
    print '---{ %i/%i }---{ %s }------' % (j, len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'])
        artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        time.sleep(2)
    except:
        print 'wait 10 minutes'
        time.sleep(600)
        try:
            req = urllib2.Request(rec['artlink'])
            artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
            time.sleep(30)
        except:
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #ISBN
            if meta['name'] == 'citation_isbn':
                rec['isbn'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'dan':
                    rec['language'] = 'danish'
    #abstract
    for dd in artpage.body.find_all('dd', attrs = {'class' : 'blacklight-abstract_ts'}):
        rec['abs'] = dd.text.strip()
    #fulltext
    for div in artpage.body.find_all('div', attrs = {'class' : 'panel__block-contents'}):
        for li in div.find_all('li'):
            for img in li.find_all('img', attrs = {'alt' : 'Openaccess'}):
                for a in li.find_all('a'):
                    if a.has_attr('pdf') and re.search('\.pdf$', a['href']):
                        rec['FFT'] = a['href']
    print '  ', rec.keys()

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
