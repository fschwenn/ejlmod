# -*- coding: utf-8 -*-
#harvest Maryland University theses
#FS: 2018-01-31

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Maryland U., College Park'

typecode = 'T'

jnlfilename = 'THESES-MARYLAND-%s' % (stampoftoday)

rpp = 60
pages = 1

recs = []
for  (fc, dep, aff) in [('m', '2793', 'Maryland U., College Park'), ('c', '2756', 'Maryland U., College Park'),
                        ('a', '2746', 'Maryland U., College Park'), ('', '2800', 'Maryland U.')]:
    for page in range(pages):
        tocurl = 'https://drum.lib.umd.edu/handle/1903/' + dep + '/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(page*rpp) + '&etal=-1&order=DESC'
        print '==={ %s %i/%i }==={ %s }===' % (dep, page+1, pages, tocurl)
        try:
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")
            time.sleep(4)
        except:
            print "retry %s in 180 seconds" % (tocurl)
            time.sleep(180)
            tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl), features="lxml")

        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            for a in div.find_all('a'):
                rec = {'jnl' : 'BOOK', 'tc' : 'T', 'tit' : a.text.strip(), 
                       'keyw' : [], 'supervisor' : [], 'affiliation' : aff}
            rec['artlink'] = 'https://drum.lib.umd.edu' + a['href']
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            if fc: rec['fc'] = fc
            if not  rec['hdl'] in ['1903/22153']:
                recs.append(rec)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(4)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'DC.subject':
                rec['keyw'].append(meta['content'])
            elif meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'], rec['affiliation'] ]]
            elif meta['name'] == 'bepress_citation_pdf_url':
                rec['FFT'] = meta['content']
            elif meta['name'] == 'DC.identifier':
                if re.search('doi:', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #elif meta['name'] == 'DC.contributor':
            #    rec['supervisor'].append([meta['content']])
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'DCTERMS.available'}):
        rec['date'] = re.sub('T.*', '', meta['content'])
    for div in artpage.body.find_all('div', attrs = {'class' : 'simple-item-view-advisor'}):
        for p in div.find_all('div'):
            rec['supervisor'].append([ re.sub('^Dr. ', '', p.text.strip()) ])
    if not 'doi' in rec.keys():
        rec['link'] = rec['artlink']
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
