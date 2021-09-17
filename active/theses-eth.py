# -*- coding: utf-8 -*-
#harvest theses from ETH
#FS: 2019-09-13


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

publisher = 'Zurich, ETH'

typecode = 'T'

jnlfilename = 'THESES-ETH-%s' % (stampoftoday)

hdr = {'User-Agent' : 'Magic Browser'}
prerecs = []
for dep in ['02000', '02010', '02150']:
    tocurl = 'https://www.research-collection.ethz.ch/handle/20.500.11850/16/discover?filtertype_1=datePublished&filter_relational_operator_1=equals&filter_1=[' + str(now.year - 1) + '+TO+' + str(now.year + 1) + ']&filtertype_2=split_leitzahl&filter_relational_operator_2=contains&filter_2=' + dep + '&submit_apply_filter=&rpp=100'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    time.sleep(3)
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        if dep == '02000':
            rec['note'] = ['Dep. Mathematik']
            rec['fc'] = 'm'
        elif dep == '02010':
            rec['note'] = ['Dep. Physik']
        elif dep == '02150':
            rec['note'] = ['Dep. Informatik']
            rec['fc'] = 'c'
        for a in div.find_all('a'):
            rec['artlink'] = 'https://www.research-collection.ethz.ch' + a['href'] + '?show=full'
            rec['hdl'] = re.sub('.*handle\/(.*\d).*', r'\1', a['href'])
            prerecs.append(rec)


recs = []
i = 0
for rec in prerecs:
    i += 1
    print '---{ %i/%i}---{ %s}------' % (i, len(prerecs), rec['artlink'])
    try:
        artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        time.sleep(3)
    except:
        try:
            print "retry %s in 180 seconds" % (rec['link'])
            time.sleep(180)
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
        except:
            print "no access to %s" % (rec['link'])
            continue      
    for meta in artpage.head.find_all('meta'):
        if meta.has_attr('name'):
            #author
            if meta['name'] == 'DC.creator':
                author = re.sub(' *\[.*', '', meta['content'])
                rec['autaff'] = [[ author ]]
                rec['autaff'][-1].append('Zurich, ETH')
            #DOI
            elif meta['name'] == 'DC.identifier':
                if re.search('^10.3929', meta['content']):
                    rec['doi'] = meta['content']
            #title
            elif meta['name'] == 'citation_title':
                rec['tit'] = meta['content']
            #date
            elif meta['name'] == 'DCTERMS.issued':
                rec['date'] = meta['content']
            #keywords
            elif meta['name'] == 'DC.subject':
                for keyw in re.split(' *; *', meta['content']):
                    rec['keyw'].append(keyw)
            #language
            elif meta['name'] == 'DC.language':
                if meta['content'] == 'por':
                    rec['language'] = 'portuguese'
            #FFT
            #elif meta['name'] == 'citation_pdf_url':
            #    rec['hidden'] = meta['content']
            #abstract
            elif meta['name'] == 'DCTERMS.abstract':
                rec['abs'] = meta['content']
            #license            
            elif meta['name'] == 'DC.rights':
                if re.search('creativecommons.org', meta['content']):
                    rec['licence'] = {'url' : re.sub('.*http', 'http', meta['content'])}
    if 'licence' in rec.keys():
        for div in artpage.body.find_all('div', attrs = {'class' : 'file-link'}):
            for a in div.find_all('a'):
                if re.search('Fulltext', a.text):
                    #ETH is just too restrictive against robots (even 5 minutes delays do not work)
                    #rec['FFT'] = 'https://www.research-collection.ethz.ch' + a['href']
                    rec['link'] = 'https://www.research-collection.ethz.ch' + a['href']
    recs.append(rec)



	


#closing of files and printing
xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
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
