# -*- coding: utf-8 -*-
#harvest theses from greek national archive of PhD theses
#FS: 2021-02-08

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special/'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'didaktorika.gr'
jnlfilename = 'THESES-DIDAKTORIKA-%s' % (stampoftoday)

rpp = 50
pages = 2

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for page in range(pages):
    tocurl = 'https://www.didaktorika.gr/eadd/browse?type=subject&value=Physical+Sciences&sort_by=2&order=DESC&rpp=' + str(rpp) + '&submit_browse=Update&locale=en&offset=' + str(page*rpp)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
    for tr in tocpage.body.find_all('tr'):
        if tr.find_all('th'):
            continue
        for td in tr.find_all('td', attrs = {'headers' : 't1'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'auts' : []}
            rec['year'] = td.text.strip()
            rec['date'] = td.text.strip()
            if int(rec['date']) > now.year - 2:
                for td2 in tr.find_all('td', attrs = {'headers' : 't2'}):
                    for a in td2.find_all('a'):
                        rec['artlink'] = 'https://www.didaktorika.gr' + a['href']
                    recs.append(rec)
    print '  %i records do far' % (len(recs))
    time.sleep(10)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        req = urllib2.Request(rec['artlink'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        time.sleep(3)
    except:
        try:
            print "   retry %s in 15 seconds" % (rec['artlink'])
            time.sleep(15)
            req = urllib2.Request(rec['artlink'], headers=hdr)
            artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx), features="lxml")
        except:
            print "   no access to %s" % (rec['artlink'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                if meta.has_attr('xml:lang'):
                    if meta['xml:lang'] in ['EN', 'en']:
                        rec['auten'] = meta['content']
                    elif meta['xml:lang'] in ['EL', 'el']:
                        rec['autel'] = meta['content']
                else:
                    rec['auts'] = [ meta['content'] ]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
                if meta.has_attr('xml:lang') and meta['xml:lang'] in ['EL', 'el']:
                    for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'DCTERMS.alternative'}):
                        rec['transtit'] = meta2['content']
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\D[123]\d\d\D', meta['content']):
                    rec['pages'] = re.sub('.*\D([123]\d\d).*', r'\1', meta['content'])
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #langauge
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'Greek':
                    rec['language'] = 'Greek'
            #keywords
            elif meta['name'] == 'DC.subject':
                if meta.has_attr('xml:lang') and meta['xml:lang'] in ['EN', 'en']:
                    for keyw in re.split(' *; *', meta['content']):
                        rec['keyw'].append(keyw)
            #license
            elif meta['name'] == 'DC.relation':
                if re.search('^BY', meta['content']):
                    rec['license'] = {'statement' : 'CC-' + re.sub('_', '-', meta['content'])}
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta.has_attr('xml:lang'):
                    if meta['xml:lang'] in ['EN', 'en']:
                        rec['abs'] = meta['content']
                    elif meta['xml:lang'] in ['EL', 'el']:
                        rec['absel'] = meta['content']
            #handle
            elif meta['name'] == 'citation_abstract_html_url':
                if re.search('handle.net\/\d', meta['content']):
                    rec['hdl'] = re.sub('.*handle.net\/', '', meta['content'])
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('^10\.\d+\/',  meta['content']):
                    rec['doi'] = meta['content']
    #authors
    if 'auten' in rec.keys():
        if 'autel' in rec.keys():
            rec['auts'] = [ '%s, CHINESENAME: %s' %  (rec['auten'], rec['autel']) ]
        else:
            rec['auts'] = [ rec['auten'] ]
    elif 'autel' in rec.keys():
        rec['auts'] = [ rec['autel'] ]
    #abstract
    if not 'abs' in rec.keys() and 'absel' in rec.keys():
        rec['abs'] = rec['absel']
    #pseudodoi
    if not 'hdl' in rec.keys() and not 'doi' in rec.keys():
        rec['doi'] = '20.2000/Didktorika/' + re.sub('\D', '', rec['artlink'])
        rec['link'] = rec['artlink']
    print '  ', rec.keys()

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
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
