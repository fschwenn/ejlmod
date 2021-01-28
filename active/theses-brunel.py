# -*- coding: utf-8 -*-
#harvest theses from Brunel U.
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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Brunel U.'
jnlfilename = 'THESES-BRUNEL-%sA' % (stampoftoday)

rpp = 50
pages = 1


hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
#for dep in ['8623', '8629']:
for dep in ['8623']:
    for j in range(pages):
        tocurl = 'https://bura.brunel.ac.uk/handle/2438/' + dep +'/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str((j+2)*rpp) + '&etal=-1&order=DESC'
        print '===[ %s ]===[ %i/%i ]===[ %s ]===' % (dep, j+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for tr in tocpage.body.find_all('tr'):
            for td in tr.find_all('td', attrs = {'headers' : 't2'}):
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'autaff' : []}
                for a in td.find_all('a'):
                    rec['link'] = 'https://bura.brunel.ac.uk' + a['href'] #+ '?show=full'
                    rec['doi'] = '20.2000/BRUNEL' + a['href']
                    prerecs.append(rec)
    time.sleep(10)

i = 0
recs = []
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(prerecs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
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
            if meta['name'] == 'DC.creator':
                if re.search('\d\d\d\d\-\d\d\d\d',  meta['content']):
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                else:
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
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
    if rec['autaff']:
        rec['autaff'][-1].append(publisher)
        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                if 'pdf_url' in rec.keys():
                    rec['FFT'] = rec['pdf_url']
                else:
                    for div in artpage.find_all('div'):
                        for a2 in div.find_all('a'):
                            if a2.has_attr('href') and re.search('bistream.*\.pdf', a['href']):
                                divt = div.text.strip()
                                if re.search('Restricted', divt):
                                    print divt
                                else:
                                    rec['FFT'] = 'https://ecommons.cornell.edu' + re.sub('\?.*', '', a['href'])
        if not 'FFT' in rec.keys() and 'pdf_url' in rec.keys():
            rec['hidden'] = rec['pdf_url'] 
        print '  ', rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
