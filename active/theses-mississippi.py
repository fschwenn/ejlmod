# -*- coding: utf-8 -*-
#harvest theses from Mississippi U.
#FS: 2020-05-26


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
numofpages = 1

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Mississippi U.'

uninteresting = [re.compile('M\.A\.'), re.compile('M\.S\.'), re.compile('Ed\.D\.'),
                 re.compile('Ed\.S\.'), re.compile('M\.C\.J\.'), re.compile('M\.F\.A\.'),
                 re.compile('M\.M\.'), re.compile('Accountancy'), re.compile('Art'),
                 re.compile('Biological Science'), re.compile('Business Administration'),
                 re.compile('Chemistry'), re.compile('Counselor Education'),
                 re.compile('Creative Writing'), re.compile('Criminal Justice'),
                 re.compile('Curriculum and Instruction'), re.compile('Documentary Expression'),
                 re.compile('Economics'), re.compile('Education'), re.compile('English'),
                 re.compile('Health and Kinesiology'), re.compile('Higher Education'),
                 re.compile('History'), re.compile('Music'),
                 re.compile('Pharmaceutical Sciences'), re.compile('Political Science'),
                 re.compile('Psychology')]


                 
hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
jnlfilename = 'THESES-MISSISSIPPI-%s' % (stampoftoday)
for i in range(numofpages):
    if i == 0:
        tocurl = 'https://egrove.olemiss.edu/etd/index.html'
    else:
        tocurl = 'https://egrove.olemiss.edu/etd/index.%i.html' % (i+1)
    print '---{ %i/%i }---{ %s }---' % (i+1, numofpages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
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
    print '---{ %i/%i }---{ %s }------{ %i }---' % (i, len(prerecs), rec['artlink'], len(recs))
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
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
                for meta2 in artpage.head.find_all('meta', attrs = {'name' : 'bepress_citation_author_institution'}):
                    rec['autaff'][-1].append(meta2['content']+', USA')
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
    if not 'doi' in rec.keys():
        rec['doi'] = '20.2000/Mississippi/' + re.sub('\D', '', rec['artlink'])
        rec['link'] = rec['artlink']
    skipit = False
    for regexpr in uninteresting:
        if regexpr.search(disstyp):
            skipit = True
            break
    if skipit:
        print 'skip %s' % (disstyp)
    else:
        rec['note'].append(disstyp)
        recs.append(rec)
        print rec.keys()

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
    
