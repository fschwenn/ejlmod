# -*- coding: utf-8 -*-
#harvest theses from Montreal
#FS: 2020-01-24


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

publisher = 'U. Montreal (main)'

typecode = 'T'

startyear = str(now.year - 1)

hdr = {'User-Agent' : 'Magic Browser'}

for fac in ['2949', '2990']:
    tocurl = 'https://papyrus.bib.umontreal.ca/xmlui/handle/1866/' + fac + '/discover?filtertype=dateIssued&filter_relational_operator=equals&filter=[' + startyear + '+TO+' + str(now.year) + ']&rpp=200'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    prerecs = []
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://papyrus.bib.umontreal.ca' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            prerecs.append(rec)

    i = 0
    recs = []
    for rec in prerecs:
        i += 1
        print '---{ %s }---{ %i/%i}---{ %s }------' % (fac, i, len(prerecs), rec['artlink'])
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
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
                    rec['autaff'][-1].append(publisher)
                #author
                if meta['name'] == 'DC.contributor':
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['supervisor'] = [[ author ]]
                    rec['supervisor'][-1].append(publisher)
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
                    rec['FFT'] = meta['content']
        #abstract
        for div in artpage.body.find_all('div', attrs = {'class' : 'simple-item-view-description'}):
            for h5 in div.find_all('h5'):
                if re.search('R.s.', h5.text) or re.search('Abstra', h5.text):
                    h5.replace_with('')
                    for div2 in  div.find_all('div', attrs = {'class' : 'spacer'}):
                        div2.replace_with('XXXSPACERXXX')
                    abstract = re.split('XXXSPACERXXX', div.text.strip())
                    #print len(abstract)                    
                    rec['abs'] = ''.join(abstract[len(abstract)/2:])
        #degree
        for div in artpage.body.find_all('div', attrs = {'class' : 'simple-item-view-degreelevel'}):
            for h5 in div.find_all('h5'):
                h5.replace_with('')
                if div.text.strip() == "Doctoral":
                    recs.append(rec)
                else:
                    print 'skip', div.text.strip()


    jnlfilename = 'THESES-MONTREAL-%s_%s' % (stampoftoday, fac)


    #closing of files and printing
    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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
