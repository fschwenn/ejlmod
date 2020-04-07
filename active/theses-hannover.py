# -*- coding: utf-8 -*-
#harvest theses from Leibniz U., Hannover
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

publisher = 'Leibniz U., Hannover'

numberofpages = 4
recordsperpage = 50

prerecs = []
recs = []
jnlfilename = 'THESES-HANNOVER-%sOLD' % (stampoftoday)
for pn in range(numberofpages):
    tocurl = 'https://www.repo.uni-hannover.de/handle/123456789/2962/browse?rpp=' + str(recordsperpage) + '&sort_by=2&type=dateissued&offset=' + str(pn * recordsperpage) + '&etal=-1&order=DESC'
    print '==={ %i/%i }==={ %s }===' % (pn+1, numberofpages, tocurl)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for a in div.find_all('a'):
            if re.search('handle\/\d', a['href']):
                rec['artlink'] = 'https://www.repo.uni-hannover.de' + a['href'] #+ '?show=full'
                rec['doi'] = re.sub('.*handle\/(.*\d).*', r'20.2000/Hannover/\1', a['href'])
                prerecs.append(rec)
    time.sleep(10)

i = 0
for rec in prerecs:
    wrongddc = False
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
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('doi.org\/10', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/(10.*)', r'\1', meta['content'])
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            elif meta['name'] == 'DC.subject':
                #DDC
                if meta.has_attr('scheme') and meta['scheme'] == 'DCTERMS.DDC':
                    rec['ddc'] = meta['content']
                    rec['note'].append(meta['content'])
                    if not rec['ddc'][:2] in ['50', '51', '52', '53']:
                        print '  skip DDC=%s' % (rec['ddc'])
                        wrongddc = True
                #keywords
                elif meta['xml:lang'] == 'eng':
                    for keyw in re.split(' *; *', meta['content']):
                        rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] in ['ger']:
                    rec['language'] = 'german'
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
    if 'pdflink' in rec.keys():
        if 'licence' in rec.keys():
            rec['FFT'] = rec['pdflink']
        else:
            rec['hidden'] = rec['pdflink']
    if not wrongddc:
        print rec.keys()
        recs.append(rec)

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf,mode='wb'), 'utf8')
ejlmod2.writeXML(recs, xmlfile, publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, "r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text:
    retfiles = open(retfiles_path, "a")
    retfiles.write(line)
    retfiles.close()
