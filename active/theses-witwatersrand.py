# -*- coding: utf-8 -*-
#harvest theses from Witwatersrand U.
#FS: 2020-11-17

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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' #+ '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" #+ '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'Witwatersrand U.'

rpp = 50
pages = 10
boringfacs = ['Faculty of Engineering and the Built Environment',
              'Faculty of Health Sciences', 'Faculty of Commerce',
              'Faculty of Humanities', 'School of Literature',
              'School of Social Sciences', 'Faculty of the Humanities',
              'Faculty of Engineering and the Built Environment',
              'Faculty of Humanities at the University of the Witwatersrand',
              'School of Physiology', 'School of Geography',
              'Faculty of Humanities University of the Witwatersrand',
              'School of Public Health', 'School of Geoscience',
              'School of Construction Economics and Management',
              'School of Chemical and Metallurgical Engineering',
              'School of Economic and Business Sciences',
              'Faculty of health science', 'Faculty of Humanities',
              'Faculty of Health Sciences', 'Faculty of commerce',
              'Faculty of Engineering and the Built Environment',
              'School of Geosciences', 'Faculty of Health Science',
              'School of Architecture and Planning',
              'Faculty of Engineering and Built Environment',
              'Faculty of Humanities at the University of Witwatersrand']
hdr = {'User-Agent' : 'Magic Browser'}
jnlfilename = 'THESES-WITWATERSRAND-%s' % (stampoftoday)

inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
for page in range(pages):
    tocurl = 'http://wiredspace.wits.ac.za/handle/10539/104/discover?order=desc&rpp=' + str(rpp) + '&sort_by=dc.date.issued_dt&page=' + str(page+1) + '&group_by=none&etal=0'
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    try:
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
    except:
        print "retry in 300 seconds"
        time.sleep(300)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    time.sleep(3)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'note' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'http://wiredspace.wits.ac.za' + a['href']# + '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            if not rec['hdl'] in uninterestingDOIS:
                prerecs.append(rec)

recs = []
i = 0
for rec in prerecs:
    keepit = True
    i += 1
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
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append(publisher)
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
                rec['abs'] = meta['content']
            #faculty
            elif meta['name'] == 'DC.description':
                mc = re.sub('[\n\t\r]', ' ', meta['content'])
                if re.search('[Ss]ubmitted', mc):
                    (deg, fac) = (False, False)
                    if re.search('(faculty|Faculty|School of|school of)', mc):
                        fac = re.sub('.*[fF]aculty', 'Faculty', mc)
                        fac = re.sub('.*[sS]chool', 'School', fac)
                        fac = re.sub(',.*', '', fac)
                        fac = re.sub(' in (partial)? full?fill?ment.*', '', fac)
                        if fac in boringfacs:
                            keepit = False
                        else:
                            rec['note'].append(fac)
                    if re.search('[De]gree of ', mc):
                        deg = re.sub('.*[De]gree of ', '', mc)
                        deg = re.sub('[,\.].*', '', deg)
                        deg = re.sub(' \d.*', '', deg)
                        if re.search('Masters? of', deg):
                            keepit = False
                        else:
                            rec['note'].append(deg)
                    if not deg and not fac:
                        rec['note'].append(mc)
                else:
                    rec['note'].append(mc)
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



