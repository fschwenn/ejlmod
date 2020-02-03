# -*- coding: utf-8 -*-
#harvest theses from Charles U. Prague
#FS: 2019-11-25


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

publisher = 'Charles U., Prague (main)'

typecode = 'T'

jnlfilename = 'THESES-CTU-%s' % (stampoftoday)
if now.month < 8:
    years = [str(now.year - 1), str(now.year)]
else:
    years = [str(now.year)]

hdr = {'User-Agent' : 'Magic Browser'}
for year in years:
    if year != year[0]:
        time.sleep(300)
    tocurl = 'https://dspace.cuni.cz/discover?filtertype_1=ds_uk_faculty&filter_relational_operator_1=equals&filter_1=Matematicko-fyzik%C3%A1ln%C3%AD+fakulta&filtertype_2=ds_thesesDefenceYear&filter_relational_operator_2=equals&filter_2=' + year + '&filtertype_3=ds_uk_language_iso&filter_relational_operator_3=equals&filter_3=en_US&submit_apply_filter=&rpp=500&locale-attribute=en'
    print tocurl
    req = urllib2.Request(tocurl, headers=hdr)
    tocpage = BeautifulSoup(urllib2.urlopen(req))
    recs = []
    i = 0
    for div in tocpage.body.find_all('div', attrs = {'class' : 'artifact-description'}):
        i += 1
        rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK'}
        for a in div.find_all('a'):
            rec['artlink'] = 'https://dspace.cuni.cz' + a['href'] #+ '?show=full'
            rec['hdl'] = re.sub('.*handle\/', '', a['href'])
            for h5 in div.find_all('h5', attrs = {'class' : 'work-type'}):
                if re.search('dissertation thesis', h5.text):
                    recs.append(rec)
                else:
                    print '[%i] skip %s' % (i, h5.text.strip())

    i = 0
    for rec in recs:
        i += 1
        print '---{ %s }---{ %i/%i}---{ %s }------' % (year, i, len(recs), rec['artlink'])
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
                #title
                elif meta['name'] == 'DC.title':
                    if meta['xml:lang'] == "en_US":
                        rec['tit'] = meta['content']
                #date
                elif meta['name'] == 'DCTERMS.issued':
                    rec['date'] = meta['content']
                #keywords
                elif meta['name'] == 'DC.subject':
                    if meta['xml:lang'] == "en_US":
                        for keyw in re.split(' *; *', meta['content']):
                            rec['keyw'].append(keyw)
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    if meta['xml:lang'] == "en_US":
                        rec['abs'] = meta['content']
                #FFT
                elif meta['name'] == 'citation_pdf_url':
                    rec['hidden'] = meta['content']
        for span in artpage.body.find_all('span', attrs = {'class' : 'text-theses-failed'}):
            rec['tit'] += ' [FAILED]'
        print rec.keys()
    jnlfilename = 'THESES-CTU-%s_%s' % (stampoftoday, year)


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
