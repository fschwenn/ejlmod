# -*- coding: utf-8 -*-
#harvest theses from NARCIS
#FS: 2019-09-15


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

publisher = 'NARCIS'
jnlfilename = 'THESES-NARCIS-%s' % (stampoftoday)

#check already harvested
ejldirs = ['/afs/desy.de/user/l/library/dok/ejl/onhold',
           '/afs/desy.de/user/l/library/dok/ejl/backup',
           '/afs/desy.de/user/l/library/dok/ejl/backup/%i' % (now.year-1)]
redoki = re.compile('THESES.NARCIS.*doki$')
rehttp = re.compile('^I\-\-(http.*id).*')
nochmal = []
bereitsin = []
for ejldir in ejldirs:
    print ejldir
    for datei in os.listdir(ejldir):
        if redoki.search(datei):
            inf = open(os.path.join(ejldir, datei), 'r')
            for line in inf.readlines():
                if len(line) > 1 and line[0] == 'I':
                    if rehttp.search(line):
                        http = rehttp.sub(r'\1', line.strip())
                        if not http in bereitsin:
                            if not http in nochmal:
                                bereitsin.append(http)
                                #print http
            print '  %6i %s' % (len(bereitsin), datei)



hdr = {'User-Agent' : 'Magic Browser'}

recs = []
for year in [str(now.year-1), str(now.year)]:
    page = 0
    complete = False
    while not complete:
        tocurl = 'https://www.narcis.nl/search/coll/publication/Language/EN/genre/doctoralthesis/dd_year/' + year + '/pageable/' + str(page)
        print tocurl
        try:
            req = urllib2.Request(tocurl, headers=hdr)
            tocpage = BeautifulSoup(urllib2.urlopen(req))
        except:
            print 'wait 5 minutes'
            time.sleep(300)
            req = urllib2.Request(tocurl, headers=hdr)
            tocpage = BeautifulSoup(urllib2.urlopen(req))
        for h1 in tocpage.body.find_all('h1', attrs = {'class' : 'search-results'}):
            target = re.sub('.*of (\d.*\d).*', r'\1', h1.text.strip())
            ntarget = int(re.sub('\D', '', target))
        for div in tocpage.body.find_all('div', attrs = {'class' : 'search-results'}):
            for div2 in div.find_all('div', attrs = {'class' : 'search-options'}):
                div2.replace_with('')
            for li in div.find_all('li'):
                for a in li.find_all('a'):
                    if a.has_attr('href'):
                        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'oa' : False}
                        rec['artlink'] = 'https://www.narcis.nl' + a['href']
                        rec['tit'] = re.sub(' \(\d\d\d\d\)$', '', a.text.strip())
                        rec['note'] = [ rec['artlink'], '%i of %i' % (len(recs) + 1, ntarget) ]
                        for img  in li.find_all('img', attrs = {'class' : 'open-access-logo'}):
                            rec['oa'] = True
                    ihttp = re.sub('(.*id).*', r'\1', rec['artlink'])
                    if ihttp in bereitsin:
                        print '   skip %s' % (rec['artlink'])
                    else:
                        recs.append(rec)
                        bereitsin.append(ihttp)
        print '---{ %i | %s }---{ %i/%i }---{ %s }---' % (page, tocurl, len(recs), ntarget, rec['artlink'])
        time.sleep(10)
        page += 1
        if len(recs) >= ntarget or 10*page >= ntarget:
            complete = True

        
time.sleep(3)

i = 0
dictrecs = {}
for rec in recs:
    uni = 'unknown'
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    #req = urllib2.Request(rec['artlink'], headers=hdr)    
    #artpage = BeautifulSoup(urllib2.urlopen(req))
    artfilename = '/tmp/%s_%08i' % (jnlfilename, i)
    if not os.path.isfile(artfilename):
        os.system('wget -T 300 -O %s "%s"' % (artfilename, rec['artlink']))
        time.sleep(5)
    inf = open(artfilename, 'r')
    artpage = BeautifulSoup(''.join(inf.readlines()))
    inf.close()
    for meta in artpage.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #affiliation            
            elif meta['name'] == 'citation_dissertation_institution':
                uni = meta['content']
                rec['autaff'][-1].append(uni)
            #abstract
            elif meta['name'] == 'citation_abstract':
                rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'citation_publication_date':
                rec['date'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if meta['content'] == 'nl':
                    rec['language'] = 'dutch'
                elif meta['content'] == 'fr':
                    rec['language'] = 'french'
                elif meta['content'] == 'es':
                    rec['language'] = 'spanish'
                elif meta['content'] == 'de':
                    rec['language'] = 'german'
                elif meta['content'] != 'en':
                    rec['note'].append(meta['content'])
    for table in artpage.find_all('table', attrs = {'class' : 'size02'}):
        for tr in table.find_all('tr'):
            for th in tr.find_all('th'):
                tht = th.text.strip()
            for td in tr.find_all('td'):
                tdt = td.text.strip()
            if tht == 'Reference(s)':
                rec['keyw'] = re.split(', ', tdt)
            elif tht == 'ISBN':
                isbns = re.split(' *; *', tdt)
                rec['isbns'] = [[('a', re.sub('\-', '', isbn))] for isbn in isbns]
            elif re.search('DOI$', tht):
                rec['doi'] = tdt
            elif re.search('Handle$', tht):
                rec['hdl'] = tdt
            elif re.search('NBN$', tht):
                rec['urn'] = tdt
            elif tht == 'Persistent Identifier':
                if tdt[:4] in ['urn', 'URN']:
                   rec['urn'] = tdt
            elif tht == 'Publication':
                rec['link'] = tdt
                if not 'hdl' in rec.keys() and not 'doi' in rec.keys():
                    if re.search('\/handle\/\d', rec['link']):
                        rec['hdl'] = re.sub('.*handle\/', '', rec['link'])
    if 'link' in rec.keys():
        print '  try to get PDF from %s' % (rec['link'])
        try:
            req = urllib2.Request(rec['link'], headers=hdr)
            origpage = BeautifulSoup(urllib2.urlopen(req))
            for meta in origpage.head.find_all('meta'):
                if meta.has_attr('name'):
                    if meta['name'] == 'citation_pdf_url':
                        if rec['oa']:
                            rec['FFT'] = meta['content']
                        else:
                            rec['hidden'] = meta['content']
                        print '  found PDF: %s' % (meta['content'])
                    if meta['name'] == 'citation_isbn':
                        if not 'isbn' in rec.keys():
                            rec['isbn'] = meta['content']
                    if meta['name'] == 'citation_doi':
                        if not 'doi' in rec.keys():
                            rec['doi'] = meta['content']    
        except:
            print '  could not find PDF'
        if not 'FFT' in rec.keys():
            rec['link'] = rec['artlink']
        if 'hdl' in rec.keys() or 'doi' in rec.keys():
            del rec['link']
    if not 'doi' in rec.keys() and not 'isbn' in rec.keys() and not 'urn' in rec.keys() and not 'hdl' in rec.keys():
        rec['doi'] = '20.2001/NARCIS/' + re.sub('\W', '', rec['artlink'])
    print rec
    print [(kk, len(dictrecs[kk])) for kk in dictrecs.keys()]
    for body in artpage.find_all('body'):
        unikey = re.sub('\W', '', uni)
        unikey = re.sub('[a-z]', '', unikey)
        #avoid lots of files with just 1 record
        unikey = str(len(recs))
        j = 0
        while unikey in dictrecs.keys() and len(dictrecs[unikey]) >= 150:
            j += 1
            unikey = re.sub('\d', '', unikey) + str(j)
        if unikey in dictrecs.keys():
            dictrecs[unikey].append(rec)
        else:
            dictrecs[unikey] = [rec]

if len(recs) < 200:
    jnlfilename = 'THESES-NARCIS-%s' % (stampoftoday)
    #closing of files and printing
    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
    ejlmod2.writeXML(recs, xmlfile, publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path,"r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,"a")
        retfiles.write(line)
        retfiles.close()
#if there are too many records, split by university
else:
    for unikey in dictrecs.keys():
        print unikey, len(dictrecs[unikey])
        jnlfilename = 'THESES-NARCIS-%s-%s' % (stampoftoday, unikey)
        #closing of files and printing
        xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
        ejlmod2.writeXML(dictrecs[unikey], xmlfile, publisher)
        xmlfile.close()
        #retrival
        retfiles_text = open(retfiles_path,"r").read()
        line = jnlfilename+'.xml'+ "\n"
        if not line in retfiles_text: 
            retfiles = open(retfiles_path,"a")
            retfiles.write(line)
            retfiles.close()
