# -*- coding: utf-8 -*-
#harvest theses from Niels Bohr Institute, Københavns Universitet
#FS: 2020-02-03


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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Bohr Inst.'

hdr = {'User-Agent' : 'Magic Browser'}
repacs = re.compile('.*(\d\d\.\d\d\...).*')
recs = []
jnlfilename = 'THESES-NIELSBOHR-%s' % (stampoftoday)
for year in [now.year, now.year-1]:
    try:
        tocurl = 'https://www.nbi.ku.dk/english/theses/phd-theses/phd_theses_%i' % (year)
        print tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(5)
        for div in tocpage.body.find_all('div', attrs = {'class' : 'media-body'}):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'keyw' : [], 'year' : str(year)}
            for h2 in div.find_all('h2'):
                for a in h2.find_all('a'):
                    rec['link'] = 'https://www.nbi.ku.dk' + a['href']
                    rec['doi'] = '20.2000/NielsBohr/' + re.sub('\W', '', a['href'][31:])
                    recs.append(rec)
    except:
        print year, '?'


i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(10)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'Title':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #title
            elif meta['name'] == 'Description':
                rec['tit'] = meta['content']
    for table in artpage.body.find_all('table', attrs = {'id' : 'table7'}):
        #pdf
        for a in table.find_all('a'):
            if a.has_attr('href') and re.search('Download', a.text):
                rec['hidden'] = 'https://www.nbi.ku.dk' + a['href']
                a.replace_with('')
        #supervisor
        for p in table.find_all('p'):
            pt = p.text.strip()
            if re.search('^Supervisor', pt):
                rec['supervisor'] = []
                for sv in re.split(', ', re.sub('.*: *', '', pt)):
                    rec['supervisor'].append([re.sub('Prof\. ', '', sv)])
        #abstract
        for td in table.find_all('td'):
            for h2 in td.find_all('h2'):
                h2.replace_with('')
                rec['abs'] = td.text.strip()
    print rec.keys()

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
    
