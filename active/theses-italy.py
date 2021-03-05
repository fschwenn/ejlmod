# -*- coding: utf-8 -*-
#harvest theses from different italian universities
#FS: 2020-02-20

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

universities = {'milanbicocca' : ('Milan Bicocca U.', 'https://boa.unimib.it', '/handle/10281/9145', 8),
                'trento' : ('Trento U.', 'https://iris.unitn.it', '/handle/11572/237822', 10),
                'pavia' : ('Pavia U.', 'https://iris.unipv.it', '/handle/11571/1198268', 10),
                'turinpoly' : ('Turin Polytechnic', 'https://iris.polito.it', '/handle/11583/2614423', 10),
                'milan' : ('Milan U.', 'https://air.unimi.it', '/handle/2434/146884', 20),
                'udine' : ('Udine U.', 'https://air.uniud.it', '/handle/11390/1123314', 7),
                'genoa' : ('Genoa U.', 'https://iris.unige.it', '/handle/11567/928192', 20),
                'ferrara' : ('Ferrara U.', 'https://iris.unife.it', '/handle/11392/2380873', 7),
                'trieste' : ('Trieste U', 'https://arts.units.it', '/handle/11368/2907477', 10),
                'siena' : ('Siena U.', 'https://usiena-air.unisi.it', '/handle/11365/973085', 5),
                'verona' : ('Verona U.', 'https://iris.univr.it', '/handle/11562/924246', 7),
                'cagliari' : ('Cagliari U.', 'https://iris.unica.it', '/handle/11584/207612', 8),
                'sns' : ('Pisa, Scuola Normale Superiore', 'https://ricerca.sns.it', '/handle/11384/78634', 5),
                'cagliarieprints' : ('Cagliari U.', 'https://iris.unica.it', '/handle/11584/265854', 8),
                'parma' : ('Parma U.', 'https://www.repository.unipr.it', '/handle/1889/636', 1)}

uni = sys.argv[1]
publisher = universities[uni][0]
pages = universities[uni][3]
jnlfilename = 'THESES-%s-%s' % (uni.upper(), stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for page in range(pages):
    tocurl = '%s%s?offset=%i&sort_by=-1&order=DESC' % (universities[uni][1], universities[uni][2], 20*page)
    print '---{ %i/%i }---{ %s }------' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(5)
    for tr in tocpage.body.find_all('tr'):
        rec = False
        for td in tr.find_all('td', attrs = {'headers' : 't1'}):
            for a in td.find_all('a'):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
                rec['artlink'] = universities[uni][1] + a['href'] + '?mode=full.716'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
        if not rec:
            for td in tr.find_all('td', attrs = {'headers' : 't3'}):
                for a in td.find_all('a'):
                    rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
                    rec['artlink'] = universities[uni][1] + a['href'] + '?mode=full.716'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
        for td in tr.find_all('td', attrs = {'headers' : 't2'}):
            if re.search('[12]\d\d\d', td.text):
                rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', td.text.strip())
                if int(rec['year']) >= now.year - 2:
                    prerecs.append(rec)
            else:
                print '(YEAR?)', td.text
                prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    interesting = True
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
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #email
            elif meta['name'] == 'citation_author_email':
                rec['autaff'][-1].append('EMAIL:' + meta['content'])
            #ORCID
            elif meta['name'] == 'citation_author_orcid':
                rec['autaff'][-1].append('ORCID:' + meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #pages
            elif meta['name'] == 'citation_lastpage':
                if re.search('^\d+$', meta['content']):
                    rec['pages'] = meta['content']
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' (the|of|and) ', meta['content']):
                    rec['abs'] = meta['content']
            #thesis type
            #elif meta['name'] == 'DC.type':
            #    if len(meta['content']) > 5:
            #        rec['note'].append(meta['content'])
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] in ['it', 'ita', 'italian']:
                    rec['language'] = 'italian'
            #keywords
            elif meta['name'] == 'DC.subject':
                if re.search(';.*;', meta['content']):
                    rec['keyw'] = re.split(' *; *', meta['content'])
            #department
            elif meta['name'] == 'citation_keywords':
                section = re.sub('Settore ', '', meta['content'])
                if re.search('^[A-Z][A-Z][A-Z]', section):
                    interesting = False
                    if section[:3] in ['FIS', 'INF', 'ING', 'MAT']:
                        rec['note'].append(section)
                        interesting = True
                    else:
                        print '  skip', section
    if not 'autaff' in rec.keys():
        for meta in artpage.find_all('meta', attrs = {'name' : 'DC.creator'}):
            rec['autaff'] = [[ meta['content'] ]]
    # :( meta-tags now hidden in JavaScript
    for table in artpage.body.find_all('table', attrs = {'class' : 'itemTagFields'}):
        for tr in table.find_all('tr'):
            for td in tr.find_all('td', attrs = {'class' : 'metadataFieldLabel'}):
                tdlabel = td.text.strip()
            for td in tr.find_all('td', attrs = {'class' : 'metadataFieldValue'}):
                #author
                if re.search('^Autori', tdlabel):
                    if not 'autaff' in rec.keys():
                        rec['autaff'] = [[td.text.strip()]]
                #supervisor
                elif re.search('^Tutore', tdlabel):
                    if not 'supervisor' in rec.keys():
                        rec['supervisor'] = [[td.text.strip()]]
                #title
                elif re.search('^Titolo', tdlabel):
                    if not 'tit' in rec.keys():
                        rec['tit'] = td.text.strip()
                #date
                elif re.search('^Data di', tdlabel):
                    if not 'date' in rec.keys():
                        rec['date'] = re.sub('.*(\d\d\d\d).*', r'\1', td.text.strip())
                #abstract
                elif re.search('^Abstract', tdlabel):
                    if not 'abs' in rec.keys():
                        if re.search(' the ', td.text):
                            rec['abs'] = td.text.strip()
                #language
                elif re.search('^Lingua', tdlabel):
                    if not 'language' in rec.keys():
                        if re.search('Ital', td.text.strip()):
                            rec['language'] = 'italian'
                #keywords
                elif re.search('^Parole.*Inglese', tdlabel):
                    if not 'keyw' in rec.keys():
                        rec['keyw'] = re.split('; ', td.text.strip())
                #section
                elif re.search('^Settore', tdlabel):
                    section = re.sub('Settore ', '', td.text.strip())
                    if re.search('^[A-Z][A-Z][A-Z]', section):
                        interesting = False
                        if section[:3] in ['FIS', 'INF', 'ING', 'MAT']:
                            rec['note'].append(td.text.strip())
                            interesting = True
                        else:
                            print '  skip', section
        #FFT
        if not 'FFT' in rec.keys():
            for div in artpage.body.find_all('div', attrs = {'class' : 'itemTagBitstreams'}):
                for span in div.find_all('span', attrs = {'class' : 'label'}):
                    if re.search('Open', span.text):
                        for a in div.find_all('a'):
                            if re.search('pdf$', a['href']):
                                rec['FFT'] = universities[uni][1] + a['href']
    if 'autaff' in rec.keys():
        rec['autaff'][-1].append(publisher)
        #year might be the year of deposition
        if 'date' in rec.keys() and not 'year' in rec.keys():
            rec['year'] = re.sub('.*([12]\d\d\d).*', r'\1', rec['date'])
        if 'year' in rec.keys() and not 'date' in rec.keys():
            rec['date'] = rec['year']
        #license
        for table in artpage.body.find_all('table', attrs = {'class' : 'ep_block'}):
            for a in table.find_all('a'):
                if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                    rec['licence'] = {'url' : a['href']}
        #abstract
        if not 'abs' in rec.keys():
            for p in artpage.find_all('p', attrs = {'class' : 'abstractIta'}):
                rec['abs'] = p.text.strip()
        #link
        if not 'doi' in rec.keys() and not 'hdl' in rec.keys():
            rec['link'] = rec['artlink']
        if interesting:
            recs.append(rec)
        #abstract
        if not 'abs' in rec.keys():
            for p in artpage.body.find_all('p', attrs = {'class' : 'abstractEng'}):
                rec['abs'] = p.text.strip()
    else:
        print '---[ NO AUTHOR! ]---  '

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
