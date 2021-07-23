# -*- coding: utf-8 -*-
#harvest theses from Cantabria U., Santander
#FS: 2020-08-25


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
jnlfilename = 'THESES-CANTABRIA-%s' % (stampoftoday)

publisher = 'Cantabria U., Santander'

hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for fac in ['103', '133', '123', '1838']:
    tocurl = 'https://repositorio.unican.es/xmlui/handle/10902/' + fac + '/discover?rpp=10&etal=0&group_by=none&page=1&sort_by=dc.date.issued_dt&order=desc'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        new = True
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for span in div.find_all('span', attrs = {'class' : 'date'}):
            rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
            if int(rec['year']) < now.year - 2:
                new = False
                print '  skip',  rec['year']
        if new:
            for a in div.find_all('a'):
                if re.search('handle', a['href']):
                    rec['artlink'] = 'https://repositorio.unican.es' + a['href'] #+ '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
    time.sleep(2)

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
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append(publisher)
            #author
            if meta['name'] == 'DC.contributor':
                if not meta.has_attr('xml:lang'):
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['supervisor'] = [[ author ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #license
            elif meta['name'] == 'DC.rights':
                rec['license'] = {'url' : meta['content']}
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' the ',  meta['content']):
                    rec['abs'] = re.sub('ABSTRACT: ', '', meta['content'])
                else:
                    rec['absspa'] = re.sub('RESUMEN: ', '', meta['content'])
            #ISBN
            elif meta['name'] == 'citation_isbn':
                rec['isbn'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] in ['spa', 'es']:
                    rec['language'] = 'spanish'
    if not 'abs' in rec.keys():
        if 'absspa' in rec.keys():
            rec['abs'] = rec['absspa']

#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs,xmlfile,publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
