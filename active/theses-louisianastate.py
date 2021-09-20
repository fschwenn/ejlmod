# -*- coding: utf-8 -*-
#harvest theses from Louisiana State U.
#FS: 2021-09-17

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
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'
numofpages = 2

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Louisiana State U.'

uninteresting = [re.compile('Master of ')]
uninteresting += [re.compile('Pharmaceutical'), re.compile('Physiology'), re.compile('Dentistry'),
                  re.compile('Chemistry'), re.compile('Biomedical'), re.compile('Biostatistics'),
                  re.compile('Chemical'), re.compile('Clinical'), re.compile('Education'),
                  re.compile('Electrical '), re.compile('English'), re.compile('Epidemiology'),
                  re.compile('Graphic'), re.compile('Health'), re.compile('History'),
                  re.compile('Human'), re.compile('Integrative Life Sciences'), re.compile('Pharmacy'),
                  re.compile('Interior Design'), re.compile('Kinetic Imaging'),
                  re.compile('Microbiology'), re.compile('Immunology'), re.compile('Neuroscience'),
                  re.compile('Nursing'), re.compile('Painting'), re.compile('Printmaking'),
                  re.compile('Photography'), re.compile('Film'), re.compile('Psychology'),
                  re.compile('Public Policy'), re.compile('Administration'), re.compile('Sculpture'),
                  re.compile('Extended Media'), re.compile('Special Education'), re.compile('Medical'),
                  re.compile('Systems Modeling'), re.compile('Theatre'), re.compile('Business'),
                  re.compile('Urban and Regional Planning'), re.compile('Biochemistry'),
                  re.compile('Nanoscience'), re.compile('Pharmacology'), re.compile('Toxicology'),
                  re.compile('Media'), re.compile('Biology'), re.compile('Therapy'),
                  re.compile('Rehabilitation'), re.compile('Social'), re.compile('Anatomy')]
uninteresting += [re.compile('Nutrition'), re.compile('Accounting'),
                  re.compile('Biological'), re.compile('Civil'), re.compile('Agricultural'),
                  re.compile('Oceanography'), re.compile('Pathobiological'), re.compile('Music'),
                  re.compile('Geography'), re.compile('Geology'), re.compile('Geophysics'),
                  re.compile('Sociology'), re.compile('Kinesiology'), re.compile('Natural'),
                  re.compile('Literature'), re.compile('Entomology'), re.compile('Finance'),
                  re.compile('Petroleum'), re.compile('Management'), re.compile('Medicine'),
                  re.compile('Economics'), re.compile('Communication'), re.compile('Enviromental'),
                  re.compile('Textiles,'), re.compile('Marketing'), re.compile('Animal'), 
                  re.compile('Political'), re.compile('Environmental'), re.compile('French')]

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
jnlfilename = 'THESES-LouisianaStateU-%s' % (stampoftoday)
for i in range(numofpages):
    #if i == 0:
    #    tocurl = 'https://digitalcommons.lsu.edu/gradschool_dissertations/index.html'
    #else:
    tocurl = 'https://digitalcommons.lsu.edu/gradschool_dissertations/index.%i.html' % (i+1)
    print '==={ %i/%i }==={ %s }===' % (i+1, numofpages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(3)
    for p in tocpage.body.find_all('p', attrs = {'class' : 'article-listing'}):
        for a in p.find_all('a'):
            rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : []}
            rec['artlink'] = a['href']
            prerecs.append(rec)

i = 0
recs = []
for rec in prerecs:
    i += 1
    disstyp = False
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['artlink'])
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
    #license
    for link in artpage.head.find_all('link', attrs = {'rel' : 'license'}):
        rec['license'] = {'url' : link['href']}
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'bepress_citation_author':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                for div in artpage.body.find_all('div', attrs = {'id' : 'orcid'}):
                    for p in div.find_all('p'):
                        rec['autaff'][-1].append('ORCID:%s' % (p.text.strip()))
                rec['autaff'][-1].append(publisher)
            #title
            elif meta['name'] == 'bepress_citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'bepress_citation_date':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'description':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'bepress_citation_pdf_url':
                if 'license' in rec.keys():
                    rec['FFT'] = meta['content']
                else:
                    rec['hidden'] = meta['content']
            #DOI
            elif meta['name'] == 'bepress_citation_doi':
                rec['doi'] = re.sub('.*org\/(10.*)', r'\1', meta['content'])
                rec['doi'] = re.sub('.*org\/doi:(10.*)', r'\1', rec['doi'])
            #typ of dissertation
            elif meta['name'] == 'bepress_citation_dissertation_name':
                disstyp = meta['content'].strip()
                rec['note'].append(disstyp)
    if not 'doi' in rec.keys():
        rec['doi'] = '30.3000/LousianaStateU/' + re.sub('\D', '', rec['artlink'])
        rec['link'] = rec['artlink']
    skipit = False
    if disstyp:
        for regexpr in uninteresting:
            if regexpr.search(disstyp):
                skipit = True
                print '    skip %s' % (disstyp)
                break
    #Department
    if not skipit:
        for div in artpage.body.find_all('div', attrs = {'id' : 'department'}):
            for p in div.find_all('p'):
                dep = p.text.strip()
                rec['note'].append(dep)
                for regexpr in uninteresting:
                    if regexpr.search(dep):
                        skipit = True
                        print '    skip %s' % (dep)
                        break
    if not skipit:
        recs.append(rec)
        print '    ', rec.keys()

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
