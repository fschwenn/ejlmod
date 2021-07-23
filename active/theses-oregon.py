# -*- coding: utf-8 -*-
#harvest theses from Oregon U.
#FS: 2021-01-27

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'THESES-OREGON-%s' % (stampoftoday)

publisher = 'Oregon U.'

hdr = {'User-Agent' : 'Magic Browser'}

rpp = 50
pages = 4
years = 2
boringdisciplines = ['Department+of+Geography', 'Department+of+Educational+Methodology%2C+Policy%2C+and+Leadership',
                     'Department+of+Psychology', 'School+of+Music+and+Dance', 'Department+of+Geological+Sciences',
                     'Department+of+Biology', 'Department+of+Linguistics', 'Department+of+Anthropology',
                     'Department+of+Architecture', 'Department+of+Comparative+Literature',
                     'Department+of+Economics', 'Department+of+English', 'Department+of+Finance',
                     'Department+of+History', 'Department+of+Marketing', 'Department+of+Political+Science',
                     'Department+of+Sociology', 'Department+of+Special+Education+and+Clinical+Sciences',
                     'Environmental+Studies+Program', 'School+of+Journalism+and+Communication',
                     'Department+of+Chemistry+and+Biochemistry', 'Department+of+Counseling+Psychology+and+Human+Services',
                     'Department+of+Human+Physiology', 'Conflict+and+Dispute+Resolution+Program',
                     'Department+of+Accounting', 'Department+of+Chemistry', 'Department+of+Decision+Sciences',
                     'Department+of+East+Asian+Languages+and+Literatures', 'Department+of+Education+Studies',
                     'Department+of+German+and+Scandinavian', 'Department+of+Landscape+Architecture',
                     'Department+of+Management', 'Department+of+Philosophy',
                     'Department+of+Romance+Languages', 'Department+of+Theater+Arts']
boringdegrees = ['M.A.', 'M.S.', 'masters', 'D.Ed.']

recs = []
redeg = re.compile('rft.degree=')
for page in range(pages):
    tocurl = 'https://scholarsbank.uoregon.edu/xmlui/handle/1794/13076/discover?rpp='+str(rpp)+'&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        keepit = True
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : [], 'supervisor' : []}
        for span in div.find_all('span', attrs = {'class' : 'date'}):
            if re.search('[12]\d\d\d', span.text):
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
                if int(rec['year']) < now.year - years:
                    keepit = False
                    print '  skip',  rec['year']
        for span in div.find_all('span', attrs = {'class' : 'Z3988'}):
            infos = re.split('&', span['title'])
            for info in infos:
                if keepit:
                    if redeg.search(info):
                        degree = redeg.sub('', info)
                        if degree in boringdisciplines or degree in boringdegrees:
                            keepit = False
                            print '  skip', degree
                        elif not degree in ['Ph.D.', 'doctoral']:
                            rec['note'].append(degree)
        if keepit:
            for a in div.find_all('a'):
                if re.search('handle', a['href']):
                    rec['artlink'] = 'https://scholarsbank.uoregon.edu' + a['href'] + '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
    print '  %i records so far' % (len(recs))
    time.sleep(2)

i = 0
for rec in recs:
    keepit = True
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append(publisher)
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['content']:
                    rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split('[,;] ', meta['content']):
                    rec['keyw'].append(keyw)
    for tr in artpage.body.find_all('tr'):
        for td in tr.find_all('th', attrs = {'class' : 'label-cell'}):
            tdt = td.text.strip()
            td.decompose()
        for td in tr.find_all('td'):
            if td.text.strip() == 'en_US':
                continue
            #supervisor
            if tdt in ['dc.contributor.supervisor', 'dc.contributor.advisor']:
                if td.text.strip():
                    rec['supervisor'].append([ re.sub(' \(.*', '', td.text.strip()) ])
    print '  ', rec.keys()
                
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'),'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
