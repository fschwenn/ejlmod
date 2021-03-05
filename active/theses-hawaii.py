# -*- coding: utf-8 -*-
#harvest theses from Hawaii
#FS: 2021-02-24

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Hawaii U.'
jnlfilename = 'THESES-HAWAII-%s' % (stampoftoday)

rpp = 10

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for (dep, depnr) in [('Astronomy', '772'), ('Physics', '2136'), ('Mathematics', '2094')]:
    tocurl = 'https://scholarspace.manoa.hawaii.edu/handle/10125/' + depnr + '/browse?type=dateissued&year=-1&month=-1&sort_by=2&order=DESC&rpp=' + str(rpp) + '&etal=0&submit_browse=Update'
    print '===[ %s ]===[ %s ]===' % (dep, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'headers' : 't2'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : [], 'note' : [dep]}
            for a in td.find_all('a'):
                rec['artlink'] = 'https://scholarspace.manoa.hawaii.edu' + a['href'] #+ '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '',  a['href'])
                recs.append(rec)
    time.sleep(7)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue

    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                if re.search('\d\d\d\d\-\d\d\d\d',  meta['content']):
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                else:
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'].append([ author ])
            #description
            elif meta['name'] == 'DC.description':
                rec['note'].append(meta['content'])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    if len(rec['autaff']) == 1:
        rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if 'pdf_url' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['pdf_url']
        else:
            rec['hidden'] = rec['pdf_url']
    for tr in artpage.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
            tdt = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue'}):
            #abstract
            if tdt == 'Abstract:':
                rec['abs'] = td.text.strip()
            #pages
            elif tdt == 'Pages/Duration:':
                if re.search('\d\d p', td.text):
                    rec['pages'] = re.sub('.*?(\d\d+) p.*', r'\1', td.text.strip())
                        
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
