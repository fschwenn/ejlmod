# -*- coding: utf-8 -*-
#harvest theses from Santa Maria U., Valparaiso
#FS: 2020-03-24

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
import mechanize
import unicodedata

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Santa Maria U., Valparaiso'


numberofpages = 1
recordsperpage = 50
wrongdepartments = ['Universidad Tecnica Federico Santa Maria. Departamento de Electronica',
                    'Universidad Tecnica Federico Santa Maria. Departamento de Quimica',
                    'Universidad Tecnica Federico Santa Maria UTFSM INFORMATICA',
                    'Universidad Tecnica Federico Santa Maria UTFSM ELECTRONICA']

###remove accents from a string
def akzenteabstreifen(string):
    if not type(string) == type(u'unicode'):
        string = unicode(string,'utf-8', errors='ignore')
        if not type(string) == type(u'unicode'):
            return string
        else:
            return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')
    else:
        return unicode(unicodedata.normalize('NFKD',re.sub(u'ß', u'ss', string)).encode('ascii','ignore'),'utf-8')


prerecs = []
recs = []
jnlfilename = 'THESES-SANTAMARIA-%s' % (stampoftoday)
for pn in range(numberofpages):
    tocurl = 'https://repositorio.usm.cl/handle/11673/21680/browse?rpp=' + str(recordsperpage) + '&sort_by=2&type=dateissued&offset=' + str(pn * recordsperpage) + '&etal=-1&order=DESC'
    print '==={ %i/%i }==={ %s }===' % (pn+1, numberofpages, tocurl)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl)) 
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
        for a in div.find_all('a'):
            if re.search('handle\/\d', a['href']):
                rec['artlink'] = 'https://repositorio.usm.cl' + a['href'] #+ '?show=full'
                rec['hdl'] = re.sub('.*handle\/(.*\d).*', r'\1', a['href'])
                prerecs.append(rec)
    time.sleep(10)

i = 0
for rec in prerecs:
    wrongdegree = False
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue


        
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'DC.creator':
                author = meta['content']
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append(publisher)
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #supervisor
            elif meta['name'] == 'DC.contributor':
                if meta.has_attr('xml:lang'):
                    rec['division'] = akzenteabstreifen(meta['content'])
                    rec['note'].append(rec['division'])
                    if meta['content'] in wrongdepartments:
                        print '   ignore "%s"' % (meta['content'])
                        wrongdegree = True
                elif not rec['supervisor']:
                    rec['supervisor'].append([re.sub('([a-z])\.$', r'\1', meta['content'])])
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d\d', meta['content']):
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', meta['content'])
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] in ['spa', 'es']:
                    rec['language'] = 'spanish'
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdflink'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #license            
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
            #thesis type
            elif meta['name'] == 'DC.description':
                rec['note'].append(meta['content'])
                if re.search('Mag.ster en', meta['content'], re.IGNORECASE):
                    #print '   skip "%s"' % (meta['content'])
                    wrongdegree = True
    if 'pdflink' in rec.keys():
        if 'licence' in rec.keys():
            rec['FFT'] = rec['pdflink']
        else:
            rec['hidden'] = rec['pdflink']
    if not wrongdegree:
        print rec.keys()
        recs.append(rec)
        
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
