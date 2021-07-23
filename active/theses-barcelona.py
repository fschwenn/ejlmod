# -*- coding: utf-8 -*-
#harvest theses from Barcelona U.
#FS: 2020-11-19

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

publisher = 'U. Barcelona (main)'

rpp = 10
startyear = now.year-1
departments = [('PHYS', 'Barcelona U.', ['35246', '41813', '103124', '106688', '41840', '41381']),
	       ('MATH', 'U. Barcelona (main)', ['42083', '43181', '35131'])]
hdr = {'User-Agent' : 'Magic Browser'}

hdls = []
for (subj, aff, deps) in departments:
    recs = []
    jnlfilename = 'THESES-BARCELONA-%s-%s' % (stampoftoday, subj)
    for dep in deps:
        tocurl = 'http://diposit.ub.edu/dspace/handle/2445/' + dep + '/browse?type=title&sort_by=2&order=DESC&rpp=' + str(rpp) + '&etal=0&submit_browse=Update'
        print '==={ %s (%s) }==={ %s }===' % (subj, dep, tocurl)
        req = urllib2.Request(tocurl, headers=hdr)
        tocpage = BeautifulSoup(urllib2.urlopen(req))
        time.sleep(3)
        for tr in tocpage.body.find_all('tr'):
            keepit = True
            rec = {'tc' : 'T', 'keyw' : [], 'jnl' : 'BOOK', 'affiliation' : aff,
                   'supervisor' : []}
            for td in tr.find_all('td', attrs = {'headers' : 't1'}):
                if re.search('^\d\d\d\d$', td.text):
                    rec['date'] = td.text.strip()
                    if int(rec['date']) < startyear:
                        keepit = False
            for td in tr.find_all('td', attrs = {'headers' : 't2'}):
                for a in td.find_all('a'):                
                    rec['artlink'] = 'http://diposit.ub.edu' + a['href'] 
                    rec['hdl'] = re.sub('.*handle\/', '', a['href'])
                    if keepit:
                        if not rec['hdl'] in hdls:
                            recs.append(rec)
                            hdls.append(rec['hdl'])
        print '   %i records so far' % (len(recs))

    i = 0
    for rec in recs:
        i += 1
        print '---{ %s }---{ %i/%i }---{ %s }---' % (subj, i, len(recs), rec['artlink'])
        try:
            artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            time.sleep(5)
        except:
            try:
                print "retry %s in 180 seconds" % (rec['artlink'])
                time.sleep(180)
                artpage = BeautifulSoup(urllib2.build_opener(urllib2.HTTPCookieProcessor).open(rec['artlink']))
            except:
                print "no access to %s" % (rec['link'])
                continue      
        for meta in artpage.head.find_all('meta'):
            if meta.has_attr('name'):
                #author
                if meta['name'] == 'DC.creator':
                    rec['autaff'] = [[ meta['content'], rec['affiliation'] ]]
                #supervisor
                elif meta['name'] == 'DC.contributor':
                    if not 'autaff' in rec.keys():
                        rec['supervisor'].append([meta['content']])
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
                    rec['hidden'] = meta['content']
                #pages
                elif meta['name'] == 'DCTERMS.extent':
                    if re.search('\d\d', meta['content']):
                        rec['pages'] = re.sub('.*?(\d\d+).*', r'\1', meta['content'])
                #abstract
                elif meta['name'] == 'DCTERMS.abstract':
                    if re.search('\[eng\]', meta['content']):
                        rec['abs'] = re.sub('\[eng\] *', '', meta['content'])
                    else:
                        rec['absspa'] = re.sub('^\[.*\] ', '', meta['content'])
                if not 'abs' in rec.keys() and 'absspa' in rec.keys():
                    rec['abs'] = rec['absspa']
        print '  ', rec.keys()

    #closing of files and printing
    xmlf = os.path.join(xmldir, jnlfilename+'.xml')
    xmlfile = codecs.EncodedFile(codecs.open(xmlf, mode='wb'), 'utf8')
    ejlmod2.writenewXML(recs, xmlfile, publisher, jnlfilename)
    xmlfile.close()
    #retrival
    retfiles_text = open(retfiles_path, "r").read()
    line = jnlfilename+'.xml'+ "\n"
    if not line in retfiles_text: 
        retfiles = open(retfiles_path, "a")
        retfiles.write(line)
        retfiles.close()
        
