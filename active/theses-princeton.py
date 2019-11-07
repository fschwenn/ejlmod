# -*- coding: utf-8 -*-
#harvest theses from University of Princeton
#FS: 2019-09-25


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

publisher = 'Princeton U.'

typecode = 'T'


sections = [('dsp01t722h882n', 'Physics'),
            ('dsp015m60qr913', 'Astrophysics'),
            ('dsp01pg15bd903', 'Plasma'),
            ('dsp01v692t6222', 'Mathematics')]

hdr = {'User-Agent' : 'Magic Browser'}
for section in sections:
    jnlfilename = 'THESES-PRINCETON-%s-%s' % (stampoftoday, section[1])
    recs = []
    #for page in ['', '?offset=20']:
    for page in ['']:
        tocurl = 'https://dataspace.princeton.edu/jspui/handle/88435/' + section[0] + page
        print tocurl
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(3)
        for tr in tocpage.body.find_all('tr'):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
            for a in tr.find_all('a'):
                if re.search('handle\/88435', a['href']):
                    rec['artlink'] = 'https://dataspace.princeton.edu' + a['href'] #+ '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)
    i = 0
    for rec in recs:
        rec['link'] = rec['artlink']
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (section[1], i, len(recs), rec['artlink'])
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
                if meta['name'] == 'DC.contributor.author':
                    author = re.sub(' *\[.*', '', meta['content'])
                    rec['autaff'] = [[ author ]]
                    rec['autaff'][-1].append('Princeton U.')
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
                    rec['FFT'] = meta['content']
    


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
