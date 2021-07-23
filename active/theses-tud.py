# -*- coding: utf-8 -*-
#harvest theses from TU Dortmund
#FS: 2019-09-13

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

publisher = 'Tech. U., Dortmund (main)'

jnlfilename = 'THESES-TUD-%s' % (stampoftoday)
recs = []
hdr = {'User-Agent' : 'Magic Browser'}

### TUPrints ###
tocurl = 'https://tuprints.ulb.tu-darmstadt.de/view/subjects/ddc=5Fdnb=5F530.html'
print tocurl

prerecs = []
req = urllib2.Request(tocurl, headers=hdr)
tocpage = BeautifulSoup(urllib2.urlopen(req))
time.sleep(3)

for p in tocpage.body.find_all('p'):
    pt = re.sub('[\n\t\r]', ' ', p.text.strip())
    doctype = re.sub('.*\[(.*)\].*', r'\1', pt)
    if re.search('Ph.*hesis', doctype) or re.search('abilitation', doctype):
        for a in p.find_all('a'):
            for em in a.find_all('em'):
                takeit = True
                rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
                rec['artlink'] = a['href']
                if re.search('\([12]\d\d\d\)', p.text):
                    rec['year'] = re.sub('.*\(([12]\d\d\d)\).*', r'\1', pt)
                    if int(rec['year']) < now.year - 1:
                        print '  skip %s' % (rec['year'])
                        takeit = False
                if takeit:
                    prerecs.append(rec)
    else:
        print '  skip %s' % (doctype)

i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(prerecs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(4)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    #author
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.creators_name'}):
        rec['autaff'] = [[ meta['content'] ]]
    #language
    for meta in artpage.head.find_all('meta', attrs = {'name' : 'eprints.language'}):
        if  meta['content'] == 'de':
            rec['language'] = 'german'
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'eprints.contact_email':
                rec['autaff'][0].append('EMAIL:' + meta['content'])
            #title
            elif meta['name'] == 'eprints.title':
                rec['tit'] = meta['content']
            #keywords
            elif meta['name'] == 'eprints.keywords':
                rec['keyw'] = re.split('[,;] ', meta['content'])
            #abstract
            elif meta['name'] == 'eprints.abstract':
                if not 'language' in rec.keys():
                    rec['abs'] = meta['content']
            elif meta['name'] == 'eprints.abstractalternative_name':
                if 'language' in rec.keys():
                    rec['abs'] = meta['content']
            #date
            elif meta['name'] == 'eprints.date':
                rec['date'] = meta['content']
            #DOI
            elif meta['name'] == 'eprints.doi':
                rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            #alternate title
            elif meta['name'] == 'eprints.titlealternative_name':
                if 'language' in rec.keys():
                    rec['transtit'] = meta['content']
            #URN
            elif meta['name'] == 'eprints.urn':
                rec['urn'] = meta['content']
            #fulltext
            elif meta['name'] == 'eprints.document_url':
                rec['fulltextlink'] = meta['content']
    #license
    for a in artpage.find_all('a'):
        if re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
    #FFT
    if 'fulltextlink' in rec.keys():
        if 'license' in rec.keys():
            rec['FFT'] = rec['fulltextlink']
        else:
            rec['hidden'] = rec['fulltextlink']
    rec['autaff'][0].append(publisher)
    recs.append(rec)
    print '   ', rec.keys()

### ELDORDO ###
tocurl = 'https://eldorado.tu-dortmund.de/handle/2003/35/browse?type=dateissued&sort_by=2&order=DESC&rpp=50&etal=0&submit_browse=Update'
print tocurl

prerecs = []
for offset in [0]:
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
    for td in tocpage.body.find_all('td', attrs = {'headers' : 't2'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for a in td.find_all('a'):
            rec['artlink'] = 'https://eldorado.tu-dortmund.de' + a['href']
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)


i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(prerecs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['link'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('Tech. U., Dortmund (main)')
            #doctype
            elif meta['name'] == 'DC.type':
                if meta['content'] == "doctoralThesis":
                    rec['tc'] = 'T'
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
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'por':
                    rec['language'] = 'portuguese'
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d+ pages', meta['content']):
                    rec['pages'] = re.sub('\D*(\d+) pages.*', r'\1', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #license
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
    if rec['tc'] == 'T':
        recs.append(rec)

#closing of files and printing
xmlf  = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
