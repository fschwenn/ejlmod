# -*- coding: utf-8 -*-
#harvest theses from Andes U., Bogota
#FS: 2020-08-28


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
import ssl

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Andes U., Bogota'

jnlfilename = 'THESES-BOGOTA-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
tocurl = 'https://repositorio.uniandes.edu.co/handle/1992/30/browse?type=organization&value=Departamento+de+F%C3%ADsica'
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : []}
    for h4 in div.find_all('h4'):
        for a in h4.find_all('a'):
            rec['link'] = 'https://repositorio.uniandes.edu.co' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
    for span in div.find_all('span', attrs = {'class' : 'date'}):
        rec['year'] = re.sub('.*?([12]\d\d\d).*', r'\1', span.text.strip())
        if int(rec['year']) > now.year-5:
            recs.append(rec)
        else:
            print '  skip', rec['year']

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            req = urllib2.Request(rec['link'], headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req))
        except:
            print "no access to %s" % (rec['link'])
            continue    
    for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'citation_author':
                    rec['autaff'] = [[ meta['content'], publisher ]]
                #supervisor
                elif meta['name'] == 'DC.contributor':
                    rec['supervisor'].append([meta['content']])
                #title
                elif meta['name'] == 'DC.title':
                    rec['tit'] = meta['content']
                #language
                elif meta['name'] == 'citation_language':
                    if meta['content'] == 'spa':
                        rec['language'] = 'Spanish'
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
                    rec['hidden'] = meta['content']


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
