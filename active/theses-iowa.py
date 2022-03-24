# -*- coding: utf-8 -*-
#harvest theses from Iowa State U. (main)
#FS: 2020-04-08

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

publisher = 'Iowa State U. (main)'
hdr = {'User-Agent' : 'Magic Browser'}

rpp = 10
pages = 1
recs = []
jnlfilename = 'THESES-IOWASTATE-%s' % (stampoftoday)

boringdegrees = ['Master of Science']

for (fc, dep) in [('', 'Physics%20and%20Astronomy'), ('m', 'Mathematics')]:
    for page in range(pages):
        print '==={ %i/%i %s }===' % (page+1, pages, dep)
        tocurl = 'https://dr.lib.iastate.edu/collections/0830d32e-14e1-4a4f-bb8f-271a75ed35af?scope=0830d32e-14e1-4a4f-bb8f-271a75ed35af&view=listElement&f.department=' + dep + ',equals&spc.sf=dc.date.issued&spc.sd=DESC&spc.rpp=' + str(rpp) + '&spc.page=' + str(page+1)
        print '  ', tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        for script in tocpage.find_all('script', attrs = {'id' : 'dspace-angular-state'}):
            scriptt = re.sub('&q;', '"', re.sub('[\n\t]', '', script.contents[0].strip()))
            scripttjson = json.loads(scriptt)
            for k in scripttjson['NGRX_STATE']['core']['cache/object'].keys():
                keepit = True
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'supervisor' : []}
                if fc: rec['fc'] = fc
                if 'metadata' in scripttjson['NGRX_STATE']['core']['cache/object'][k]['data'].keys():
                    metadata = scripttjson['NGRX_STATE']['core']['cache/object'][k]['data']['metadata']
                    #print 'K', metadata.keys()
                    for tag in metadata.keys():
                        #degree
                        if tag == 'thesis.degree.name':
                            degree = metadata[tag][0]['value']
                            if degree in boringdegrees:
                                keepit = False
                            else:
                                rec['note'].append(degree)
                        elif tag == 'dc.type.genre':
                            rec['note'].append(metadata[tag][0]['value'])
                        #date
                        elif tag == 'dc.date.issued':
                            rec['date'] = metadata[tag][0]['value']
                        #title
                        elif tag == 'dc.title':
                            rec['tit'] = metadata[tag][0]['value']
                        #supervisor
                        elif tag == 'dc.contributor.advisor':
                            for value in metadata[tag]:
                                rec['supervisor'].append([value['value']])
                        #embargo
                        elif tag == 'dc.date.embargo':
                            rec['embargo'] = (metadata[tag][0]['value'] > stampoftoday)
                        #DOI
                        elif tag == 'dc.identifier.doi':
                            rec['doi'] = re.sub('.*doi.org\/', '', metadata[tag][0]['value'])
                        #keywords
                        elif tag == 'dc.subject':
                            rec['keyw'] = []
                            for value in metadata[tag]:
                                rec['keyw'].append(value['value'])
                        #abstract
                        elif tag == 'dc.description.abstract':
                            rec['abs'] = re.sub('&l;.?p&g;', '', metadata[tag][0]['value'])
                        #author
                        elif tag == 'dc.contributor.author':
                            rec['autaff'] = [[ metadata[tag][0]['value'], publisher ]]
                        #link
                        elif tag == 'dc.identifier.uri':
                            rec['artlink'] = metadata[tag][0]['value']
                            if re.search('handle\/20.500.12876', rec['artlink']):
                                rec['hdl'] = re.sub('.*handle\/', '', rec['artlink'])
                            if not 'dc.identifier.doi' in metadata.keys():
                                rec['link'] = rec['artlink']
                    if keepit and 'autaff' in rec.keys():
                        recs.append(rec)
            time.sleep(5)

print 'get fulltext links'

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    req = urllib2.Request(rec['artlink'], headers=hdr)
    artpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for meta in artpage.head.find_all('meta', attrs = {'property' : 'citation_pdf_url'}):
        rec['hidden'] = 'https://dr.lib.iastate.edu' + meta['content']
    time.sleep(5)
    print '    ', rec.keys()
            

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path, 'r').read()
line = jnlfilename+'.xml'+ '\n'
if not line in retfiles_text:
    retfiles = open(retfiles_path, 'a')
    retfiles.write(line)
    retfiles.close()


