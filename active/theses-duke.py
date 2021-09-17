# -*- coding: utf-8 -*-
#harvest theses from Duke U.
#FS: 2019-12-13


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

publisher = 'Duke U. (main)'

rpp = 20

hdr = {'User-Agent' : 'Magic Browser'}
for department in ['Physics', 'Mathematics']:
    tocurl = 'https://dukespace.lib.duke.edu/dspace/handle/10161/4/browse?type=department&value=' + department + '&rpp=' + str(rpp) + '&sort_by=2&order=DESC'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    recs = []
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : []}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://dukespace.lib.duke.edu' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            if department == 'Mathematics':
                rec['fc'] = 'm'
            recs.append(rec)
    time.sleep(30)

    i = 0
    for rec in recs:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (department, i, len(recs), rec['artlink'])
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
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'DC.creator':
                    if re.search('\d\d\d\d\-\d\d\d\d',  meta['content']):
                        rec['autaff'][-1].append('ORCID:' + meta['content'])
                    else:
                        author = re.sub(' *\[.*', '', meta['content'])
                        rec['autaff'] = [[ author ]]
                #supervisor
                if meta['name'] == 'DC.contributor':
                    rec['supervisor'].append([meta['content'], publisher])
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
        rec['autaff'][-1].append(publisher)
        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                if 'pdf_url' in rec.keys():
                    rec['FFT'] = rec['pdf_url']
        #PDF as hidden
        if not 'license' in rec.keys() and 'pdf_url' in rec.keys():
            rec['hidden'] = rec['pdf_url']
        print '  ', rec.keys()
    jnlfilename = 'THESES-DUKE_U-%s_%s' % (stampoftoday, re.sub('\W', '', department))


    #closing of files and printing
    xmlf = os.path.join(xmldir,jnlfilename+'.xml')
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
