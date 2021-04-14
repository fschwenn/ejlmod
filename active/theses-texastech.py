# -*- coding: utf-8 -*-
#harvest theses from Texas Tech.
#FS: 2021-04-14

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

publisher = 'Texas Tech.'
jnlfilename = 'THESES-TexasTech-%s' % (stampoftoday)
departments = ['Applied+Physics', 'Mathematical+Physics', 'Mathematics', 'Mathematics+and+Statistics',
               'Physics', 'Science']
rpp = 10

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
j = 0
for department in departments:
    j += 1
    tocurl = 'https://ttu-ir.tdl.org/handle/2346/521/browse?type=department&value=' + department + '&sort_by=2&order=DESC&rpp=' + str(rpp)
    print '==={ %i/%i }==={ %s }===' % (j, len(departments), tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req), features="lxml")
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : []}
        rec['note'] = [ re.sub('\W', ' ', department) ]
        for span in div.find_all('span', title=re.compile('rft.degree=Doctor')):
            for a in div.find_all('a'):
                rec['artlink'] = 'https://ttu-ir.tdl.org' + a['href'] + '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                recs.append(rec)
    print '  %i/%i' % (len(recs), len(divs))
    time.sleep(30)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
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
                if re.search('\d\d\d\d\-\d\d\d\d',  meta['content']):
                    rec['autaff'][-1].append('ORCID:' + meta['content'])
                else:
                    author = re.sub(' \d.*', '', re.sub(' *\[.*', '', meta['content']))
                    rec['autaff'] = [[ author ]]
            #title
            elif meta['name'] == 'DC.title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = re.sub('.*([12]\d\d\d).*', r'\1', meta['content'])
            #keywords
            elif meta['name'] == 'DC.subject':
                rec['keyw'] += re.split(' *; *', meta['content'])
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #FFT
            elif meta['name'] == 'citation_pdf_url':
                rec['pdf_url'] = meta['content']
    rec['autaff'][-1].append(publisher)
    #license
    for a in artpage.find_all('a'):
        if a.has_attr('href') and re.search('creativecommons.org', a['href']):
            rec['license'] = {'url' : a['href']}
            if 'pdf_url' in rec.keys():
                rec['FFT'] = rec['pdf_url']
            else:
                for div in artpage.find_all('div'):
                    for a2 in div.find_all('a'):
                        if a2.has_attr('href') and re.search('bistream.*\.pdf', a['href']):
                            divt = div.text.strip()
                            if re.search('Restricted', divt):
                                print divt
                            else:
                                rec['FFT'] = 'https://uh-ir.tdl.org' + re.sub('\?.*', '', a['href'])
    #upload PDF at least hidden (need login)
    if not 'FFT' in rec.keys() and 'pdf_url' in rec.keys():
        rec['hidden'] = rec['pdf_url']

    for tr in artpage.find_all('tr', attrs = {'class' : 'ds-table-row'}):
        for td in tr.find_all('td', attrs = {'class' : 'label-cell'}):
            tht = td.text.strip()
        for td in tr.find_all('td', attrs = {'class' : 'word-break'}):
            #supervisor
            if tht in ['dc.contributor.advisor', 'dc.contributor.committeeChair']:
                rec['supervisor'].append([td.text.strip()])
    print '  ', rec.keys()
    

#closing of files and printing
xmlf = os.path.join(xmldir,jnlfilename+'.xml')
xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
ejlmod2.writeXML(recs,xmlfile,publisher)
xmlfile.close()
#retrival
retfiles_text = open(retfiles_path,"r").read()
line = jnlfilename+'.xml'+ "\n"
if not line in retfiles_text: 
    retfiles = open(retfiles_path,"a")
    retfiles.write(line)
    retfiles.close()
