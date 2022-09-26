# -*- coding: utf-8 -*-
#harvest theses from MIT
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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'MIT'

typecode = 'T'

jnlfilename = 'THESES-MIT-%s' % (stampoftoday)

rpp = 100
pages = 4

#these keywords are in fact the departments/institute/PhD prorgams
boringkeywords = ['Joint Program in Biological Oceanography.',
                  'Joint Program in Marine Geology and Geophysics.',
                  'Joint Program in Physical Oceanography.',
                  "Woods Hole Oceanographic Institution",
                  "Massachusetts Institute of Technology. Department of Earth, Atmospheric, and Planetary Sciences",
                  'Sloan School of Management. Master of Finance Program.',
                  'Civil and Environmental Engineering.', 'Economics.',
                  'Harvard--MIT Program in Health Sciences and Technology.',
                  'Operations Research Center.', 'Biological Engineering.',
                  'Joint Program in Oceanography/Applied Ocean Science and Engineering.',
                  'Sloan School of Management.', 'Chemical Engineering.',
                  'Institute for Data, Systems, and Society.',
                  'Materials Science and Engineering.', 'Technology and Policy Program.',
                  'Center for Real Estate. Program in Real Estate Development.',
                  'Chemistry.', 'Program in Media Arts and Sciences',
                  'Aeronautics and Astronautics.', 'Biology.', 'Mechanical Engineering.',
                  'Earth, Atmospheric, and Planetary Sciences.',
                  'Woods Hole Oceanographic Institution.',
                  'Joint Program in Applied Ocean Science and Engineering',
                  'Joint Program in Oceanography/Applied Ocean Science and Engineering',
                  'Massachusetts Institute of Technology. Computational and Systems Biology Program',
                  'Massachusetts Institute of Technology. Department of Economics',
                  'Massachusetts Institute of Technology. Department of Political Science',
                  'Massachusetts Institute of Technology. Microbiology Graduate Program',
                  'Massachusetts Institute of Technology. Operations Research Center',
                  'Massachusetts Institute of Technology. Program in Science, Technology and Society',
                  'Massachusetts Institute of Technology. Department of Brain and Cognitive Sciences',
                  'Massachusetts Institute of Technology. Department of Linguistics and Philosophy',
                  'Massachusetts Institute of Technology. Department of Civil and Environmental Engineering',
                  'Massachusetts Institute of Technology. Graduate Program in Science Writing',
                  'Massachusetts Institute of Technology. Department of Biological Engineering',
                  'Massachusetts Institute of Technology. Department of Architecture',
                  'Massachusetts Institute of Technology. Department of Chemical Engineering',
                  'Massachusetts Institute of Technology. Department of Urban Studies and Planning',
                  'Massachusetts Institute of Technology. Department of Aeronautics and Astronautics',
                  'System Design and Management Program.', 'Sloan School of Management',
                  'Massachusetts Institute of Technology. Department of Materials Science and Engineering',
                  'Massachusetts Institute of Technology. Department of Biology',
                  'Massachusetts Institute of Technology. Department of Chemistry',
                  'Massachusetts Institute of Technology. Program in Comparative Media Studies/Writing',
                  'Program in Media Arts and Sciences (Massachusetts Institute of Technology)',
                  'Harvard-MIT Program in Health Sciences and Technology',
                  'Massachusetts Institute of Technology. Supply Chain Management Program',
                  'Massachusetts Institute of Technology. Center for Real Estate. Program in Real Estate Development.']

hdr = {'User-Agent' : 'Magic Browser'}

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
for page in range(pages):
    tocurl = 'https://dspace.mit.edu/handle/1721.1/7582/discover?sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&page=' + str(page+1)
    print page+1, pages, tocurl
#    try:
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(5)
#    except:
#        print "retry in 180 seconds"
#        time.sleep(180)
#        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open('%s%i' % (tocurl, offset)))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://dspace.mit.edu' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            if not rec['hdl'] in uninterestingDOIS:
                prerecs.append(rec)


recs = []
i = 0
for rec in prerecs:
    i += 1
    keepit = True
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(10)
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
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('MIT')
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
                    if keyw in boringkeywords:
                        keepit = False
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
            #department
            elif meta['name'] == 'DC.contributor':
                dep = meta['content']
                if dep in boringkeywords:
                    keepit = False
                else:
                    rec['note'].append(dep)
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

