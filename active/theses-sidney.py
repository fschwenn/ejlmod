# -*- coding: utf-8 -*-
#harvest theses from Sydney U. 
#FS: 2019-12-11


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

publisher = 'Sydney U.'

rpp = 100
pages = 2


            

refac = re.compile('(Life|Health|Medicine|Social|Information|Music|Arts|Chemistry)')
hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for j in range(pages):
    tocurl = 'https://ses.library.usyd.edu.au/handle/2123/35/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(j*rpp) + '&etal=-1&order=DESC'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
    relevant = 0
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for span in div.find_all('span', attrs = {'class' : 'publisher'}):
            fac = span.text.strip()
            if not refac.search(fac):
                for a in div.find_all('a'):
                    rec['artlink'] = 'https://ses.library.usyd.edu.au' + a['href'] #+ '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
                    relevant += 1
    print '---{ %i/%i }---{ %i/%i +> %i/%i }---' % (j, pages, relevant, len(divs), len(recs), pages*rpp)
    time.sleep(10)

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
    #hidden PDF
    if not 'FFT' in rec.keys():
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
                            rec['hidden'] = 'https://ecommons.cornell.edu' + re.sub('\?.*', '', a['href'])
    print '  ', rec.keys()
jnlfilename = 'THESES-SIDNEY-%s' % (stampoftoday)

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
