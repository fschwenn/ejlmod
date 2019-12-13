# -*- coding: utf-8 -*-
#harvest theses from Cornell
#FS: 2019-12-09


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

publisher = 'Cornell U.'

typecode = 'T'


rpp = 20
yearstocover = 1

hdr = {'User-Agent' : 'Magic Browser'}
allhdls = []
for filter in ['Physics', 'Quantum+physics', 'Theoretical+physics', 'physics', 'Cosmology', 'Mathematics', 'Applied+mathematics', 'Astronomy', 'Astrophysics', 'Particle+physics']:
    tocurl = 'https://ecommons.cornell.edu/handle/1813/47/discover?field=subject&filtertype=subject&filter_relational_operator=equals&filter=' + filter + '&sort_by=dc.date.issued_dt&order=desc&rpp=' + str(rpp)
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    recs = []
    divs = tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'})
    for div in divs:
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for span in div.find_all('span', attrs = {'class' : 'date'}):
            rec['date'] = span.text.strip()
            if int(rec['date'][:4]) >= now.year - yearstocover:
                for span in div.find_all('span', title=re.compile('rft.degree=Doctor')):
                    for a in div.find_all('a'):
                        rec['artlink'] = 'https://ecommons.cornell.edu' + a['href'] #+ '?show=full'
                        rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                        if rec['hdl'] in allhdls:
                            print 'skip double appearance of', rec['hdl']
                        else:
                            recs.append(rec)
                            allhdls.append(rec['hdl'])
    print '  %i/%i' % (len(recs), len(divs))
    time.sleep(30)

    i = 0
    for rec in recs:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }------' % (filter, i, len(recs), rec['artlink'])
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
                #DOI
                elif meta['name'] == 'DC.identifier' and re.search('doi.org', meta['content']):
                    rec['doi'] = re.sub('.*doi.org\/', '', meta['content'])
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
                                    rec['FFT'] = 'https://ecommons.cornell.edu' + re.sub('\?.*', '', a['href'])
                                    
    jnlfilename = 'THESES-CORNELL-%s_%s' % (stampoftoday, re.sub('\W', '', filter))


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
