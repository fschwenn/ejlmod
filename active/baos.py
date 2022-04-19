# -*- coding: utf-8 -*-
#!/usr/bin/python
#program to harvest Bulgarian Academy of Science
# FS 2022-04-14

import sys
import os
import ejlmod2
import re
import urllib2
import urlparse
import codecs
from bs4 import BeautifulSoup
import time

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"
tmpdir = '/tmp'

def tfstrip(x): return x.strip()
regexpref = re.compile('[\n\r\t]')

typecode = 'P'

issueid = sys.argv[1]

publisher = 'Bulgarian Academy of Sciences'
urltrunk = 'http://www.proceedings.bas.bg/index.php/cr/issue/view/%s' % (issueid)
    
print urltrunk
try:
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk), features="lxml")
    time.sleep(3)
except:
    print "retry %s in 180 seconds" % (urltrunk)
    time.sleep(180)
    tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(urltrunk), features="lxml")

recs = []
for div in tocpage.body.find_all('div', attrs = {'class' : 'section'}):
    for h2 in div.find_all('h2'):
        note = regexpref.sub('', h2.text).strip()
        print ' - %s - ' % (note)
    for h3 in div.find_all('h3'):
        rec = {'jnl' : 'Compt.Rend.Acad.Bulg.Sci.', 'tc' : 'P', 'note' : [note], 'keyw' : [],
               'autaff' : []}
        if note in ['Mathematics']:
            rec['fc'] = 'm'
        elif note in ['Chemistry', 'Biology', 'Medicine', 'Geophysics', 'Agricultural Sciences'
                      'Engineering Sciences', 'Geology']:
            rec['fc'] = 'o'
        elif note in ['Space Sciences']:
            rec['fc'] = 'a'
        for a in h3.find_all('a'):
            rec['artlink'] = a['href']
            recs.append(rec)

i = 0
for rec in recs:
    i += 1
    autaff = False
    time.sleep(3)
    print '---{ %i/%i }---{ %s }---' % (i, len(recs), rec['artlink'])
    artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #date
            if meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #article ID
            elif meta['name'] == 'citation_firstpage':
                rec['p1'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'].append(meta['content'])
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #authors and affiliations
            elif meta['name'] == 'citation_author':
                rec['autaff'].append([ meta['content'] ])
            elif meta['name'] == 'citation_author_institution':
                rec['autaff'][-1].append(meta['content'])
            #volume and issue
            elif meta['name'] == 'citation_issue':
                    rec['issue'] = meta['content']
            elif meta['name'] == 'citation_volume':
                    rec['vol'] = meta['content']
            #abstract
            elif meta['name'] == 'DC.Description':
                rec['abs'] = meta['content']
            #fulltext
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
                            
            #references
            elif meta['name'] == 'citation_reference':
                rec['refs'].append([('x', meta['content'])])
    print [(k, len(rec[k])) for k in rec.keys()]

jnlfilename = 'crabs%s.%s_%s' % (rec['vol'], rec['issue'], issueid)
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
 
