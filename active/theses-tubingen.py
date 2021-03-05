# -*- coding: utf-8 -*-
#harvest theses from Tubingen
#FS: 2020-04-27


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

xmldir = '/afs/desy.de/user/l/library/inspire/ejl'# + '/special'
retfiles_path = "/afs/desy.de/user/l/library/proc/retinspire/retfiles"# + '_special'


now = datetime.datetime.now()
stampoftoday = '%4d-%02d-%02d' % (now.year, now.month, now.day)

publisher = 'U. Tubingen'

typecode = 'T'

startyear = str(now.year - 1)
rpp = 50

hdr = {'User-Agent' : 'Magic Browser'}

for fac in ['Physik', 'Sonstige+-+Mathematik+und+Physik', 'Mathematik']:
    tocurl = 'https://publikationen.uni-tuebingen.de/xmlui/handle/10900/42126/discover?rpp=' + str(rpp) + '&filtertype_0=dateIssued&filtertype_1=fachbereich&filter_0=[' + startyear + '+TO+' + str(now.year+1) + ']&filter_relational_operator_1=equals&filter_1=' + fac + '&filter_relational_operator_0=equals&filtertype=type&filter_relational_operator=equals&filter=Dissertation'
    
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    recs = []
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://publikationen.uni-tuebingen.de' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            recs.append(rec)

    i = 0
    for rec in recs:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (fac, i, len(recs), rec['artlink'])
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
                elif meta['name'] == 'DC.contributor':
                    author = re.sub(' *\(.*', '', meta['content'])
                    rec['supervisor'] = [[ author ]]
                    rec['supervisor'][-1].append(publisher)
                #language
                elif meta['name'] == 'DC.language':
                    if meta['content'] == 'de':
                        rec['language'] = 'german'
                elif meta['name'] == 'DC.identifier':
                    #DOI
                    if re.search('doi.org.10', meta['content']):
                        rec['doi'] = re.sub('.*org.(10.*)', r'\1', meta['content'])
                    #HDL
                    elif re.search('handle.net', meta['content']):
                        rec['hdl'] = re.sub('.*handle.net\/', '',  meta['content'])
                    #URN
                    elif re.search('nbn-resolving.de\/urn', meta['content']):
                        rec['urn'] = re.sub('.*nbn-resolving.de\/', '',  meta['content'])
                #title
                elif meta['name'] == 'DC.title':
                    rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'DCTERMS.issued':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    for keyw in re.split(' *; *', meta['content']):
                        for kw2 in re.split(' , ', keyw):
                            if not kw2 in rec['keyw']:
                                rec['keyw'].append(kw2)
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    if meta.has_attr('xml:lang'):
                        if meta['xml:lang'] == 'en':
                            rec['abs'] = meta['content']
                        elif meta['xml:lang'] == 'de_DE':
                            rec['abs_de'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['hidden'] = meta['content']
        #abstract
        if not 'abs' in rec.keys() and 'abs_de' in rec.keys():
            rec['abs'] = rec['abs_de']


    jnlfilename = 'THESES-TUBINGEN-%s_%s' % (stampoftoday, re.sub('\W', '', fac))


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
