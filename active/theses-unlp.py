# -*- coding: utf-8 -*-
#harvest theses from UNLP, La Plata (main)
#FS: 2020-02-04


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

publisher = 'UNLP, La Plata (main)'

rpp = 50
pages = 1

departmentstoskip = ['Doctor en Ciencias Exactas, área Química; Universidad Nacional de La Plata',
                     'Doctor en Ciencias Exactas, área Ciencias Biológicas; Universidad Nacional de La Plata',
                     'Licenciado en Biotecnología y Biología Molecular; Universidad Nacional de La Plata',
                     'Magister en Plantas Medicinales; Universidad Nacional de La Plata',
                     'Magister en Física Contemporánea; Universidad Nacional de La Plata',
                     'Magister en Tecnología e Higiene de los Alimentos']
                     

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for page in range(pages):
    tocurl = 'http://sedici.unlp.edu.ar/handle/10915/23/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page) + '&sort_by=dc.date.issued_dt&order=desc'
    print '---{ %i/%i }---{ %s }------' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    divs = tocpage.body.find_all('li', attrs = {'class' : 'ds-artifact-item'})
    for div in divs:
        relevant = True
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for a in div.find_all('a'):
            rec['artlink'] = 'http://sedici.unlp.edu.ar' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            rec['tit'] = a.text.strip()
        for span in div.find_all('span', attrs = {'xmlns:ex' : 'ar.edu.unlp.sedici.xmlui.xsl.XslExtensions'}):
            spant = span.text.strip()
            if re.search('(Master|Qu.mica|Biol.gica|Medicin|Higiene|Licenciado)', spant):
                #print '  skip', spant
                relevant = False
        if relevant:
            recs.append(rec)
    time.sleep(3)

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
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split('; ', meta['content'])
            #author
            elif meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'], publisher ]]
            #doi
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org\/10', meta['content']):                
                    rec['doi'] = re.sub('.*doi.org\/(10.*)', r'\1', meta['content'])
            #pdf
            elif meta['name'] == 'citation_pdf_url':
                rec['citation_pdf_url'] = meta['content']
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'es':
                    rec['language'] = 'spanish'
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'citation_pdf_url' in rec.keys():
                rec['FFT'] = rec['citation_pdf_url']
    #hiddenPDF
    if not 'license' in rec.keys() and 'citation_pdf_url' in rec.keys():
        rec['hidden'] = rec['citation_pdf_url']

    print '  ', rec.keys()


jnlfilename = 'THESES-UNLP-%s' % (stampoftoday)


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
