# -*- coding: utf-8 -*-
#harvest theses from Toronto U.
#FS: 2019-12-12


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

publisher = 'Toronto U.'

rpp = 50
pages = 10 

hdr = {'User-Agent' : 'Magic Browser'}
recs = []
deprecs = {}
for i in range(pages):
    tocurl = 'https://tspace.library.utoronto.ca/handle/1807/9945/browse?rpp=' + str(rpp) + '&sort_by=2&type=dateissued&offset=' + str(i*rpp) + '&etal=-1&order=DESC'
    print '---{ %i/%i }---{ %s }---' % (i+1, pages, tocurl)
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for tr in tocpage.body.find_all('tr'):
        for td in tr.find_all('td', attrs = {'headers' : 't2'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'supervisor' : []}
            for a in td.find_all('a'):
                rec['artlink'] = 'https://tspace.library.utoronto.ca' + a['href'] #+ '?show=full'
                rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                recs.append(rec)
    time.sleep(15)

i = 0
for rec in recs:
    i += 1
    print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
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
    if 'autaff' in rec.keys():
        rec['autaff'][-1].append(publisher)
        #license
        for a in artpage.find_all('a'):
            if a.has_attr('href') and re.search('creativecommons.org', a['href']):
                rec['license'] = {'url' : a['href']}
                if 'pdf_url' in rec.keys():
                    rec['FFT'] = rec['pdf_url']
        #other metadata
        for div in artpage.body.find_all('div', attrs = {'class' : 'item-container'}):
            for tr in div.find_all('tr'):
                for span in tr.find_all('span'):
                    spant = span.text.strip()
                for a in tr.find_all('a'):
                    at = a.text.strip()
                    #supervisor
                    if spant == 'Advisor:':
                        rec['supervisor'].append([at, publisher])
                    #department
                    elif spant == 'Department:':
                        if at in deprecs.keys():
                            deprecs[at].append(rec)
                        else:
                            deprecs[at] = [rec]
        #
        print '  ', rec.keys()
        if i % 10 == 0:
            print ', '.join(['%s (%s)' % (dep, len(deprecs[dep])) for dep in deprecs.keys()])

for dep in deprecs.keys():
    if dep in ['Astronomy and Astrophysics', 'Physics', 'Mathematics']:
        print '+', dep
        jnlfilename = 'THESES-TORONTO-%s_%s' % (stampoftoday, re.sub('\W', '', dep))
        #closing of files and printing
        xmlf = os.path.join(xmldir,jnlfilename+'.xml')
        xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
        ejlmod2.writeXML(deprecs[dep], xmlfile, publisher)
        xmlfile.close()
        #retrival
        retfiles_text = open(retfiles_path,"r").read()
        line = jnlfilename+'.xml'+ "\n"
        if not line in retfiles_text: 
            retfiles = open(retfiles_path,"a")
            retfiles.write(line)
            retfiles.close()
    else:
        print '-', dep
