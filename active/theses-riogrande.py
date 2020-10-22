# -*- coding: utf-8 -*-
#harvest theses from Rio Grande do Sul U.
#FS: 2020-10-08
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
jnlfilename = 'THESES-RioGrandeDoSul-%s' % (stampoftoday)

publisher = 'Rio Grande do Sul U.'

hdr = {'User-Agent' : 'Magic Browser'}

rpp = 50
pages = 4
boringdegrees = ['mestrado']

prerecs = []
for (depnr, department) in [('46', 'Physics'), ('48', 'Mathematics'), ('49', 'Applied Mathematics'), ('43', 'Computation')]:
    for page in range(pages):
        tocurl = 'https://lume.ufrgs.br/handle/10183/' + depnr +'/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
        print '==={ %s }==={ %i/%i }==={ %s }===' % (department, page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            new = True
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [department], 'keyw' : [], 'supervisor' : []}
            for span in div.find_all('span', attrs = {'class' : 'date'}):
                if re.search('[12]\d\d\d', span.text):
                    rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', span.text.strip())
                    if int(rec['year']) < now.year - 2*10:
                        new = False
                        print '  skip',  rec['year']
            if new:
                for a in div.find_all('a'):
                    if re.search('handle', a['href']):
                        rec['artlink'] = 'https://lume.ufrgs.br' + a['href'] + '?show=full'
                        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                        prerecs.append(rec)
        time.sleep(2)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue    
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = meta['content']
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append(publisher)
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta['content']:
                    if meta.has_attr('xml:lang'):
                        if meta['xml:lang'] == 'en':
                            rec['abs'] = meta['content']
                        elif meta['xml:lang'] == 'pt':
                            rec['abspt'] = meta['content']
                    else:
                        rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split('[,;] ', meta['content']):
                    if not re.search('^info.eu.repo', keyw):
                        rec['keyw'].append(keyw)
    #abstract
    if 'abspt' in rec.keys() and not 'abs' in rec.keys():
        rec['abs'] = rec['abspt']
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            tdt = td.text.strip()
            td.decompose()
        for td in tr.find_all('td'):
            if td.text.strip() == 'pt_BR':
                continue
            #supervisor
            if tdt == 'dc.contributor.advisor':
                rec['supervisor'] = [[ re.sub(' \(.*', '', td.text.strip()) ]]
            #degree
            elif tdt == 'dc.degree.level':
                degree = td.text.strip()
                if degree in boringdegrees:
                    print '  skip "%s"' % (degree)
                    keepit = False
                else:
                    rec['note'].append(degree)
            #language
            elif tdt == 'dc.language.iso':
                if td.text.strip() == 'por':
                    rec['language'] = 'portuguese'
    for a in artpage.body.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    if keepit:
        recs.append(rec)
        print '  ', rec.keys()
                
#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'),'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
