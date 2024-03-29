# -*- coding: utf-8 -*-
#harvest theses from Cambridge Univeristy
#FS: 2018-02-02


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
startyear = now.year - 1

publisher = 'Cambridge U.'

typecode = 'T'

jnlfilename = 'THESES-CAMBRIDGE-%s' % (stampoftoday)


tocurls = []
tocurls.append('https://www.repository.cam.ac.uk/handle/1810/256064/discover?rpp=100&etal=0&scope=&group_by=none&page=1&sort_by=dc.date.issued_dt&order=desc&filtertype_0=type&filter_relational_operator_0=equals&filter_0=Thesis')
tocurls.append('https://www.repository.cam.ac.uk/handle/1810/256064/discover?rpp=100&etal=0&scope=&group_by=none&page=2&sort_by=dc.date.issued_dt&order=desc&filtertype_0=type&filter_relational_operator_0=equals&filter_0=Thesis')
tocurls.append('https://www.repository.cam.ac.uk/handle/1810/256064/discover?rpp=100&etal=0&scope=&group_by=none&page=1&sort_by=dc.date.issued_dt&order=asc&filtertype_0=type&filter_relational_operator_0=equals&filter_0=Thesis')
tocurls.append('https://www.repository.cam.ac.uk/handle/1810/256064/discover?rpp=100&etal=0&scope=&group_by=none&page=2&sort_by=dc.date.issued_dt&order=asc&filtertype_0=type&filter_relational_operator_0=equals&filter_0=Thesis')
tocurls.append('https://www.repository.cam.ac.uk/handle/1810/256064/discover?rpp=100&etal=0&scope=&group_by=none&page=3&sort_by=dc.date.issued_dt&order=asc&filtertype_0=type&filter_relational_operator_0=equals&filter_0=Thesis')

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
dois = []
for tocurl in tocurls:
    try:
        print tocurl
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (tocurl)
        time.sleep(180)
        tocpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(tocurl))

    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'jnl' : 'BOOK', 'supervisor' : []}
        for h4 in div.find_all('h4'):
            for a in h4.find_all('a'):
                rec['tit'] = a.text.strip()
                rec['link'] = 'https://www.repository.cam.ac.uk' + a['href']
                rec['doi'] = '20.2000/OXFORD/' + re.sub('\W', '', a['href'])
                if not rec['doi'] in dois and not rec['doi'] in uninterestingDOIS:
                    prerecs.append(rec)
                    dois.append(rec['doi'])

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['link'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        time.sleep(3)
    except:
        print "retry %s in 180 seconds" % (rec['link'])
        time.sleep(180)
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            if meta['name'] == 'DC.creator':
                rec['auts'] = [ meta['content'] ]
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            elif meta['name'] == 'citation_pdf_url':
                rec['FFT'] = meta['content']
            elif meta['name'] == 'DC.identifier':
                if re.search('^10\.\d+\/', meta['content']):
                    rec['doi'] = meta['content']
            elif meta['name'] == 'citation_date':
                rec['date'] = meta['content']
    aff = []
    for div in artpage.body.find_all('div', attrs = 'item-page-field-wrapper'):
        for h5 in div.find_all('h5'):
            h5text = h5.text.strip()
        if h5text == 'Authors':
            for div2 in div.find_all('div'):
                rec['auts'] = [ div2.text.strip() ]
                for a in div2.find_all('a', attrs = {'title' : 'ORCID iD'}):
                    rec['auts'] = [ a.text.strip() + re.sub('.*\/(.*)', r', ORCID:\1', a['href']) ]
        elif h5text == 'Advisors':
            for div2 in div.find_all('div'):
                sv = [ div2.text.strip() ]
                for a in div2.find_all('a', attrs = {'title' : 'ORCID iD'}):
                    sv.append(re.sub('.*\/(.*)', r'ORCID:\1', a['href']))
                rec['supervisor'].append(sv)
        elif h5text == 'Author Affiliation':
            aff += [div2.text.strip() for div2 in div.find_all('div')]
        elif h5text == 'Awarding Institution':
            aff += [div2.text.strip() for div2 in div.find_all('div')]
        elif h5text == 'Qualification':
            for div2 in div.find_all('div'):
                dt = div2.text.strip()
                if dt in ['MPhil']:
                    print '  skip "%s"' % (dt)
                    keepit = False
                else:
                    rec['note'] = [ dt ]
                
    rec['aff'] = [ ', '.join(aff) ]
    if keepit:
        recs.append(rec)
        print '   ', rec.keys()
    else:
        newuninterestingDOIS.append(rec['doi'])
                                                          
        
    
    
#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
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
