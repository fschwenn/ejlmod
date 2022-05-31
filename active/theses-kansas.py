# -*- coding: utf-8 -*-
#harvest theses from Kansas State U.
#FS: 2020-02-10


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

publisher = 'Kansas State U.'

pages = 40

rejectwords = []
for rejectword in ['Department of Adult Learning', 'Department of Agricultural', 'Department of Agronomy',
                   'Department of Anatomy', 'Department of Animal', 'Department of Apparel', 'Department of Bio',
                   'Department of Chemi', 'Department of Civil Engineering', 'Department of Communications Studies',
                   'Department of Curriculum and Instruction', 'Department of Diagnostic',
                   'Department of Diagnostic Medicine and Pathobiology', 'Department of Economics',
                   'Department of Educational', 'Department of Entomology', 'Department of Environmental Design',
                   'Department of Family', 'Department of Food', 'Department of Geography',
                   'Department of Grain Science', 'Department of History', 'Department of Horticulture',
                   'Department of Hospitality Managemen', 'Department of Human', 'Department of Industrial',
                   'Department of Kinesiology', 'Department of Landscape', 'Department of Mechanical',
                   'Department of Modern Languages', 'Department of Music', 'Department of Plant',
                   'Department of Plant Pathology', 'Department of Psycho', 'Department of Psychological',
                   'Department of Soci', 'Department of Sociology', 'Department of Special Education',
                   'Department of Statistics', 'Kansas Department of Transportation', 'Master of ']:
    rejectwords.append(re.compile(rejectword))

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
jnlfilename = 'THESES-KANSASSTATE-%s' % (stampoftoday)
hdr = {'User-Agent' : 'Magic Browser'}
for page in range(pages):
    tocurl = 'https://krex.k-state.edu/dspace/handle/2097/4/recent-submissions?offset=' + str(page*5)
    print '---{ %i/%i }---{ %s }------' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(5)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-title'}):
        for a in div.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
            rec['artlink'] = 'https://krex.k-state.edu' + a['href']
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            if not rec['hdl'] in uninterestingDOIS:
                prerecs.append(rec)


i = 0
recs = []
for rec in prerecs:
    interesting = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(5)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['link'])
            continue
    keepit = True
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'citation_author':
                rec['autaff'] = [[ meta['content'] ]]
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #thesis type
            elif meta['name'] == 'DC.description':
                rec['note'].append(meta['content'])
                if keepit:
                    for rejectword in rejectwords:
                        if rejectword.search(meta['content']):
                            keepit = False
                            break
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                rec['keyw'] = re.split('; ', meta['content'])
    rec['autaff'][-1].append(publisher)
    if keepit:
        recs.append(rec)
    else:
        newuninterestingDOIS.append(rec['hdl'])

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

ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()

