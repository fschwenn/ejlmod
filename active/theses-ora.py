# -*- coding: utf-8 -*-
#harvest Oxford University Reseach Archive for theses
#FS: 2018-01-25


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

publisher = 'Oxford University'

typecode = 'T'

jnlfilename = 'THESES-ORA-%s' % (stampoftoday)

tocurl = 'https://ora.ox.ac.uk/search/detailed?q=%2A%3A%2A&truncate=450&filterf_subject=%22Physics%22&filterf_thesisLevel=%22Doctoral%22&rows=500&sort=timestamp%20desc'

try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (tocurl)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

prerecs = []
for div in tocpage.find_all('div', attrs = {'class' : 'response_doc'}):
    rec = {'jnl' : 'BOOK', 'tc' : typecode}
    isnew = True
    for td in div.find_all('td'):
        if re.search('^20\d\d', td.text):
            rec['date'] = re.sub('^(20\d\d).*', r'\1', td.text.strip()) 
            year = int(re.sub('.*(20\d\d).*', r'\1', rec['date']))
            if year < now.year - 1:
                isnew = False
    for span in div.find_all('span', attrs = {'class' : 'stitle'}):
        rec['tit'] = span.text.strip()
        for a in span.find_all('a'):
            rec['link'] = 'https://ora.ox.ac.uk' + a['href']
            rec['doi'] = re.sub('.*:', '20.2000/', a['href'])
    if isnew:
        prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    i += 1
    print '%i/%i' % (i, len(prerecs))
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    #fulltext
    for ul in artpage.body.find_all('ul', attrs = {'id' : 'download_ul'}):
        for a in ul.find_all('a'):
            rec['FFT'] = a['href']
    #abstract
    for div in artpage.body.find_all('div', attrs = {'class' : 'abstract_block'}):
        rec['abs'] = re.sub('^Abstract. *', '', div.text.strip())
    #contributors
    for div in artpage.body.find_all('div', attrs = {'class' : 'author'}):
        authortyp = False
        for span in div.find_all('span', attrs = {'class' : 'small_link'}):            
            if re.search('More by this author', span.text):
                authortyp = 'author'
            elif re.search('More by this supervisor', span.text):
                authortyp = 'supervisor'
            span.replace_with('')
        if authortyp == 'author':
            #author
            for div2 in div.find_all('div', attrs = {'class' : 'aname'}):
                rec['auts'] = [ div2.text.strip() ]
            #affiliation
                for div2 in div.find_all('div', attrs = {'class' : 'adet'}):
                    aff = ''
                    for td in div2.find_all('td'):
                        if not td.text.strip() in ['Affiliation', 'Author', 'Role', 'Roles', 'Author, Copyright holder']:
                            aff += ' ' + td.text.strip()
                    rec['aff'] = [ aff.strip() ]
        elif authortyp == 'supervisor':
            #supervisor
            for div2 in div.find_all('div', attrs = {'class' : 'aname'}):
                if rec.has_key('MARC'):
                    rec['MARC'].append(('701', [('a', re.sub('(.*) (.*)', r'\2, \1', div2.text.strip()))]))
                else:
                    rec['MARC'] = [('701', [('a', re.sub('(.*) (.*)', r'\2, \1', div2.text.strip()))])]
    #keywords
    #subject
    for table in artpage.body.find_all('table'):
        if table.has_attr('class'):
            if 'infoL' in table['class'] or 'infoR' in table['class']:
                if re.search('Keywords', table.text):
                    rec['keyw'] = []
                    for li in table.find_all('li'):
                        rec['keyw'].append(li.text.strip())
                elif re.search('Subjects', table.text):
                    rec['note'] = []
                    for li in table.find_all('li'):
                        rec['note'].append(li.text.strip())
    #bad metadata
    if not rec.has_key('auts'):
        rec['auts'] = [ 'Mustermann, Martin' ]
    recs.append(rec)

    
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
