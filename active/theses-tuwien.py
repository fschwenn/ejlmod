# -*- coding: utf-8 -*-
#harvest theses from Wien
#FS: 2020-10-31
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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'#+'/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"#+'_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)
jnlfilename = 'THESES-TUWIEN-%s' % (stampoftoday)

publisher = 'Vienna, Tech. U.'

hdr = {'User-Agent' : 'Magic Browser'}

rpp = 20
pages = 30
boringinstitutes = ['E360', 'E017', 'E017', 'E105', 'E120', 'E163', 'E164', 'E165',
                    'E186', 'E187', 'E188', 'E194', 'E259', 'E311', 'E315', 'E322',
                    'E330', 'E317', 'E166', 'E253', 'E192', 'E193', 'E280', 'E251',
                    'E253', 'E259', 'E260', 'E264', 'E280', 'E285', 'E299', 'E202',
                    'E204', 'E206', 'E207', 'E208', 'E212', 'E220', 'E222', 'E226',
                    'E230', 'E234', 'E249', 'E352', 'E353', 'E354', 'E355', 'E359',
                    'E360', 'E362', 'E366', 'E370', 'E371', 'E372', 'E373', 'E376',
                    'E383', 'E384', 'E387', 'E388', 'E389', 'E390', 'E392', 'E399',
                    'E120', 'E122', 'E127', 'E128', 'E129', 'E153', 'E163', 'E164',
                    'E165', 'E166', 'E174', 'E179', 'E187', 'E188', 'E193', 'E302',
                    'E305', 'E307', 'E308', 'E311', 'E315', 'E317', 'E322', 'E325',
                    'E329', 'E330', 'E340', 'E349', 'E183', 'E185']

boringdegrees = ['Diploma']




inf = open('/afs/desy.de/user/l/library/dok/ejl/uninteresting.dois', 'r')
uninterestingDOIS = []
newuninterestingDOIS = []
for line in inf.readlines():
    uninterestingDOIS.append(line.strip())
inf.close()

prerecs = []
for page in range(pages):
    tocurl = 'https://repositum.tuwien.at/handle/20.500.12708/5?sort_by=2&order=DESC&offset=' + str(page*rpp) + '&rpp=' + str(rpp)
    print '==={ %i/%i }==={ %s }===' % (page+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    for tr in tocpage.body.find_all('tr'):
        for a in tr.find_all('a'):
            if a.has_attr('href') and re.search('handle\/20.500', a['href']):
                rec = {'tc' : 'T', 'jnl' : 'BOOK', 'note' : [], 'keyw' : [], 'oa' : False}
                rec['hdl'] = re.sub('.*?(20.500.*)', r'\1', a['href'])
                rec['artlink'] = 'https://repositum.tuwien.at' + a['href']
                for img in tr.find_all('img', attrs = {'title' : 'Open Access'}):
                    rec['oa'] = True
                    if not rec['hdl'] in uninterestingDOIS:
                        prerecs.append(rec)
    time.sleep(4)

i = 0
recs = []
for rec in prerecs:
    keepit = True
    i += 1
    print '---{ %i/%i (%i) }---{ %s }------' % (i, len(prerecs), len(recs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        time.sleep(4)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['artlink'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']), features="lxml")
        except:
            print "no access to %s" % (rec['artlink'])
            continue
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name') and meta.has_attr('content'):
            #author
            if meta['name'] == 'DC.creator':
                rec['autaff'] = [[ meta['content'] ]]
            #supervisor
            if meta['name'] == 'DC.contributor':
                rec['supervisor'] = [[ meta['content'] ]]
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                if meta.has_attr('xml:lang'):
                    if meta['xml:lang'] == 'en':
                        rec['abs'] = meta['content']
                    elif meta['xml:lang'] == 'de':
                        rec['absde'] = meta['content']
                else:
                    rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                if rec['oa']:
                    rec['FFT'] = meta['content']
                else:
                    rec['hidden'] = meta['content']
            #keywords
            elif meta['name'] == 'citation_keywords':
                for keyw in re.split('[,;] ', meta['content']):
                    if not keyw in ['Thesis', 'Hochschulschrift']:
                        rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'Deutsch':
                    rec['language'] = 'german'
            #DOI
            elif meta['name'] == 'citation_doi':
                rec['doi'] = meta['content']
            #pages
            elif meta['name'] == 'DC.format':
                if re.search('\d\d', meta['content']):
                    rec['pages'] = re.sub('\D*(\d\d+).*', r'\1', meta['content'])
            #type
            elif meta['name'] == 'DC.type':
                if meta['content'] in boringdegrees:
                    print '  skip "%s"' % (meta['content'])
                    keepit = False
                elif not meta['content'] in ['Thesis', 'Hochschulschrift']:
                    rec['note'].append(meta['content'])
    for table in artpage.body.find_all('table', attrs = {'class' : 'itemDisplayTable'}):
        #tr not properly set in html
        for td in table.find_all('td'):
            if td.has_attr('class'):
                if 'metadataFieldLabel' in td['class']:
                    metadataFieldLabel = td.text.strip()
                elif 'metadataFieldValue' in td['class']:
                    #ORCID of author
                    if metadataFieldLabel == 'Authors:':
                        for a in td.find_all('a'):
                            if a.has_attr('href') and re.search('orcid.org', a['href']):
                                rec['autaff'][-1].append(re.sub('.*\/', 'ORCID:', a['href']))
                    #ORCID of supervisor
                    elif metadataFieldLabel == 'Advisor:':
                        for a in td.find_all('a'):
                            if a.has_attr('href') and re.search('orcid.org', a['href']):
                                rec['supervisor'][-1].append(re.sub('.*\/', 'ORCID:', a['href']))
                    #institute
                    elif metadataFieldLabel == 'Organisation:':
                        institute = td.text.strip()
                        if institute[:4] in boringinstitutes:
                            print '  skip "%s"' % (institute[:4])
                            keepit = False
                        else:
                            rec['note'].append(institute)
    #author's affiliation
    rec['autaff'][-1].append(publisher)
    #abstract
    if not 'abs' in rec.keys() and 'absde' in rec.keys():
        rec['abs'] = rec['absde']
    if keepit:
        recs.append(rec)
        print '  ', rec.keys()
    else:
        newuninterestingDOIS.append(rec['hdl'])

#closing of files and printing
xmlf = os.path.join(xmldir, jnlfilename+'.xml')
xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'),'utf8')
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

