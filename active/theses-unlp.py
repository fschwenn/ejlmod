# -*- coding: utf-8 -*-
#harvest theses from Universidad Nacional de La Plata
#FS: 2020-06-30

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

publisher = 'UNLP, La Plata (main) '
rpp = 50
pages = 2
uninteresting = ['Qumica', 'Biologa', 'Bioqumica', 'Ciencias Sociales', 'Ciencias Veterinarias', 'Farmacia']

jnlfilename = 'THESES-UNLP-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
handles = []
for page in range(pages):
    tocurl = 'http://sedici.unlp.edu.ar/handle/10915/23/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
    for li in tocpage.body.find_all('li', attrs = {'class' : 'ds-artifact-item'}):
        for div in li.find_all('div', attrs = {'class' : 'type'}):
            if re.search('maestria', div.text) or re.search('grado', div.text):
                print '  skip', div.text.strip()
            else:
                for div in li.find_all('div', attrs = {'class' : 'artifact-description'}):
                    rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'note' : []}
                    for a in div.find_all('a'):
                        rec['artlink'] = 'http://sedici.unlp.edu.ar' + a['href'] + '?show=full'
                        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                        rec['tit'] = a.text.strip()
                        if not rec['hdl'] in handles:
                            prerecs.append(rec)
                            handles.append(rec['hdl'])

recs = []
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
                rec['autaff'] = [[ author, publisher ]]
            #supervisor
            elif meta['name'] == 'DC.contributor':
                rec['supervisor'].append([meta['content']])
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
                    rec['subject'] = keyw
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'es':
                    rec['language'] = 'spanish'
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
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org\/10', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/(10.*)', r'\1', meta['content'])
            #type
            elif meta['name'] == 'DC.type':
                rec['note'].append(meta['content'])

    if 'subject' in rec.keys():
        if rec['subject'].encode('ascii','ignore') in uninteresting:
            print '  skip', rec['subject'].encode('ascii','ignore')
        else:
            rec['note'].append(rec['subject'].encode('ascii','ignore'))
            recs.append(rec)
    else:
        recs.append(rec)	

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
