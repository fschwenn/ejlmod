# -*- coding: utf-8 -*-
#harvest Uni Bonn Theses
#FS: 2020-05-11


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl' + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles" + '_special'

now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Bonn (main)'
hdr = {'User-Agent' : 'Magic Browser'}

years = 2 + 8
rpp = 200


for ddc in ['500', '510', '530']:
    jnlfilename = 'THESES-BONN-%s-%s' % (stampoftoday, ddc)
    recs = []
    for i in range(years):
        year = now.year - i
        tocurl = 'https://bonndoc.ulb.uni-bonn.de/xmlui/handle/20.500.11811/1627/discover?filtertype_0=ddc&filter_relational_operator_0=equals&filter_0=ddc%3A' + ddc + '&filtertype=dateIssued&filter_relational_operator=equals&filter=[' + str(year) + '+TO+' + str(year) + ']&rpp=' + str(rpp)
        print '==={ %i }==={ %s }==={ %s }===' % (year, ddc, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'year' : str(year), 'date' : str(year)}
            for a in div.find_all('a'):
                for h4 in a.find_all('h4'):
                    rec['artlink'] = 'https://bonndoc.ulb.uni-bonn.de' + a['href']# + '?show=full'
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    recs.append(rec)

    i = 0
    for rec in recs:
        i += 1
        print '---{ %i/%i }---{ %s }------' % (i, len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            time.sleep(10)
        except:
            try:
                print 'retry %s in 180 seconds' % (rec['artlink'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            except:
                print 'no access to %s' % (rec['artlink'])
                continue
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'DC.creator':
                    rec['autaff'] = [[ meta['content'] ]]
                #supervisor
                elif meta['name'] == 'DC.contributor':
                    rec['supervisor'] = [[ meta['content'] ]]
                #title
                elif meta['name'] == 'DC.title':
                    rec['tit'] = meta['content'] 
                #keywords
                elif meta['name'] == 'DC.Subject':
                    if not meta.has_attr('scheme'):
                        rec['keyw'] = re.split('[;,] ', meta['content'])
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    rec['abs'] = meta['content']
                #language
                elif meta['name'] == 'DC.Language':
                    if meta['content'] != 'eng':
                        if meta['content'] == 'ger':
                            rec['language'] = 'german'
                        else:
                            rec['language'] = meta['content']
                #URN
                elif meta['name'] == 'DC.Identifier':
                    if re.search('^urn', meta['content']):
                        rec['urn'] = meta['content']
                #URN
                elif meta['name'] == 'citation_pdf_url':
                    rec['fulltext'] = meta['content']
                #license
                elif meta['name'] == 'DC.Rights':
                    if re.search('creativecommons.org', meta['content']):
                        rec['license'] = {'url' : meta['content']}
        if 'fulltext' in rec.keys():
            if 'license' in rec.keys():
                rec['FFT'] = rec['fulltext']
            else:
                rec['hidden'] = rec['fulltext']
        rec['autaff'][-1].append(publisher)
        print '  ', rec.keys()
                    
    #closing of files and printing
    xmlf    = os.path.join(xmldir,jnlfilename+'.xml')
    xmlfile  = codecs.EncodedFile(codecs.open(xmlf,mode='wb'),'utf8')
    ejlmod2.writeXML(recs,xmlfile,publisher)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path,'r').read()
    line = jnlfilename+'.xml'+ '\n'
    if not line in retfiles_text: 
        retfiles = open(retfiles_path,'a')
        retfiles.write(line)
        retfiles.close()


