# -*- coding: utf-8 -*-
#harvest theses from Izmir Inst. Tech.
#FS: 2020-12-24

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Izmir Inst. Tech.'

#bad certificate
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

rpp = 50
pages = 1
boringfacs = ['Architecture', 'Chemistry', 'Architectural Restoration',
              'Biotechnology and Bioengineering', 'Civil Engineering', 
#              'Computer Engineering', 'Electronics and Communication Engineering', 
              'Food Engineering', 'Materials Science and Engineering',
              'Chemical Engineering', 'City and Regional Planning',
              'Molecular Biology and Genetics']
hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-IZMIR-%s' % (stampoftoday)


inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
for page in range(pages):
    tocurl = 'https://openaccess.iyte.edu.tr/xmlui/handle/11147/60/discover?filtertype=type&filter_relational_operator=equals&filter=doctoralThesis&sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp) + '&page=' + str(page+1)
    tocurl = 'https://openaccess.iyte.edu.tr/browse?type=type&sort_by=2&order=DESC&rpp=' + str(rpp) + '&etal=-1&value=doctoralThesis&offset=' + str(rpp*page)
    tocurl = 'https://openaccess.iyte.edu.tr/simple-search?query=&location=publications&filter_field_1=itemtype&filter_type_1=equals&filter_value_1=Doctoral+Thesis&filter_field_2=dateIssued&filter_type_2=equals&filter_value_2=%5B2021+TO+2040%5D&crisID=&relationName=&sort_by=score&order=desc&rpp=' + str(rpp) + '&etal=0&start=' + str(rpp*page)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    try:
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
    except:
        print "retry in 300 seconds"
        time.sleep(300)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
    time.sleep(3)
    for div in tocpage.body.find_all('td', attrs = {'headers' : 't2'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : [], 'supervisor'  : []}
        for a in div.find_all('a'):
            rec['link'] = 'https://openaccess.iyte.edu.tr' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            if not rec['hdl'] in uninterestingDOIS:
                prerecs.append(rec)

recs = []
i = 0
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }---' % (i, len(prerecs), len(recs), rec['link'])
    try:
        req = urllib2.Request(rec['link'], headers=hdr)
        artpage = BeautifulSoup(urllib2.urlopen(req, context=ctx))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['link']))
        except:
            print "no access to %s" % (rec['link'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
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
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if re.search(' the ', meta['content']):
                    rec['abs'] = meta['content']
            #language
            elif meta['name'] == 'citation_language':
                if not meta['content'] in ['eng', 'en']:
                    rec['language'] = meta['content']
            #pages
            elif meta['name'] == 'DCTERMS.extent':
                if re.search('\d\d', meta['content']):            
                    rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', meta['content'])
    for tr in artpage.body.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            label = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            #department
            if label in ['dc.contributor.department', 'dc.department']:
                fac = re.sub('.zmir Institute of Technology. ', '', td.text.strip())
                if fac in boringfacs:
                    keepit = False
                else:
                    rec['note'].append(fac)
            #supervisor
            elif label == 'dc.contributor.advisor':
                rec['supervisor'].append([td.text.strip()])
            #ORCID
            elif label == 'dc.authorid':
                rec['autaff'][-1].append(['ORCID:'+td.text.strip()])
    rec['autaff'][-1].append(publisher)
    if keepit:
        print '  ', rec.keys()
        recs.append(rec)
    else:
        newuninterestingDOIS.append(rec['hdl'])


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


ouf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'a')
for doi in newuninterestingDOIS:
    ouf.write(doi + '\n')
ouf.close()

        
