# -*- coding: utf-8 -*-
#harvest theses from Rochester U.
#FS: 2021-04-15

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Rochester'

startyear = now.year-1
departments = [('PHYS', 'Rochester U.', '59'),
	       ('MATH', 'U. Rochester', '74')]
hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-ROCHESTER-%s' % (stampoftoday)

recs = []
for (subj, aff, dep) in departments:
    starturl = 'https://urresearch.rochester.edu/browseCollectionItems.action?collectionId=' + dep
    print '==={ %s (%s) }==={ %s }===' % (subj, dep, starturl)
    req = urllib2.Request(starturl)
    startpage = BeautifulSoup(urllib2.urlopen(req))
    for h3 in startpage.find_all('h3'):
        if re.search('Viewing.*of', h3.text):
            rpp = int(re.sub('.* (\d+) of.*', r'\1', h3.text.strip()))
            total = int(re.sub('.*of (\d+).*', r'\1', h3.text.strip()))
            pages = (total-1)/rpp + 1
    tocpages = [startpage]
    for i in range(pages-1):
        time.sleep(5)
        tocurl = 'https://urresearch.rochester.edu/browseCollectionItems.action?rowStart=' + str((i+1)*rpp) + '&startPageNumber=1&currentPageNumber=2&sortElement=name&sortType=asc&collectionId=' + dep + '&selectedAlpha=All&contentTypeId=-1'
        print '==={ %s (%s) }==={ %i/%i | %i/%i }==={ %s }===' % (subj, dep, i+2, pages, (i+2)*rpp, total, tocurl)
        req = urllib2.Request(tocurl)
        tocpages.append(BeautifulSoup(urllib2.urlopen(req)))
    for tocpage in tocpages:
        for tbody in tocpage.find_all('tbody'):
            for tr in tbody.find_all('tr'):
                keepit = True
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'affiliation' : aff,
                       'supervisor' : [], 'note' : [subj]}
                for a in tr.find_all('a'):
                    if a.has_attr('href') and re.search('institutionalItemId', a['href']):
                        rec['link'] = 'https://urresearch.rochester.edu' + re.sub(';jsessionid=.*\?', '?', a['href'])
                        rec['tit'] = a.text.strip()
                        rec['doi'] = '20.2000/Rochester/' + re.sub('\D', '', rec['link'])
                for td in tr.find_all('td'):
                    if re.search('^\d\d\d\d$', td.text):
                        rec['year'] = td.text.strip()
                        if int(rec['year']) < startyear:
                            keepit = False                            
                if keepit:
                    recs.append(rec)
    print '  %i records so far' % (len(recs))

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'])
        artpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.urlopen(req))
            time.sleep(5)
        except:
            print "no access to %s" % (rec['link'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], rec['affiliation'] ]]
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
    #FFT
    for table in artpage.body.find_all('table', attrs = {'class' : 'greyBorderTable'}):
        for a in table.find_all('a'):
            if a.has_attr('href') and re.search('fileDownloadForInstit', a['href']):
                if re.search('\.pdf', a.text):
                    rec['hidden'] = 'https://urresearch.rochester.edu/' + re.sub(';jsessionid=.*\?', '?', a['href'][1:])
    #abstract
    for table in artpage.body.find_all('table', attrs = {'class' : 'noPaddingTable'}):
        lt = ''
        for tr in table.find_all('tr'):
            if lt == 'Abstract' and not 'abs' in rec.keys():
                rec['abs'] = tr.text.strip()
            for label in tr.find_all('label'):
                lt = label.text.strip()
    #remaining metadata
    for table in artpage.body.find_all('table', attrs = {'width' : '100%'}):
        lt = ''
        for tr in table.find_all('tr'):            
            #supervisor
            if lt == 'Contributor(s):':
                if re.search('Thesis Advisor', tr.text):
                    for a in tr.find_all('a'):
                        rec['supervisor'].append([a.text.strip()])
            #keywords
            if lt == 'Subject Keywords:':
                rec['keyw'] = re.split('; ', tr.text.strip())
                lt = ''
            #pages
            if lt == 'Extents:':
                if re.search('pages.*\d\d', tr.text):
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', tr.text.strip())
                    lt = ''
            #label
            for label in tr.find_all('td', attrs = {'class' : 'previewLabel'}):
                lt = label.text.strip()                            
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
        
