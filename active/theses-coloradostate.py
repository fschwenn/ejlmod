# -*- coding: utf-8 -*-
#harvest theses from Colorado State U., Fort Collins
#FS: 2021-12-06

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Colorado State U., Fort Collins'

jnlfilename = 'THESES-ColoradoStateU-%s' % (stampoftoday)

rpp = 20
pages = 1

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
for dep in [('Physics', '', '100500', 'Colorado State U.'),
            ('Mathematics', 'm', '100469', 'Colorado State U., Fort Collins')]:
    for page in range(pages):
        tocurl = 'https://mountainscholar.org/handle/10217/' + dep[2] + '/discover?rpp=' + str(rpp) + '&etal=0&group_by=none&page=' + str(page+1) + '&sort_by=dc.date.issued_dt&order=desc'
        print '==={ %s %i/%i }==={ %s }===' % (dep[0], page+1, pages, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
        divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
        for div in divs:
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : [], 'affiliation' : dep[3], 'note' : []}
            if dep[1]:
                rec['fc'] = dep[1]
            for a in div.find_all('a'):
                rec['artlink'] = 'https://mountainscholar.org' + a['href'] + '?show=full'
                if re.search('handle\/', a['href']):
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
                else:
                    print '  skip ', rec['artlink']
        time.sleep(10)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(5)
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
                rec['autaff'][-1].append(rec['affiliation'])
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
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'pdf_url' in rec.keys():
                rec['FFT'] = rec['pdf_url']
    #upload PDF at least hidden
    if not 'FFT' in rec.keys() and 'pdf_url' in rec.keys():
        rec['hidden'] = rec['pdf_url']
    #supervisor + degree
    for tr in artpage.find_all('tr'):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            tdt = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            if tdt == 'dc.contributor.advisor':
                rec['supervisor'].append([td.text.strip()])
            elif tdt == 'thesis.degree.level':
                degree = td.text.strip()
                if degree != 'Doctoral':
                    rec['note'].append(degree)
    print '   ', rec.keys()


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
