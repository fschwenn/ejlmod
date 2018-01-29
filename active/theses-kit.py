# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest theses from Karlsruhe Insitute of Technolgy
# FS 2018-01-08

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import datetime
import time 

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'KIT'

typecode = 'T'

jnlfilename = 'THESES-KIT-%s' % (stampoftoday)

tocurl = 'http://www.etp.kit.edu/english/391.php'
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

prerecs = []
for td in tocpage.body.find_all('td'):
    for a in td.find_all('a'):
        if a.has_attr('href'):
            link = a['href']
            if re.search('ekp-invenio.physik.uni-karlsruhe.de.record.\d+$', link):
                rec = {'jnl' : 'BOOK', 'link' : link, 'tc' : typecode}
                prerecs.append(rec)
                print link

i = 0
recs = []
for rec in prerecs:
    isnew = True
    i += 1
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']+'/export/xm'))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']+'/export/xm'))
    #author
    for datafield in artpage.find_all('datafield', attrs = {'tag' : '100'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            rec['auts'] = [ subfield.text.strip() ] 
    #title
    for datafield in artpage.find_all('datafield', attrs = {'tag' : '245'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            rec['tit'] =  subfield.text.strip()  
    #reportnumber
    for datafield in artpage.find_all('datafield', attrs = {'tag' : '035'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            if rec.has_key('rn'):
                rec['rn'].append(subfield.text.strip())
            else:
                rec['rn'] = [ subfield.text.strip() ]
    #language
    for datafield in artpage.find_all('datafield', attrs = {'tag' : '041'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            if not 'English' == subfield.text.strip():
                rec['language'] = subfield.text.strip()
    #date
    for datafield in artpage.find_all('datafield', attrs = {'tag' : '260'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'c'}):
            rec['date'] = subfield.text.strip()
            year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
            if year < now.year - 1:
                isnew = False
    #abstract
    for datafield in artpage.find_all('datafield', attrs = {'tag' : '520'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'a'}):
            rec['abs'] = subfield.text.strip()
    #DOI,FFT
    for datafield in artpage.find_all('datafield', attrs = {'tag' : '856'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'u'}):
            url = subfield.text.strip()
            if re.search('doi.org.*10\.', url):
                rec['doi'] = re.sub('.*?(10\.\d.*)', r'\1', url)
            elif re.search('\.pdf$', url):
                rec['FFT'] = url
    #CMS-paper
    for datafield in artpage.find_all('datafield', attrs = {'tag' : '920'}):
        for subfield in datafield.find_all('subfield', attrs = {'code' : 'l'}):
            exp = subfield.text.strip()
            if exp == 'CMS':
                rec['exp'] = 'CERN-LHC-CMS'
            elif exp == 'Belle':
                rec['exp'] = 'KEK-BF-BELLE-II'
            elif exp == 'KATRIN':
                rec['exp'] = 'KATRIN'
            elif exp == 'CDF':
                rec['exp'] = 'FNAL-E-0830'
            elif exp == 'DELPHI':
                rec['exp'] = 'CERN-LEP-DELPHI'    
    if not rec.has_key('doi'):
        rec['doi'] = '20.2000/' + re.sub('.*\/', '', rec['link'])
    print '---[ %i/%i ]---[ %s ]---' % (i, len(recs), rec['tit'])
    if isnew:
        recs.append(rec)
    else:
        print 'old thesis'
    time.sleep(5)
            
            
    
            
#closing of files and printing
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
 
            
    
